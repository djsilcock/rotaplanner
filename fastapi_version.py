from fastapi import FastAPI, APIRouter
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
import json
import httpx
import asyncio


from rotaplanner.activities.edit_activities import router as activities_router
from rotaplanner.config.endpoints import router as config_router

from rotaplanner.graphql import graphql_app

from rotaplanner.database import connection_dependency, sql_setup
from test_data import (
    staff_list,
    location_list,
    activity_tags,
    activities,
)


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


app = FastAPI()

api_app = APIRouter()


app.mount("/static", StaticFiles(directory="rotaplanner/static"), name="static")
app.include_router(api_app, prefix="/api")
app.include_router(graphql_app, prefix="/graphql")
