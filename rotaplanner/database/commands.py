import sqlite3
import pathlib


from . import get_database_connection
import click


@click.group()
def db():
    pass


@db.command("setup")
def setup_database():
    with get_database_connection(force=True) as connection:
        sqlite_setup_file = pathlib.Path(__file__, "..", "setup.sql").resolve()
        with open(sqlite_setup_file) as f:
            sql_setup = f.read()
            connection.executescript(sql_setup)


@db.command("populate")
def populate_database():
    from test_data import (
        staff_list,
        location_list,
        activity_tags,
        activities,
    )

    with get_database_connection() as connection:
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
            start, finish = activity[2]
            connection.execute(
                "INSERT INTO activities (id, name, start, finish) VALUES (?, ?, ?, ?) ON CONFLICT(id) DO NOTHING",
                (activity_id, activity_name, start, finish),
            )
        connection.execute(
            "INSERT INTO activity_roles (activity_id, name) SELECT id, ? FROM activities",
            ("default",),
        )
