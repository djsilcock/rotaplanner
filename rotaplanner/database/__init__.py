import sqlite3
import pathlib
import uuid
import datetime
import pickle
from logging import getLogger


from contextlib import contextmanager

sqlite_file_name = pathlib.Path(__file__, "..", "database.db").resolve()


sqlite_url = f"sqlite:///{sqlite_file_name}"
logger = getLogger(__name__)
logger.info("SQLite URL: %s", sqlite_url)
connect_args = {"check_same_thread": False}


def adapt_uuid(value: uuid.UUID):
    return str(value)


def adapt_timestamp(value: datetime.datetime):
    return value.isoformat(sep=" ")


def convert_timestamp(value: bytes):
    if value == "NULL":
        return None
    return datetime.datetime.fromisoformat(value.decode())


sqlite3.register_adapter(datetime.datetime, adapt_timestamp)
sqlite3.register_adapter(uuid.UUID, adapt_uuid)
sqlite3.register_converter("timestamp", convert_timestamp)


def get_database_connection(force=False):
    # check if the database file exists, if not create it and run setup
    if not sqlite_file_name.exists() and not force:
        raise RuntimeError("Database file does not exist, please run setup")

    connection = sqlite3.connect(
        sqlite_file_name,
        check_same_thread=False,
        detect_types=sqlite3.PARSE_COLNAMES | sqlite3.PARSE_DECLTYPES,
    )
    connection.row_factory = sqlite3.Row
    connection.set_trace_callback(logger.info)
    return connection


@contextmanager
def database_connection(force=False):
    connection = get_database_connection(force=force)
    yield connection
    connection.close()
