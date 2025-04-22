"Api requests and responses"

import datetime
import itertools
import uuid
import enum

from ..models import Activity, Staff, StaffAssignment, Location
from pydantic import BaseModel, Field, RootModel, TypeAdapter, model_validator
from dataclasses import dataclass
from sqlalchemy import func, or_, select, delete
from typing import Literal, Annotated, Union, Self

from sqlalchemy.orm import Session
from rotaplanner.database import engine
from rotaplanner.constants import UNALLOCATED_STAFF
from sqlmodel import Session


class StaffApi(BaseModel):
    "response"
    id: uuid.UUID
    name: str


class AssignmentWithStaff(BaseModel):
    "staff assignment"
    tags: str = Field(default="")
    start_time: datetime.datetime | None
    finish_time: datetime.datetime | None
    staff: StaffApi


class ActivityWithAssignmentsApi(BaseModel):
    "response class for concrete activity"
    activity_id: uuid.UUID
    template_id: uuid.UUID
    name: str | None
    location: str
    activity_start: datetime.datetime
    activity_finish: datetime.datetime
    staff_assignments: list[AssignmentWithStaff]

    def includes_staff(self, staff_id):
        return any(
            (a.staff.id == staff_id or a.staff.name == staff_id)
            for a in self.staff_assignments
        )


def date_from_iso_or_ordinal(s):
    if s is None:
        return None
    if isinstance(s, datetime.date):
        return s
    if isinstance(s, int):
        return datetime.date.fromordinal(s)
    if isinstance(s, str):
        try:
            return datetime.date.fromisoformat(s)
        except ValueError:
            pass
        return datetime.date.fromordinal(int(s))


@dataclass
class GetActivitiesRequest:
    "request"
    start_date: datetime.date = None
    finish_date: datetime.date = None

    def __post_init__(self):
        self.start_date = (
            date_from_iso_or_ordinal(self.start_date) or datetime.date.today()
        )
        self.finish_date = date_from_iso_or_ordinal(
            self.finish_date
        ) or self.start_date + datetime.timedelta(days=9)


GetActivitiesResponse = RootModel[dict[datetime.date, list[ActivityWithAssignmentsApi]]]


def get_activities(request: GetActivitiesRequest, sess) -> GetActivitiesResponse:
    "get activities and assignments for date range"

    activities_query = (
        select(func.date(Activity.activity_start), Activity)
        .where(func.date(Activity.activity_start) >= (request.start_date))
        .where(func.date(Activity.activity_start) <= (request.finish_date))
        .order_by(func.date(Activity.activity_start))
    )
    result = {
        datetime.date.fromisoformat(date): list(a[1] for a in activities)
        for date, activities in itertools.groupby(
            sess.exec(activities_query), lambda k: k[0]
        )
    }
    print(result)
    return result


def get_staff(sess):
    return list(sess.scalars(select(Staff)))


def get_locations(sess):
    return list(sess.scalars(select(Location)))


def get_daterange(sess):

    return tuple(
        datetime.date.fromisoformat(d)
        for d in sess.exec(
            select(
                func.date(func.min(Activity.activity_start)),
                func.date(func.max(Activity.activity_start)),
            )
        ).one()
    )


class ReallocateStaffDragDropEntry(BaseModel):
    activityid: uuid.UUID
    initialstaff: uuid.UUID | None = None
    newstaff: uuid.UUID | None = None
    newdate: datetime.date | None = None


class DragDropHandlerRequest(BaseModel):
    entries: list[ReallocateStaffDragDropEntry] = Field(default_factory=list)


class AllocateStaffRequest(BaseModel):
    alloctype: Literal["allocate"] = "allocate"
    newstaff: uuid.UUID
    activity: uuid.UUID
    force: bool = False


class SwapStaffRequest(BaseModel):
    alloctype: Literal["swapstaff"]
    staff: tuple[uuid.UUID, uuid.UUID]
    activities: list[uuid.UUID]


class RemoveStaffRequest(BaseModel):
    alloctype: Literal["remove"] = "remove"
    initialstaff: uuid.UUID
    activity: uuid.UUID


# StaffChangeRequest=TypeAdapter(Annotated[Union[RestaffRequest,ReallocateStaffRequest,AllocateStaffRequest,SwapStaffRequest,RemoveStaffRequest],Field(discriminator='alloctype')])


def uuid_or_none(s):
    if s is None:
        return None
    if isinstance(s, uuid.UUID):
        return s

    return uuid.UUID(s)


class AllocateActivity(BaseModel):
    activity_id: uuid.UUID
    original_date: datetime.date
    new_date: datetime.date
    original_row: Literal[None] = None
    new_row: uuid.UUID


class DeAllocateActivity(BaseModel):
    activity_id: uuid.UUID
    original_date: datetime.date
    new_date: datetime.date
    original_row: uuid.UUID
    new_row: Literal[None] = None


class ReallocateActivity(BaseModel):
    activity_id: uuid.UUID
    original_date: datetime.date
    new_date: datetime.date
    original_row: uuid.UUID
    new_row: uuid.UUID


def reallocate_activity(entry: ReallocateActivity, sess: Session):
    dates = set()
    errors = []
    activity = sess.get(Activity, entry.activity_id)
    original_staff = sess.get(Staff, entry.original_row)
    new_staff = sess.get(Staff, entry.new_row)
    original_location = sess.get(Location, entry.original_row)
    new_location = sess.get(Location, entry.new_row)
    initial_date = entry.original_date or activity.activity_start.date()
    new_date = entry.new_date or activity.activity_start.date()

    if new_date != initial_date:
        # is there a matching activity on that date?
        result = sess.execute(
            select(Activity)
            .where(func.date(Activity.activity_start) == new_date)
            .where(
                or_(
                    Activity.template_id == activity.template_id,
                    Activity.name == activity.name,
                )
            )
        ).first()
        if result is None:
            return (
                (initial_date, new_date),
                f'Cannot find an activity matching {activity.name} on {new_date.strftime("%d/%m/%Y")}',
            )

        activity = result
    if new_staff != original_staff:
        if new_staff is not None:
            result = sess.execute(
                select(StaffAssignment)
                .where(StaffAssignment.activity_id == entry.activity_id)
                .where(StaffAssignment.staff_id == entry.new_row)
            ).first()
            if result is not None:
                return (
                    (initial_date, new_date),
                    f'{new_staff.name} is already assigned to {activity.name} on {new_date.strftime("%d/%m/%Y")}',
                )

        if original_staff is not None:
            sess.execute(
                delete(StaffAssignment)
                .where(StaffAssignment.activity_id == entry.activity_id)
                .where(StaffAssignment.staff_id == entry.original_row)
            )
        if new_staff is not None:
            sess.add(StaffAssignment(activity_id=entry.activity_id, staff=new_staff))
    if new_location != original_location:
        activity.location = new_location

    return (initial_date, new_date), None


class ReallocateStaff(BaseModel):
    staff: uuid.UUID
    initialactivity: uuid.UUID
    newactivity: uuid.UUID


def reallocate_staff(entry: ReallocateStaff, sess):

    dates = set()
    errors = []
    initialactivity = sess.get(Activity, entry.initialactivity)
    staff = sess.get(Staff, entry.staff)
    newactivity = sess.get(Activity, entry.newactivity)
    dates.add(initialactivity.activity_start.date())
    dates.add(newactivity.activity_start.date())
    result = sess.execute(
        select(StaffAssignment)
        .where(StaffAssignment.activity_id == entry.newactivity)
        .where(StaffAssignment.staff_id == entry.staff)
    ).first()
    if result is not None:
        errors.append(
            f'{staff.name} is already assigned to {newactivity.name} on {newactivity.activity_start.date().strftime("%d/%m/%Y")}'
        )
        return [], errors
    current_allocation = sess.execute(
        select(StaffAssignment)
        .where(StaffAssignment.activity_id == entry.initialactivity)
        .where(StaffAssignment.staff_id == entry.staff)
    ).scalar()
    if current_allocation is None:
        errors.append(f"Data is out of date - please refresh")
        return [], errors
    current_allocation.activity_id = entry.newactivity
    sess.add(current_allocation)
    return dates, errors
