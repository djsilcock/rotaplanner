from pydantic import BaseModel, RootModel
from typing_extensions import TypeAliasType
import datetime
from itertools import groupby
import uuid

from typing import Literal
import dataclasses

from fastapi import APIRouter, Response, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from rotaplanner.database import Connection
from sqlite3 import IntegrityError

from rotaplanner.utils import get_locations, get_staff

router = APIRouter()


class ReallocationError(Exception):
    pass


def daterange(start_date, finish_date):
    d = start_date
    while d <= finish_date:
        yield d
        d += datetime.timedelta(days=1)


class DateRange(BaseModel):
    start: datetime.date
    finish: datetime.date


class LabelledUUID(BaseModel):
    id: uuid.UUID
    name: str


class RotaConfig(BaseModel):
    date_range: DateRange
    staff: list[LabelledUUID]
    locations: list[LabelledUUID]


@router.get(
    "/api/config/rota-grid/",
    description="Row and column headings for the rota grid",
    operation_id="tableConfig",
)
def rota_grid(connection: Connection) -> RotaConfig:
    with connection:

        staff = [
            LabelledUUID(id=staff[0], name=staff[1])
            for staff in connection.execute(
                "SELECT id,name FROM staff ORDER BY name"
            ).fetchall()
        ]

        locations = [
            LabelledUUID(id=location[0], name=location[1])
            for location in connection.execute(
                "SELECT id,name FROM locations ORDER BY name"
            ).fetchall()
        ]

        # get start and end dates from the database
        start_date, finish_date = connection.execute(
            "SELECT DATE(MIN(activity_start)),DATE(MAX(activity_finish)) FROM activities"
        ).fetchone()

    return RotaConfig(
        staff=staff,
        locations=locations,
        date_range=DateRange(start=start_date, finish=finish_date),
    )


@dataclasses.dataclass
class StaffAssignmentDisplay:
    staff: LabelledUUID
    start_time: int | None = None
    finish_time: int | None = None


@dataclasses.dataclass
class LocationDisplay:
    location_id: str
    name: str


class ActivityDisplay(BaseModel):
    activity_id: str
    name: str
    start_time: datetime.datetime
    finish_time: datetime.datetime
    location: LabelledUUID | None
    staff_assignments: list[StaffAssignmentDisplay]


class Toast(BaseModel):
    kind: Literal["success", "error"]
    title: str
    description: str


class ActivityResponse(BaseModel):
    data: dict[datetime.date, list[ActivityDisplay]]
    toasts: list[Toast]


def get_activities(
    connection: Connection, start_date: datetime.date, finish_date: datetime.date
) -> tuple[dict[str, ActivityDisplay], datetime.date, datetime.date]:

    # print("get_activities", start_date, finish_date)
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
        WHERE date(activity_start) >= date(:start_date)
        AND date(activity_start) <= date(:finish_date)
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
                    activity_id=str(activity_id),
                    name=name,
                    start_time=start_time,
                    finish_time=finish_time,
                    location=(
                        LabelledUUID(
                            id=location_id,
                            name=location_name,
                        )
                        if location_id
                        else None
                    ),
                    staff_assignments=[],
                )
                if earliest_date is None or start_time < earliest_date:
                    earliest_date = start_time
                if latest_date is None or finish_time > latest_date:
                    latest_date = finish_time
            if staff_id:
                activities[activity_id].staff_assignments.append(
                    StaffAssignmentDisplay(
                        staff=LabelledUUID(id=staff_id, name=staff_name)
                    )
                )
        return activities, earliest_date or start_date, latest_date or finish_date


@router.get("/activities_by_date", operation_id="getActivitiesByDate")
def get_activities_grouped_by_date(
    connection: Connection,
    start_date: datetime.date = datetime.date(1970, 1, 1),
    finish_date: datetime.date = datetime.date(2100, 1, 1),
    toasts: list[Toast] | None = None,
) -> ActivityResponse:
    """Get activities grouped by date."""
    activities, earliest_date, latest_date = get_activities(
        connection, start_date, finish_date
    )
    grouped = {}
    for activity in activities.values():
        date = activity.start_time.date()
        if date not in grouped:
            grouped[date] = []
        grouped[date].append(activity)
    return ActivityResponse(data=grouped, toasts=toasts or [])


class LocationGridCell(BaseModel):
    date: datetime.date
    location: str | None = None


class MoveActivityInLocationGrid(BaseModel):

    activity_id: str
    from_cell: LocationGridCell
    to_cell: LocationGridCell


class MoveStaffInLocationGrid(BaseModel):
    staffId: str
    from_activity: str | None = None
    to_activity: str | None = None


@router.post(
    "/rota_grid/location/drag_activity", operation_id="moveActivityInLocationGrid"
)
def move_activity_in_location_grid(
    request: Request, entry: MoveActivityInLocationGrid, connection: Connection
) -> ActivityResponse:
    toasts = []
    try:
        # print(entry)
        datedelta = entry.to_cell.date - entry.from_cell.date
        sql_query = """
        SELECT activity_start, activity_finish,location_id
        FROM activities
        WHERE id = :activity_id
        """
        result = connection.execute(
            sql_query,
            {
                "activity_id": entry.activity_id,
            },
        ).fetchone()
        # print("ok so far", tuple(result))
        if result is None:
            raise ReallocationError("Activity not found")
        start_time, finish_time, original_location = result
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
                    "activity_id": entry.activity_id,
                },
            )

    except ReallocationError as e:
        toasts.append(
            Toast(
                kind="error",
                title="Error moving activity",
                description=str(e),
            )
        )

    return get_activities_grouped_by_date(
        connection,
        start_date=min(entry.from_cell.date, entry.to_cell.date),
        finish_date=max(entry.from_cell.date, entry.to_cell.date),
        toasts=toasts,
    )


@router.post("/rota_grid/location/drag_staff", operation_id="moveStaffInLocationGrid")
def move_staff_in_location_grid(
    request: Request, entry: MoveStaffInLocationGrid, connection: Connection
) -> ActivityResponse:
    toasts = []
    try:
        # print(entry)
        if entry.from_activity == entry.to_activity:
            return {"status": "ok"}  ## no need to move anything
        sql_query = """
        SELECT activity_start,location_id
        FROM activities
        WHERE id in (:from_activity_id, :to_activity_id)
        """
        original_activities = connection.execute(
            sql_query,
            {
                "from_activity_id": entry.from_activity,
                "to_activity_id": entry.to_activity,
            },
        ).fetchall()
        # print("ok so far", tuple(original_activities))
        if len(original_activities) != 2:
            raise ReallocationError("Activity not found")
        with connection:
            sql_query = """
            DELETE FROM staff_assignments
            WHERE activity_id = :activity_id AND staff_id = :staff_id
            """
            connection.execute(
                sql_query,
                {
                    "activity_id": entry.from_activity,
                    "staff_id": entry.staffId,
                },
            )
            sql_query = """
            INSERT INTO staff_assignments (activity_id, staff_id)
            VALUES (:activity_id, :staff_id)

            """
            try:
                connection.execute(
                    sql_query,
                    {
                        "activity_id": entry.to_activity,
                        "staff_id": entry.staffId,
                    },
                )
            except IntegrityError:
                raise ReallocationError("Staff already assigned to activity")

    except ReallocationError as e:
        toasts.append(
            Toast(
                kind="error",
                title="Error moving staff",
                description=str(e),
            )
        )
    start1, location_id1 = original_activities[0]
    start2, location_id2 = original_activities[1]
    # print("start1", start1, location_id1)
    # print("start2", start2, location_id2)
    return get_activities_grouped_by_date(
        connection,
        start_date=min(start1, start2),
        finish_date=max(start1, start2),
        toasts=toasts,
    )


class StaffGridCell(BaseModel):
    date: datetime.date
    staff: str | None = None


class MoveActivityInStaffGrid(BaseModel):
    activity_id: str
    from_cell: StaffGridCell
    to_cell: StaffGridCell


@router.post("/rota_grid/staff/drag_activity", operation_id="moveActivityInStaffGrid")
def move_activity_in_staff_grid(
    request: Request, entry: MoveActivityInStaffGrid, connection: Connection
) -> ActivityResponse:
    toasts = []
    with connection:
        try:
            # print(entry)
            if entry.from_cell.date != entry.to_cell.date:
                raise ReallocationError("Cannot move activity to a different date")
            if entry.from_cell.staff == entry.to_cell.staff:
                return {"status": "ok"}  ## no need to move anything
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

            if result is None:
                raise ReallocationError("Activity not found")
            if entry.from_cell.staff is not None and entry.dragEffect == "move":
                sql_query = """
            DELETE FROM staff_assignments
            WHERE activity_id = :activity_id AND staff_id = :staff_id
            """

                connection.execute(
                    sql_query,
                    {
                        "activity_id": entry.activity_id,
                        "staff_id": entry.from_cell.staff,
                    },
                )
            if entry.to_cell.staff is not None:
                sql_query = """
            INSERT INTO staff_assignments (activity_id, staff_id)
            VALUES (:activity_id, :staff_id)

            """
                try:
                    connection.execute(
                        sql_query,
                        {
                            "activity_id": entry.activity_id,
                            "staff_id": entry.to_cell.staff,
                        },
                    )
                except IntegrityError:
                    raise ReallocationError("Staff already assigned to activity")
        except ReallocationError as e:
            toasts.append(
                Toast(
                    kind="error",
                    title="Error moving activity",
                    description=str(e),
                )
            )

        return get_activities_grouped_by_date(
            connection,
            start_date=min(entry.from_cell.date, entry.to_cell.date),
            finish_date=max(entry.from_cell.date, entry.to_cell.date),
            toasts=toasts,
        )


@router.get("/rota_grid/context_menu", operation_id="tableContextMenu")
def table_context_menu(
    request: Request,
    connection: Connection,
    staff: str = None,
    date: str = None,
    location: str = None,
) -> Response:
    activities = get_activities(
        connection, datetime.date.fromisoformat(date), datetime.date.fromisoformat(date)
    )[0]
    activity_form = AddActivityForm(
        data={"staff": staff, "date": date, "location": location}
    )

    activity_form.existing_activity.choices = [
        (activity.activity_id, activity.name) for activity in activities.values()
    ] + [("--new--", "Create new activity")]
    # print("existing activities", activity_form.existing_activity.choices)
    return templates.TemplateResponse(
        "table_context_menu.html.mako",
        {
            "request": request,
            "date": date,
            "staff_id": staff,
            "location": location,
            "activity_form": activity_form,
        },
        media_type="text/vnd.turbo-stream.html",
    )


@router.post("/rota_grid/add_activity", operation_id="addActivity")
async def add_activity(
    request: Request,
    connection: Connection,
) -> Response:
    # print("add_activity", request)
    activity_form = AddActivityForm(await request.form())

    if activity_form.validate():
        # print("form validated")
        form_results = activity_form.data
        match form_results:
            case {
                "existing_activity": "--new--",
                "date": date,
                "staff": staff_id,
                "location": location_id,
            }:
                return RedirectResponse(
                    f"/create_new_activity?date={date}&staff_id={staff_id}&location_id={location_id}",
                    303,
                )

            case {
                "existing_activity": activity_id,
                "location": location_id,
                "date": date,
            } if location_id:
                # print("move activity to new location")
                if location_id == "None":
                    location_id = None
                destination_cell = LocationGridCell(date=date, location=location_id)
                source_cell = LocationGridCell(date=date, location=None)
                return move_activity_in_location_grid(
                    request=request,
                    entry=MoveActivityInLocationGrid(
                        activityId=activity_id,
                        from_cell=source_cell,
                        to_cell=destination_cell,
                    ),
                    connection=connection,
                )
            case {
                "existing_activity": activity_id,
                "staff": staff_id,
                "date": date,
            } if staff_id:
                # print("move activity to new staff")
                destination_cell = StaffGridCell(date=date, staff=staff_id)
                source_cell = StaffGridCell(date=date, staff=None)
                return move_staff_in_location_grid(
                    request=request,
                    entry=MoveActivityInStaffGrid(
                        dragEffect="copy",
                        staffId=staff_id,
                        from_cell=source_cell,
                        to_cell=destination_cell,
                    ),
                    connection=connection,
                )
            case {"action": "existing"}:
                raise ValueError("Do not understand request")
            case {"action": "template", "from_template": template_id}:
                print("todo: create activity from template")

    return HTMLResponse(
        """<turbo-frame id="add-activity-form">
                        Replacement text
                        </turbo-frame>"""
    )
