from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, Response, APIRouter
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
import json
import httpx
import asyncio


from rotarunner_ui import router as ui_router
from rotaplanner.activities.edit_activities import router as activities_router
from rotaplanner.config.endpoints import router as config_router
from rotarunner_ui.run_development_server import (
    run_vite_dev_server2,
    generate_types,
    build_frontend,
)

from rotaplanner.database import connection_dependency, sql_setup
from test_data import (
    staff_list,
    location_list,
    activity_tags,
    activities,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    with open("./rotarunner_ui/openapi.json", "w") as f:
        json.dump(app.openapi(), f, indent=2)
    print("OpenAPI schema written to rotarunner_ui/openapi.json")
    generate_types()
    on_startup()
    yield


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


app = FastAPI(lifespan=lifespan)

api_app = APIRouter()

api_app.include_router(ui_router)
api_app.include_router(activities_router)
api_app.include_router(config_router)
app.mount("/static", StaticFiles(directory="rotaplanner/static"), name="static")
app.include_router(api_app, prefix="/api")
