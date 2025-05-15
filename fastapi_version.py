from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles


from rotaplanner.activities.grid_view import router as activities_router
from rotaplanner.config.endpoints import router as config_router

from rotaplanner.database import connection_dependency, sql_setup
from test_data import (
    staff_list,
    location_list,
    activity_tags,
    activities,
)

app = FastAPI()

app.include_router(activities_router)
app.include_router(config_router)
app.mount("/static", StaticFiles(directory="rotaplanner/static"), name="static")


def on_startup():
    for connection in connection_dependency():
        # instead of converting to a context manager, we can just use the connection directly
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=NORMAL")
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
        connection.executemany(
            "INSERT INTO activities (id, name, activity_start, activity_finish) VALUES (?, ?, ?, ?) ON CONFLICT(id) DO NOTHING",
            activities,
        )
        connection.commit()
