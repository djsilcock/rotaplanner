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


class DateRange(BaseModel):
    start: datetime.date
    finish: datetime.date


class LabelledUUID(BaseModel):
    id: uuid.UUID
    name: str


class RotaConfig(BaseModel):
    date_range: DateRange
    y_axis: list[LabelledUUID]


@router.get(
    "/api/config/rota-grid/{location_or_staff}",
    description="Row and column headings for the rota grid",
    operation_id="tableConfig",
)
def rota_grid(
    location_or_staff: Literal["location", "staff"], connection: Connection
) -> RotaConfig:
    with connection:
        config = {}
        if location_or_staff == "staff":
            y_axis = [
                LabelledUUID(id=staff[0], name=staff[1])
                for staff in connection.execute(
                    "SELECT id,name FROM staff ORDER BY name"
                ).fetchall()
            ]

        elif location_or_staff == "location":
            y_axis = [
                LabelledUUID(id=location[0], name=location[1])
                for location in connection.execute(
                    "SELECT id,name FROM location ORDER BY name"
                ).fetchall()
            ]
        else:
            print(location_or_staff)
            raise HTTPException(404)
        return RotaConfig(
            y_axis=y_axis,
            date_range=DateRange(
                start=datetime.date(2024, 1, 1), finish=datetime.date(2024, 12, 31)
            ),
        )


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
