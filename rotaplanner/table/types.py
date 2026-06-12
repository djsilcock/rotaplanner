from pydantic import BaseModel, Field
import datetime


class Location(BaseModel):
    id: str | None
    name: str


class Staff(BaseModel):
    id: str | None
    name: str


class StaffAssignment(BaseModel):
    id: int | None = None
    staff: Staff
    availability_type: str = "available"
    attendance: int = 100
    flags: list[str] = Field(default_factory=list)


class Timeslot(BaseModel):
    id: int


class Role(BaseModel):
    id: int
    name: str
    assignments: list[StaffAssignment] = Field(default_factory=list)
    requirements: list[str] = Field(default_factory=list)


class Activity(BaseModel):
    id: str
    name: str
    location: str | None
    status: str = ""
    activity_start: datetime.datetime
    activity_finish: datetime.datetime
    roles: list[Role] = Field(default_factory=list)
