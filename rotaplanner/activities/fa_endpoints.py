from pydantic import BaseModel, TypeAdapter, Field
from fastapi.templating import Jinja2Templates

import datetime
from rotaplanner.date_rules import (
    Rule,
    GroupType,
    RuleType,
    RuleGroup,
    DateType,
    DateTag,
)
from ..models import (
    Activity,
    Location,
    Requirement,
    RequirementGroup,
    ActivityTag,
    Skill,
    ActivityType,
)
import uuid
from typing import Any, Self, Sequence, Literal, Annotated, Union
from rotaplanner.utils import discard_extra_kwargs
import dataclasses

from fastapi import APIRouter, HTTPException, Query, Response, Depends, Request

from rotaplanner.database import Connection


router = APIRouter()
templates = Jinja2Templates(directory="rotaplanner/templates")


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


@dataclasses.dataclass
class StaffAssignmentDisplay:
    staff: str
    start_time: int | None = None
    finish_time: int | None = None


@dataclasses.dataclass
class ActivityDisplay:
    activity_id: uuid.UUID
    name: str
    start_time: datetime.datetime
    finish_time: datetime.datetime
    location_id: str
    location_name: str
    staff_assignments: list[StaffAssignmentDisplay]


@dataclasses.dataclass
class ActivityCell:
    cell_id: str
    activities: list[ActivityDisplay]


def get_locations(connection: Connection) -> dict[uuid.UUID, Location]:
    sql_query = """
    SELECT id, name
    FROM locations
    """
    with connection:
        result = connection.execute(sql_query).fetchall()
    return {row[0]: Location(id=row[0], name=row[1]) for row in result}


def get_activities(
    connection: Connection, start_date: datetime.date, finish_date: datetime.date
) -> list[Activity]:

    sql_query = """
        SELECT
            activities.id as activity_id, 
            activities.name as activity_name, 
            activity_start, 
            activity_finish, 
            locations.name as location_name,
            locations.id as location_id,
            staff_assignments.staff_id, 
            staff.name

        FROM activities
        LEFT JOIN locations ON activities.location_id = locations.id
        LEFT JOIN staff_assignments ON activities.id = staff_assignments.activity_id
        LEFT JOIN staff on staff_assignments.staff_id = staff.id
        WHERE date(activity_start) >= :start_date
        AND date(activity_start) <= :finish_date
        ORDER BY activity_start
    """
    with connection:
        cursor = connection.execute(
            sql_query,
            {
                "start_date": start_date,
                "finish_date": finish_date,
            },
        )
        result = cursor.fetchall()
        activities = {}
        earliest_date = None
        latest_date = None
        for (
            activity_id,
            name,
            start_time,
            finish_time,
            location_name,
            location_id,
            staff_id,
            staff_name,
        ) in result:

            if activity_id not in activities:
                activities[activity_id] = ActivityDisplay(
                    activity_id=activity_id,
                    name=name,
                    start_time=start_time,
                    finish_time=finish_time,
                    location_id=location_id,
                    location_name=location_name,
                    staff_assignments=[],
                )
                if earliest_date is None or start_time < earliest_date:
                    earliest_date = start_time
                if latest_date is None or finish_time > latest_date:
                    latest_date = finish_time
            if staff_id:
                activities[activity_id].staff_assignments.append(
                    StaffAssignmentDisplay(staff=staff_name)
                )
        return activities, earliest_date, latest_date


def get_activity_cells_by_location(
    connection: Connection,
    start_date: datetime.date = datetime.date(1970, 1, 1),
    finish_date: datetime.date = datetime.date(2100, 1, 1),
    specifically_include=(),
) -> list[ActivityCell]:

    activities, earliest_date, latest_date = get_activities(
        connection, start_date, finish_date
    )

    activity_cells = {}
    for date, location_id in specifically_include:
        key = f"cell-{date.isoformat()}-{location_id}"
        if key not in activity_cells:
            activity_cells[key] = ActivityCell(cell_id=key, activities=[])

    for activity_id, activity in activities.items():
        key = f"cell-{activity.start_time.date().isoformat()}-{activity.location_id}"
        if key not in activity_cells:
            activity_cells[key] = ActivityCell(cell_id=key, activities=[])
        activity_cells[key].activities.append(activity)
    print(activity_cells)
    return (list(activity_cells.values()), earliest_date.date(), latest_date.date())


@router.get("/template_test/location")
def template_test(request: Request, connection: Connection) -> Response:

    (activity_cells, earliest_date, latest_date) = get_activity_cells_by_location(
        connection
    )
    y_axis = get_locations(connection)
    dates = [
        earliest_date + datetime.timedelta(days=i)
        for i in range((latest_date - earliest_date).days + 1)
    ]
    return templates.TemplateResponse(
        "table.html.j2",
        {
            "request": request,
            "date": datetime.date.today(),
            "dates": dates,
            "y_axis": y_axis,
            "replacement_cells": activity_cells,
            "grid_type": "location",
        },
    )


class LocationGridCell(BaseModel):
    date: datetime.date
    location: str | None = None


class MoveActivityInLocationGrid(BaseModel):
    activityId: str
    from_cell: LocationGridCell
    to_cell: LocationGridCell


@router.post("/template_test/location", operation_id="moveActivityInLocationGrid")
def move_activity_in_location_grid(
    request: Request, entry: MoveActivityInLocationGrid, connection: Connection
):
    try:
        print(entry)
        datedelta = entry.to_cell.date - entry.from_cell.date
        sql_query = """
        SELECT activity_start, activity_finish
        FROM activities
        WHERE id = :activity_id
        """
        result = connection.execute(
            sql_query,
            {
                "activity_id": entry.activityId,
            },
        ).fetchone()
        print("ok so far", tuple(result))
        if result is None:
            raise ReallocationError("Activity not found")
        start_time, finish_time = result
        new_start_time = start_time + datedelta
        new_finish_time = finish_time + datedelta
        sql_query = """
        UPDATE activities
        SET activity_start = :new_start_time, activity_finish = :new_finish_time, location_id = :new_location
        WHERE id = :activity_id
        """
        with connection:
            connection.execute(
                sql_query,
                {
                    "new_start_time": new_start_time,
                    "new_finish_time": new_finish_time,
                    "new_location": entry.to_cell.location,
                    "activity_id": entry.activityId,
                },
            )
            print(
                connection.execute(
                    "SELECT * FROM activities where id=?", (entry.activityId,)
                ).fetchall()
            )
    except ReallocationError as e:
        return {"status": "error", "error": str(e)}
    activity_cells = get_activity_cells_by_location(
        connection,
        min(entry.from_cell.date, entry.to_cell.date),
        max(entry.from_cell.date, entry.to_cell.date),
        specifically_include=[
            (entry.from_cell.date, entry.from_cell.location),
            (entry.to_cell.date, entry.to_cell.location),
        ],
    )[0]
    return templates.TemplateResponse(
        "table_cells.html.j2",
        {"request": request, "replacement_cells": activity_cells},
    )


class StaffGridCell(BaseModel):
    date: datetime.date
    staff: uuid.UUID | None


class MoveActivityInStaffGrid(BaseModel):
    activityId: uuid.UUID
    from_cell: StaffGridCell
    to_cell: StaffGridCell


class MoveStaffInLocationGrid(BaseModel):
    staffId: uuid.UUID
    from_activity: uuid.UUID | None = None
    to_activity: uuid.UUID | None = None


@router.post("/rota/drag_and_drop", operation_id="dragAndDrop")
def drag_and_drop():
    pass


@router.get("/api/activities/by_date", operation_id="activitiesByDate")
def table_by_date(
    query: Annotated[ActivitiesByDateRequest, Query()], connection: Connection
) -> list[ActivitiesByDateResponse]:
    if query.start_date is None:
        query.start_date = min(query.date)
    if query.finish_date is None:
        query.finish_date = max(query.date)
    sql_query = """
    SELECT
        date(activity_start) as date, 
        activities.id as activity_id, 
        activities.name as activity_name, 
        activities.location_id as location_id,
        locations.name as location_name,
        activity_start, 
        activity_finish, 
        staff_assignments.staff_id, 
        staff.name

    FROM activities
    LEFT JOIN locations ON activities.location_id = locations.id
    LEFT JOIN staff_assignments ON activities.id = staff_assignments.activity_id
    LEFT JOIN staff on staff_assignments.staff_id = staff.id
    WHERE date(activity_start) >= :start_date
    AND date(activity_start) <= :finish_date
    ORDER BY date(activity_start)
    """

    with connection:
        cursor = connection.execute(
            sql_query,
            {
                "start_date": query.start_date.isoformat(),
                "finish_date": query.finish_date.isoformat(),
            },
        )
        result = cursor.fetchall()
        dates = {}
        activities = {}
        for (
            activity_date,
            activity_id,
            name,
            location_id,
            location_name,
            start_time,
            finish_time,
            staff_id,
            staff_name,
        ) in result:
            if activity_date not in dates:
                dates[activity_date] = []
            if activity_id not in activities:
                activities[activity_id] = {
                    "id": activity_id,
                    "name": name,
                    "location": (
                        {"id": location_id, "name": location_name}
                        if location_id
                        else None
                    ),
                    "start_time": start_time.hour,
                    "finish_time": finish_time.hour,
                    "staff_assignments": [],
                }
            if staff_id:
                activities[activity_id]["staff_assignments"].append(
                    {"staff": {"id": staff_id, "name": staff_name}}
                )
            dates[activity_date].append(activities[activity_id])
    return [
        ActivitiesByDateResponse.model_validate({"date": date, "activities": acts})
        for date, acts in dates.items()
    ]


# handlers for drag and drop actions on rota grid
# these handlers are called by the frontend when a user drags an activity to a new location or staff member
# the handlers then update the database to reflect the new location or staff member
# the handlers then return the updated rota grid to the frontend


class ReallocationError(ValueError):
    pass


class ExitEarly(BaseException):
    pass


class ReallocateActivityOkResponse(BaseModel):
    status: Literal["ok"] = "ok"
    data: list[ActivitiesByDateResponse]


class ReallocateActivityErrorResponse(BaseModel):
    status: Literal["error"] = "error"
    error: str
    data: list[ActivitiesByDateResponse]


class MoveActivityInStaffGrid(BaseModel):
    activity_id: uuid.UUID
    new_date: datetime.date
    original_staff: uuid.UUID | None
    new_staff: uuid.UUID | None


def find_matching_activity(
    activity_id: uuid.UUID, new_date: datetime.date, connection: Connection
) -> uuid.UUID | None:
    """find_matching_activity is a helper function that finds an activity that matches the activity_id and new_date
    this is used when moving an activity to a new date
    if the activity is not found, an error is raised
    if the activity is found, the activity_id is returned
    @param activity_id: the id of the activity to be moved
    @param new_date: the new date for the activity
    @return the id of the matching activity
    @raise ReallocationError: if the activity is not found
    """
    sql_query = """
            SELECT act1.id from activities act1,activities act2
            WHERE date(act2.activity_start) = :new_date
            AND (act1.template_id = act2.template_id OR act1.name = act2.name)
            AND act1.id = :activity_id
            """
    result = [
        uuid.UUID(line[0])
        for line in connection.execute(
            sql_query,
            {
                "new_date": new_date.isoformat(),
                "activity_id": str(activity_id),
            },
        ).fetchall()
    ]
    if activity_id in result:
        return activity_id
    if len(result) == 0:
        raise ReallocationError(
            f'Cannot find an matching activity on {new_date.strftime("%d/%m/%Y")}'
        )
    if len(result) > 1:
        raise ReallocationError(
            f'Found multiple matching activities on {new_date.strftime("%d/%m/%Y")}'
        )
    return result[0]


def deallocate_staff(
    activity_id: uuid.UUID, staff_id: uuid.UUID, connection: Connection
):
    """
    deallocate_staff is a helper function that removes a staff member from an activity
    @param activity_id: the id of the activity to be modified
    @param staff_id: the id of the staff member to be removed
    """
    sql_query = """
                DELETE FROM staff_assignments
                WHERE activity_id = :activity_id
                AND staff_id = :staff_id
                """
    with connection:
        connection.execute(
            sql_query,
            {
                "activity_id": str(activity_id),
                "staff_id": str(staff_id),
            },
        )


def allocate_staff(
    activity_id: uuid.UUID,
    staff_id: uuid.UUID,
    connection: Connection,
    check_first: bool = True,
):
    """
    allocate_staff is a helper function that assigns a staff member to an activity
    @param activity_id: the id of the activity to be modified
    @param staff_id: the id of the staff member to be assigned
    @param check_first: a boolean that determines whether to check if the staff member is already assigned to the activity
    @raise ReallocationError: if the staff member is already assigned to the activity
    @raise ReallocationError: if the staff member is already busy during the activity
    """
    if check_first:
        check_assignment_possible(activity_id, staff_id)
    sql_query = """
                INSERT INTO staff_assignments (activity_id, staff_id) VALUES (:activity_id, :staff_id)
                """
    connection.execute(
        sql_query,
        {
            "activity_id": str(activity_id),
            "staff_id": str(staff_id),
        },
    )


def check_assignment_possible(
    activity_id: uuid.UUID, staff_id: uuid.UUID, connection: Connection
):
    """
    check_assignment_possible is a helper function that checks if a staff member can be assigned to an activity
    @param activity_id: the id of the activity to be checked
    @param staff_id: the id of the staff member to be checked
    @raise ReallocationError: if the staff member is already assigned to the activity
    @raise ReallocationError: if the staff member is already busy during the activity
    """
    sql_query = """
            SELECT 
                ass.staff_id,
                a.activity_id,
                a.activity_start,
                a.activity_finish
            FROM 
                staff_assignments ass
            JOIN 
                activities a ON ass.activity_id = a.id
            WHERE 
                ass.staff_id = :staff_id
                AND a.activity_start < (SELECT activity_finish FROM activities WHERE id = :activity_id)
                AND a.activity_finish > (SELECT activity_start FROM activities WHERE id = :activity_id);
        """

    result = connection.execute(
        sql_query,
        {
            "staff_id": staff_id,
            "activity_id": activity_id,
        },
    ).fetchall()
    if any(a[1] == activity_id for a in result):
        raise ReallocationError("Already assigned to that activity")
    if len(result) > 0:
        raise ReallocationError("Already busy during that time at that time")
    return True


@router.post("/api/move_activity_in_staff_grid", operation_id="moveActivityInStaffGrid")
def move_activity_in_staff_grid(
    entry: MoveActivityInStaffGrid,
) -> ReallocateActivityOkResponse | ReallocateActivityErrorResponse:

    dates = set()
    errors = []
    try:

        new_activity = find_matching_activity(entry.activity_id, entry.new_date)

        if (entry.activity_id, entry.original_staff) == (new_activity, entry.new_staff):
            # NOOP
            raise ExitEarly
        check_assignment_possible(new_activity, entry.new_staff)

        if entry.original_staff is not None:
            deallocate_staff(entry.activity_id, entry.original_staff)
        if entry.new_staff is not None:
            allocate_staff(new_activity, entry.new_staff)
    except ReallocationError as e:
        return ReallocateActivityErrorResponse(
            error=str(e),
            data=table_by_date(
                ActivitiesByDateRequest(date=[entry.original_date, entry.new_date])
            ),
        )
    except ExitEarly:
        pass
    return ReallocateActivityOkResponse(
        data=table_by_date(
            ActivitiesByDateRequest(date=[entry.original_date, entry.new_date])
        )
    )


class MoveActivityInLocationGrid(BaseModel):
    activity_id: uuid.UUID
    original_date: datetime.date
    new_date: datetime.date
    original_location: uuid.UUID | None
    new_location: uuid.UUID | None


@router.post(
    "/api/move_activity_in_location_grid", operation_id="moveActivityInLocationGrid"
)
def move_activity_in_location_grid(
    entry: MoveActivityInLocationGrid,
    connection: Connection,
) -> ReallocateActivityOkResponse | ReallocateActivityErrorResponse:
    try:
        datedelta = entry.new_date - entry.original_date
        sql_query = """
        SELECT activity_start, activity_finish
        FROM activities
        WHERE id = :activity_id
        """
        result = connection.execute(
            sql_query,
            {
                "activity_id": str(entry.activity_id),
            },
        ).fetchone()
        if result is None:
            raise ReallocationError("Activity not found")
        start_time, finish_time = result
        new_start_time = start_time + datedelta
        new_finish_time = finish_time + datedelta
        sql_query = """
        UPDATE activities
        SET activity_start = :new_start_time, activity_finish = :new_finish_time, location_id = :new_location
        WHERE id = :activity_id
        """
        with connection:
            connection.execute(
                sql_query,
                {
                    "new_start_time": new_start_time,
                    "new_finish_time": new_finish_time,
                    "new_location": entry.new_location,
                    "activity_id": entry.activity_id,
                },
            )
    except ReallocationError as e:
        return ReallocateActivityErrorResponse(
            error=str(e),
            data=table_by_date(
                ActivitiesByDateRequest(date=[entry.original_date, entry.new_date])
            ),
        )
    return ReallocateActivityOkResponse(
        data=table_by_date(
            ActivitiesByDateRequest(date=[entry.original_date, entry.new_date])
        )
    )


class ReallocateStaffToActivity(BaseModel):
    original_activity_id: uuid.UUID
    new_activity_id: uuid.UUID | None
    staff: uuid.UUID


@router.post(
    "/api/reallocate_staff_to_activity", operation_id="reallocateStaffToActivity"
)
def reallocate_staff_to_activity(
    entry: ReallocateStaffToActivity,
) -> ReallocateActivityOkResponse | ReallocateActivityErrorResponse:
    try:
        check_assignment_possible(entry.new_activity_id, entry.staff)
        deallocate_staff(entry.original_activity_id, entry.staff)
        if entry.new_activity_id is not None:
            allocate_staff(entry.new_activity_id, entry.staff)
    except ReallocationError as e:
        return ReallocateActivityErrorResponse(
            error=str(e),
            data=table_by_date(
                ActivitiesByDateRequest(date=[entry.original_date, entry.new_date])
            ),
        )
    return ReallocateActivityOkResponse(
        data=table_by_date(
            ActivitiesByDateRequest(date=[entry.original_date, entry.new_date])
        )
    )


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
    activity_tags: list[uuid.UUID]
    requirements: RequirementGroup
    location: uuid.UUID
    start_time: datetime.time
    finish_time: datetime.time
    recurrence_rules: RuleGroup


class ActivityTemplateListItem(BaseModel):
    id: uuid.UUID
    name: str


@router.get("/api/activity_templates", operation_id="getActivityTemplates")
def activity_templates(connection: Connection) -> list[ActivityTemplateListItem]:
    sql_query = """
        SELECT id,name
        FROM activities
        WHERE type = 'TEMPLATE'
    """
    with connection:
        result = connection.execute(sql_query).fetchall()
    return [
        ActivityTemplateListItem(id=uuid.UUID(row[0]), name=row[1]) for row in result
    ]


def get_locations(connection: Connection) -> dict[uuid.UUID, Location]:
    sql_query = """
    SELECT id, name
    FROM locations
    """
    with connection:
        result = connection.execute(sql_query).fetchall()
    return {row[0]: Location(id=row[0], name=row[1]) for row in result}


def get_activity_tags(connection: Connection) -> dict[uuid.UUID, ActivityTag]:
    sql_query = """
    SELECT id, name
    FROM activity_tags
    """
    with connection:
        result = connection.execute(sql_query).fetchall()
    return {row[0]: ActivityTag(id=row[0], name=row[1]) for row in result}


def get_skills(connection: Connection) -> dict[uuid.UUID, Skill]:
    sql_query = """
    SELECT id, name
    FROM skills
    """
    with connection:
        result = connection.execute(sql_query).fetchall()
    return {row[0]: Skill(id=row[0], name=row[1]) for row in result}


Locations = Annotated[dict[uuid.UUID, Location], Depends(get_locations)]
ActivityTags = Annotated[dict[uuid.UUID, ActivityTag], Depends(get_activity_tags)]
Skills = Annotated[dict[uuid.UUID, Skill], Depends(get_skills)]


@router.get("/api/activity_template/{activity_id}", operation_id="getActivityTemplate")
def activity_template(
    activity_id: uuid.UUID, connection: Connection
) -> ActivityTemplateResponse:

    with connection:
        result = connection.execute(
            "SELECT id from activity_tag_assocs WHERE activity_id = :activity_id",
            {
                "activity_id": str(activity_id),
            },
        ).fetchall()
        tags = [uuid.UUID(row[0]) for row in result]

    with connection:
        result = connection.execute(
            """
        SELECT
            name,
            location_id,
            activity_start,
            activity_finish,
            recurrence_rules,
            requirements,
            activity_tags.id AS tag_id
        FROM activities
        LEFT JOIN activity_tag_assocs ON activities.id = activity_tag_assocs.activity_id
        WHERE activities.id = :activity_id
    """,
            {
                "activity_id": str(activity_id),
            },
        ).fetchone()
    return ActivityTemplateResponse(
        id=activity_id,
        name=result[0],
        location=result[1],
        start_time=result[3],
        finish_time=result[4],
        recurrence_rules=RuleGroup.from_json(result[5]),
        requirements=RequirementGroup.from_json(result[6]),
        activity_tags=set(uuid.UUID(row["tag_id"]) for row in result),
    )


@router.post(
    "/api/activity_template/{activity_id}", operation_id="updateActivityTemplate"
)
def update_activity_template(
    activity_template: ActivityTemplateResponse, connection: Connection
):
    try:
        with connection:
            connection.execute(
                """
            UPDATE activities
            SET name = :name, 
                location_id = :location, 
                activity_start = :start_time, 
                activity_finish = :finish_time, 
                recurrence_rules = :recurrence_rules, 
                requirements = :requirements
            WHERE id = :activity_id
            """,
                {
                    "name": activity_template.name,
                    "location": activity_template.location,
                    "start_time": activity_template.start_time,
                    "finish_time": activity_template.finish_time,
                    "recurrence_rules": activity_template.recurrence_rules.model_dump_json(),
                    "requirements": activity_template.requirements.model_dump_json(),
                    "activity_id": activity_template.id,
                },
            )

            connection.execute(
                "DELETE FROM activity_tag_assocs WHERE activity_id = :activity_id",
                {
                    "activity_id": activity_template.id,
                },
            )
            connection.executemany(
                "INSERT INTO activity_tag_assocs (activity_id, tag_id) VALUES (:activity_id, :tag_id)",
                [
                    {"activity_id": activity_template.id, "tag_id": tag}
                    for tag in activity_template.activity_tags
                ],
            )
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


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
