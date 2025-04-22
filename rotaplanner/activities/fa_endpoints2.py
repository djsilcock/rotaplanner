from flask import Blueprint, render_template, request, redirect, url_for
from flask_pydantic import validate
from pydantic import BaseModel
from .queries import (
    GetActivitiesRequest,
    ReallocateStaff,
    ReallocateActivity,
    AllocateActivity,
    DeAllocateActivity,
    get_activities,
    reallocate_staff as do_reallocate_staff,
    reallocate_activity as do_reallocate_activity,
    get_staff,
    get_locations,
    get_daterange,
)
from ..utils import get_instance_fields

from flask_unpoly import unpoly
import datetime
from flask_wtf import FlaskForm
from wtforms import widgets
from wtforms import (
    StringField,
    SelectField,
    FieldList,
    FormField,
    DateField,
    HiddenField,
    SelectMultipleField,
    TimeField,
    BooleanField,
    IntegerField,
    IntegerRangeField,
    Field,
)

from wtforms_sqlalchemy.fields import QuerySelectField, QuerySelectMultipleField

from wtforms.validators import (
    NumberRange,
    StopValidation,
    ValidationError,
    DataRequired,
    Optional,
    UUID as ValidateUUID,
)
from rotaplanner.date_rules import (
    Rule,
    GroupType,
    RuleType,
    RuleGroup,
    DateType,
    DateTag,
)
from ..models import Activity, Location, Requirement, ActivityTag, Skill, ActivityType
import uuid
from typing import Any, Self, Sequence, Literal, Annotated
from rotaplanner.utils import discard_extra_kwargs
from sqlalchemy import inspect, select

from fastapi import APIRouter, HTTPException, Query, Response
from sqlmodel import Session
from rotaplanner.database import engine

blueprint = Blueprint("activities", __name__)

router = APIRouter()


def daterange(start_date, finish_date):
    d = start_date
    while d <= finish_date:
        yield d
        d += datetime.timedelta(days=1)


class LocationResponse(BaseModel):
    id: uuid.UUID
    name: str


class StaffResponse(BaseModel):
    id: uuid.UUID
    name: str


class StaffAssignmentResponse(BaseModel):
    staff: StaffResponse


class ActivityResponse(BaseModel):
    id: uuid.UUID
    name: str
    start_time: int
    finish_time: int
    location: Location | None
    staff_assignments: list[StaffAssignmentResponse]


class ActivitiesByDateResponse(BaseModel):
    date: datetime.date
    activities: list[ActivityResponse]


class ActivitiesByDateRequest(BaseModel):
    start_date: datetime.date | None = None
    finish_date: datetime.date | None = None
    date: list[datetime.date] | None = None
    include_all: bool = True


@router.get("/api/activities/by_date", operation_id="activitiesByDate")
def table_by_date(
    query: Annotated[ActivitiesByDateRequest, Query()], response: Response
) -> list[ActivitiesByDateResponse]:
    if query.start_date is None:
        query.start_date = min(query.date)
    if query.finish_date is None:
        query.finish_date = max(query.date)
    print(query)
    with Session(engine) as session:
        response.headers["Last-Modified"] = "Wed, 21 Oct 2015 07:28:00 GMT"
        response.headers["Cache-Control"] = "max-age=10"
        activities = get_activities(query, session)
        print(activities)
        return activities_by_date(query, activities)


def activities_by_date(request, activities):
    return [
        ActivitiesByDateResponse(
            date=activity_date,
            activities=[
                ActivityResponse(
                    id=activity.id,
                    name=activity.name,
                    start_time=activity.activity_start.time().hour,
                    finish_time=activity.activity_finish.time().hour,
                    location=(
                        LocationResponse.model_validate(
                            activity.location, from_attributes=True
                        )
                        if activity.location
                        else None
                    ),
                    staff_assignments=[
                        StaffAssignmentResponse.model_validate(
                            assn, from_attributes=True
                        )
                        for assn in activity.staff_assignments
                    ],
                )
                for activity in activities.get(activity_date, [])
            ],
        )
        for activity_date in (
            daterange(request.start_date, request.finish_date)
            if request.include_all
            else activities
        )
    ]


class ReallocateActivityOkResponse(BaseModel):
    status: Literal["ok"] = "ok"
    data: list[ActivitiesByDateResponse]


class ReallocateActivityErrorResponse(BaseModel):
    status: Literal["error"] = "error"
    error: str
    data: list[ActivitiesByDateResponse]


@router.post("/api/reallocate_activity", operation_id="reallocateActivity")
def reallocate_activity(
    request: AllocateActivity | DeAllocateActivity | ReallocateActivity,
) -> ReallocateActivityOkResponse | ReallocateActivityErrorResponse:
    with Session(engine) as session:
        dates, error = do_reallocate_activity(request, session)
        date_range = min(dates), max(dates)
        activities = get_activities(
            GetActivitiesRequest(start_date=date_range[0], finish_date=date_range[1]),
            session,
        )
        if error is None:
            session.commit()
            return ReallocateActivityOkResponse(
                data=activities_by_date(
                    ActivitiesByDateRequest(
                        start_date=date_range[0], finish_date=date_range[1]
                    ),
                    activities,
                )
            )
        else:
            session.rollback()
            return ReallocateActivityErrorResponse(
                error=error,
                data=activities_by_date(
                    ActivitiesByDateRequest(
                        start_date=date_range[0], finish_date=date_range[1]
                    ),
                    activities,
                ),
            )


@router.post("/api/reallocate_staff")
def reallocate_staff(
    request: ReallocateStaff,
) -> ReallocateActivityErrorResponse | ReallocateActivityOkResponse:
    with Session(engine) as session:
        dates, errors = do_reallocate_staff(request, session)
        activities = get_activities(
            GetActivitiesRequest(start_date=min(dates), finish_date=max(dates)), session
        )
        if len(errors) == 0:
            session.commit()
            return ReallocateActivityOkResponse(data=activities_by_date(activities))
        else:
            session.rollback()
            return ReallocateActivityErrorResponse(data=activities_by_date(activities))


def get_activity_templates(session):
    return session.scalars(
        select(Activity).where(Activity.type == ActivityType.TEMPLATE)
    )


class ActivityInfoResponse(BaseModel):
    name: str
    activity_tags: list[ActivityTag]
    # requirements: RequirementGroup
    location: Location


class ActivityTemplateResponse(BaseModel):
    id: uuid.UUID
    name: str
    activity_tags: list[ActivityTag]
    # requirements: RequirementGroup
    location: Location
    start_time: datetime.time
    finish_time: datetime.time
    recurrence_rules: RuleGroup


@router.get("/api/activity_templates")
def activity_templates() -> list[ActivityTemplateResponse]:
    with Session(engine) as session:
        return [
            ActivityTemplateResponse(
                id=templ.id,
                name=templ.activity_info.name,
                activity_tags=templ.activity_info.activity_tags,
                location=templ.activity_info.location,
                start_time=templ.start_time,
                finish_time=templ.finish_time,
                recurrence_rules=templ.recurrence_rules,
            )
            for templ in session.scalars(
                select(Activity).where(Activity.type == ActivityType.TEMPLATE)
            )
        ]


def ordinal(index):
    if (index % 100 > 3) and (index % 100 < 21):
        return f"{index}th"
    elif index % 10 == 1:
        return f"{index}st"
    elif index % 10 == 2:
        return f"{index}nd"
    elif index % 10 == 3:
        return f"{index}rd"
    else:
        return f"{index}th"


def get_date_tags(session):
    return session.scalars(select(DateTag))


def get_skills(session):
    return session.scalars(select(Skill))


def get_tags(session):
    return session.scalars(select(ActivityTag))
