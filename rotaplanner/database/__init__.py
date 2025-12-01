import sqlite3
import pathlib
import uuid
import datetime
import pickle
from typing import Annotated
from fastapi import Depends
from contextlib import contextmanager

sqlite_file_name = pathlib.Path(__file__, "..", "database.db").resolve()


sqlite_url = f"sqlite:///{sqlite_file_name}"
print(sqlite_url)
connect_args = {"check_same_thread": False}


def adapt_uuid(value: uuid.UUID):
    return value.hex


def adapt_timestamp(value: datetime.datetime):
    return value.isoformat(sep=" ")


def convert_timestamp(value: bytes):
    if value == "NULL":
        return None
    return datetime.datetime.fromisoformat(value.decode())


sqlite3.register_adapter(datetime.datetime, adapt_timestamp)
sqlite3.register_converter("timestamp", convert_timestamp)


def connection_dependency():
    # check if the database file exists, if not create it and run setup
    if not sqlite_file_name.exists():
        print("Database file does not exist, creating and running setup")
        connection = sqlite3.connect(
            sqlite_file_name,
            check_same_thread=False,
            detect_types=sqlite3.PARSE_COLNAMES | sqlite3.PARSE_DECLTYPES,
        )
        setup_database(connection)
        connection.commit()
        connection.close()
    connection = sqlite3.connect(
        sqlite_file_name,
        check_same_thread=False,
        detect_types=sqlite3.PARSE_COLNAMES | sqlite3.PARSE_DECLTYPES,
    )
    connection.row_factory = sqlite3.Row
    connection.set_trace_callback(print)
    try:
        yield connection
    finally:
        connection.close()


get_database_connection = contextmanager(connection_dependency)

Connection = Annotated[sqlite3.Connection, Depends(connection_dependency)]


def setup_database(connection: sqlite3.Connection):
    from test_data import (
        staff_list,
        location_list,
        activity_tags,
        activities,
    )

    sqlite_setup_file = pathlib.Path(__file__, "..", "setup.sql").resolve()

    with open(sqlite_setup_file) as f:
        sql_setup = f.read()

    connection.executescript(sql_setup)
    connection.executemany(
        "INSERT INTO staff (id, name) VALUES (?, ?) ON CONFLICT(id) DO NOTHING",
        staff_list,
    )
    connection.executemany(
        "INSERT INTO locations (id, name) VALUES (?, ?) ON CONFLICT(id) DO NOTHING",
        location_list,
    )
    connection.executemany(
        "INSERT INTO activity_tags (id, name) VALUES (?, ?) ON CONFLICT(id) DO NOTHING",
        activity_tags,
    )
    for activity in activities:
        activity_id = activity[0]
        activity_name = activity[1]
        activity_times = activity[2]
        connection.execute(
            "INSERT INTO activities (id, name) VALUES (?, ?) ON CONFLICT(id) DO NOTHING",
            (activity_id, activity_name),
        )
        connection.executemany(
            "INSERT INTO timeslots (activity_id, start, finish) VALUES (?, ?, ?) ON CONFLICT(activity_id, start) DO NOTHING",
            [(activity_id, start, finish) for start, finish in activity_times],
        )
    connection.commit()
