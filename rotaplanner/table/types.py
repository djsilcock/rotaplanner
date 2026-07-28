from pydantic import BaseModel, Field
import datetime


class Location(BaseModel):
    id: str | None
    name: str


class Staff(BaseModel):
    id: str | None
    name: str


class Role(BaseModel):
    id: int
    name: str


class StaffAssignment(BaseModel):
    id: int | None = None
    staff: Staff
    availability_type: str = "available"
    attendance: int = 100
    flags: list[str] = Field(default_factory=list)
    role: Role | None = None


class Activity(BaseModel):
    id: str
    name: str
    location: str | None
    status: str = ""
    render_type: str = ""
    cell: tuple[str, str] = ()
    activity_start: datetime.datetime
    activity_finish: datetime.datetime
    assignments: list[StaffAssignment] = Field(default_factory=list)
    roles: list[Role] = Field(default_factory=list)
