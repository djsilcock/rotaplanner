from fastapi import FastAPI, APIRouter
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
import json
import httpx
import asyncio


app = FastAPI()

api_app = APIRouter()


app.mount(
    "/generated", StaticFiles(directory="new_rotaplanner/generated"), name="generated"
)
app.include_router(api_app, prefix="/api")
