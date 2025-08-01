import sqlite3
import pathlib
import uuid
import datetime
import pickle
from typing import Annotated
from fastapi import Depends
from contextlib import contextmanager

sqlite_file_name = pathlib.Path(__file__, "..", "database.db").resolve()
sqlite_setup_file = pathlib.Path(__file__, "..", "setup.sql").resolve()

with open(sqlite_setup_file) as f:
    sql_setup = f.read()

sqlite_url = f"sqlite:///{sqlite_file_name}"
print(sqlite_url)
connect_args = {"check_same_thread": False}


def adapt_uuid(value: uuid.UUID):
    return value.hex


def adapt_timestamp(value: datetime.datetime):
    return value.isoformat()


def convert_timestamp(value: bytes):
    if value == "NULL":
        return None
    return datetime.datetime.fromisoformat(value.decode())


sqlite3.register_adapter(datetime.datetime, adapt_timestamp)
sqlite3.register_converter("timestamp", convert_timestamp)


def connection_dependency():
    connection = sqlite3.connect(
        sqlite_file_name,
        check_same_thread=False,
        detect_types=sqlite3.PARSE_COLNAMES | sqlite3.PARSE_DECLTYPES,
    )
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.close()


get_database_connection = contextmanager(connection_dependency)

Connection = Annotated[sqlite3.Connection, Depends(connection_dependency)]
