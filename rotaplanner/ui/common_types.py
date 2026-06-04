from pydantic import BaseModel, Field
import datetime


class Location(BaseModel, extra="forbid"):
    id: str | None
    name: str


class Staff(BaseModel, extra="forbid"):
    id: str | None
    name: str


class StaffAssignment(BaseModel, extra="forbid"):
    id: int | None = None
    staff: Staff
    availability_type: str = "available"
    attendance: int = 100
    flags: list[str] = Field(default_factory=list)


class Timeslot(BaseModel, extra="forbid"):
    id: int


class Skill(BaseModel, extra="forbid"):
    id: str | None
    name: str


class RequirementGroup(BaseModel, extra="forbid"):
    id: int
    group_type: str
    parent_group_id: int | None
    activity_id: str | None
    requirements: list["Requirement"] = Field(default_factory=list)


class Requirement(BaseModel, extra="forbid"):
    id: int
    quantity: int
    minimum_required: int
    maximum_allowed: int
    attendance: int = 100
    skills: list[Skill] = Field(default_factory=list)


class Role(BaseModel, extra="forbid"):
    id: int
    name: str
    assignments: list[StaffAssignment] = Field(default_factory=list)
    requirements: list[str] = Field(default_factory=list)


class Activity(BaseModel, extra="forbid"):
    id: str
    name: str
    location: str | None
    activity_start: datetime.datetime
    activity_finish: datetime.datetime
    roles: list[Role] = Field(default_factory=list)
    requirements: list[str] = Field(
        default_factory=list
    )  # expressed as python expressions
