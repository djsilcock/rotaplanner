import sqlite3
import pathlib

from . import database_connection


def setup_database():
    with database_connection(force=True) as connection:
        sqlite_setup_file = pathlib.Path(__file__, "..", "setup.sql").resolve()
        with open(sqlite_setup_file) as f:
            sql_setup = f.read()
            connection.executescript(sql_setup)


def populate_database():
    from test_data import (
        staff_list,
        location_list,
        activity_tags,
        activities,
    )

    with database_connection() as connection:
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
                "INSERT INTO timeslots (start, finish) VALUES (?, ?) ON CONFLICT(start,finish) DO NOTHING",
                activity_times,
            )
            connection.executemany(
                "INSERT INTO timeslots_in_activities (timeslot_id, activity_id) SELECT id, ? FROM timeslots WHERE start = ? AND finish = ?",
                [(activity_id, start, finish) for start, finish in activity_times],
            )
