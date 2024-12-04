"Api requests and responses"

import datetime
import itertools
import uuid
import enum

from .models import Activity, Staff, StaffAssignment, Location
from pydantic import BaseModel, Field, RootModel, TypeAdapter
from dataclasses import dataclass
from sqlalchemy import func, or_, select, delete
from typing import Literal, Annotated, Union, Self

from sqlalchemy.orm import Session
from rotaplanner.database import db
from rotaplanner.constants import UNALLOCATED_STAFF


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


@dataclass
class GetActivitiesRequest:
    "request"
    start_date: datetime.date = datetime.date.today()
    finish_date: datetime.date = datetime.date.today() + datetime.timedelta(days=364)

    def __post_init__(self):
        if isinstance(self.start_date, str):
            self.start_date = datetime.date.fromisoformat(self.start_date)
        if isinstance(self.finish_date, str):
            self.finish_date = datetime.date.fromisoformat(self.finish_date)


GetActivitiesResponse = RootModel[dict[datetime.date, list[ActivityWithAssignmentsApi]]]


def get_activities(request: GetActivitiesRequest) -> GetActivitiesResponse:
    "get activities and assignments for date range"
    sess = db.session
    activities_query = (
        select(func.date(Activity.activity_start), Activity)
        .where(func.date(Activity.activity_start) >= (request.start_date))
        .where(func.date(Activity.activity_start) <= (request.finish_date))
        .order_by(func.date(Activity.activity_start))
    )
    result = {
        datetime.date.fromisoformat(date): list(a[1] for a in activities)
        for date, activities in itertools.groupby(
            sess.execute(activities_query), lambda k: k[0]
        )
    }
    print(result)
    return result


def get_staff():
    return list(db.session.scalars(select(Staff)))


def get_locations():
    return list(db.session.scalars(select(Location)))


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


class ReallocateActivity:
    activityid: uuid.UUID
    initialstaff: uuid.UUID
    newstaff: uuid.UUID
    newdate: datetime.date
    entries: list[Self]


def reallocate_activities(entries: list[ReallocateActivity]):
    print(entries)
    sess = db.session
    dates = set()
    errors = []
    for entry in entries:
        activity = sess.get(Activity, entry.activityid)
        initialstaff = (
            sess.get(Staff, entry.initialstaff)
            if entry.initialstaff is not None
            else None
        )
        newstaff = (
            sess.get(Staff, entry.newstaff) if entry.newstaff is not None else None
        )
        if entry.newdate != activity.activity_start.date():
            # is there a matching activity on that date?
            result = sess.execute(
                select(Activity)
                .where(func.date(Activity.activity_start) == entry.newdate)
                .where(
                    or_(
                        Activity.template_id == activity.template_id,
                        Activity.name == activity.name,
                    )
                )
            ).first()
            if result is None:
                errors.append(
                    f'Cannot find an activity matching {activity.name} on {entry.newdate.strftime("%d/%m/%Y")}'
                )
                continue
            activity = result
        result = sess.execute(
            select(StaffAssignment)
            .where(StaffAssignment.activity_id == activity.id)
            .where(StaffAssignment.staff_id == entry.newstaff)
        ).first()
        if result is not None:
            errors.append(
                f'{newstaff.name} is already assigned to {activity.name} on {entry.newdate.strftime("%d/%m/%Y")}'
            )
            continue
        print(activity)
        if entry.initialstaff:
            sess.execute(
                delete(StaffAssignment)
                .where(StaffAssignment.activity_id == entry.activityid)
                .where(StaffAssignment.staff_id == entry.initialstaff)
            )
        if entry.newstaff and entry.newstaff != UNALLOCATED_STAFF:
            sess.add(
                StaffAssignment(activity_id=entry.activityid, staff_id=entry.newstaff)
            )
        dates.update(
            act.activity_start.date()
            for act in sess.scalars(
                select(Activity).where(Activity.id == entry.activityid)
            )
        )
    return dates, errors


class ReallocateStaff:
    staff: uuid.UUID
    initialactivity: uuid.UUID
    newactivity: uuid.UUID


def reallocate_staff(entry: ReallocateStaff):
    sess = db.session
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
