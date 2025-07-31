from rotaplanner.database import Connection

from rotaplanner.models import (
    Activity,
    Staff,
    StaffAssignment,
    Location,
)

from fastapi import APIRouter, HTTPException
from typing import Literal
from pydantic import BaseModel
import datetime
import uuid


router = APIRouter()


@router.get("/api/config/test-data", operation_id="testData")
def make_test_data(connection: Connection):
    with connection:
        staff = [(uuid.uuid4(), f"Staff {i}") for i in range(1, 6)]
        connection.executemany(
            """INSERT INTO staff (id, name) VALUES (?, ?)
            ON CONFLICT DO NOTHING""",
            staff,
        )
        locations = [(uuid.uuid4(), f"Location {i}") for i in range(1, 6)]
        connection.executemany(
            """INSERT INTO location (id, name) VALUES (?, ?)
            ON CONFLICT DO NOTHING""",
            locations,
        )
