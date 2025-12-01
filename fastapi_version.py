from fastapi import FastAPI, APIRouter
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
import json
import httpx
import asyncio


from rotaplanner.activities.edit_activities import router as activities_router
from rotaplanner.config.endpoints import router as config_router

from rotaplanner.graphql import graphql_app


app = FastAPI()

api_app = APIRouter()


app.mount("/static", StaticFiles(directory="rotaplanner/static"), name="static")
app.include_router(api_app, prefix="/api")
app.include_router(graphql_app, prefix="/graphql")
