from pydantic import BaseModel
from fastapi.templating import Jinja2Templates

import datetime


from typing import Literal
import dataclasses

from fastapi import APIRouter, Response, Request
from fastapi.responses import HTMLResponse,RedirectResponse

from rotaplanner.database import Connection
from sqlite3 import IntegrityError

router = APIRouter()
templates = Jinja2Templates(directory="rotaplanner/templates")

from wtforms import Form, SelectField, HiddenField,BooleanField,IntegerField,SelectMultipleField,StringField,FieldList,TimeField,FormField
from wtforms.validators import Optional,NumberRange


class ReallocationError(Exception):
    pass


def daterange(start_date, finish_date):
    d = start_date
    while d <= finish_date:
        yield d
        d += datetime.timedelta(days=1)


@dataclasses.dataclass
class Location:
    id: str
    name: str


class Staff:
    id: str
    name: str


@dataclasses.dataclass
class StaffAssignmentDisplay:
    staff_name: str
    staff_id: str
    start_time: int | None = None
    finish_time: int | None = None


@dataclasses.dataclass
class ActivityDisplay:
    activity_id: str
    name: str
    start_time: datetime.datetime
    finish_time: datetime.datetime
    location_id: str
    location_name: str
    staff_assignments: list[StaffAssignmentDisplay]


@dataclasses.dataclass
class ActivityCell:
    date: str
    row: str
    activities: list[ActivityDisplay]

    @property
    def cell_id(self):
        return f"cell-{self.date}-{self.row}"


def get_locations(connection: Connection) -> dict[str, Location]:
    sql_query = """
    SELECT id, name
    FROM locations
    """
    with connection:
        result = connection.execute(sql_query).fetchall()
    return {row[0]: Location(id=str(row[0]), name=row[1]) for row in result}


def get_staff(connection: Connection) -> dict[str, Staff]:
    sql_query = """
    SELECT id, name
    FROM staff
    """
    with connection:
        result = connection.execute(sql_query).fetchall()
    return {row[0]: Staff(id=str(row[0]), name=row[1]) for row in result}


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
                    location_id=str(location_id),
                    location_name=location_name,
                    staff_assignments=[],
                )
                if earliest_date is None or start_time < earliest_date:
                    earliest_date = start_time
                if latest_date is None or finish_time > latest_date:
                    latest_date = finish_time
            if staff_id:
                activities[activity_id].staff_assignments.append(
                    StaffAssignmentDisplay(
                        staff_name=staff_name, staff_id=str(staff_id)
                    )
                )
        return activities, earliest_date or start_date, latest_date or finish_date


def get_activity_cells_by_location(
    connection: Connection,
    start_date: datetime.date = datetime.date(1970, 1, 1),
    finish_date: datetime.date = datetime.date(2100, 1, 1),
    specifically_include=(),
) -> list[ActivityCell]:

    activities, earliest_date, latest_date = get_activities(
        connection, start_date, finish_date
    )

    activity_cells = ActivityCellDict()
    activity_cells._logging = True
    for date, location_id in specifically_include:
        key = (date.isoformat(), location_id)
        activity_cells[key]

    for activity_id, activity in activities.items():
        key = (activity.start_time.date().isoformat(), activity.location_id)
        activity_cells[key].activities.append(activity)
    # print(activity_cells)
    return (activity_cells, earliest_date.date(), latest_date.date())


class ActivityCellDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._logging = False

    def __missing__(self, key):
        (date, row_id) = key
        # if self._logging:
        # print("Creating new cell", key)
        self[key] = ActivityCell(date=date, row=row_id, activities=[])
        return self[key]


def get_activity_cells_by_staff(
    connection: Connection,
    start_date: datetime.date = datetime.date(1970, 1, 1),
    finish_date: datetime.date = datetime.date(2100, 1, 1),
    specifically_include=(),
) -> list[ActivityCell]:

    activities, earliest_date, latest_date = get_activities(
        connection, start_date, finish_date
    )

    activity_cells = ActivityCellDict()
    for date, staff_id in specifically_include:
        key = (date.isoformat(), staff_id)
        activity_cells[key]
    for activity_id, activity in activities.items():
        if len(activity.staff_assignments) == 0:
            # print("No staff assignment for activity", activity_id)
            activity_cells[
                (activity.start_time.date().isoformat(), None)
            ].activities.append(activity)
        for staff_assignment in activity.staff_assignments:
            # print("Staff assignment for activity", activity_id, staff_assignment.staff_id)
            key = (activity.start_time.date().isoformat(), staff_assignment.staff_id)
            activity_cells[key].activities.append(activity)
    return (activity_cells, earliest_date.date(), latest_date.date())


@router.get("/rota_grid/location/grid")
def rota_grid_by_location(request: Request, connection: Connection) -> Response:

    (activity_cells, earliest_date, latest_date) = get_activity_cells_by_location(
        connection
    )
    y_axis = get_locations(connection)
    dates = [
        earliest_date + datetime.timedelta(days=i)
        for i in range((latest_date - earliest_date).days + 1)
    ]
    activity_cells._logging = False
    return templates.TemplateResponse(
        "table.html.j2",
        {
            "request": request,
            "date": datetime.date.today(),
            "dates": [d.isoformat() for d in dates],
            "y_axis": y_axis,
            "activity_cells": activity_cells,
            "grid_type": "location",
        },
    )


@router.get("/rota_grid/staff/grid")
def rota_grid_by_staff(request: Request, connection: Connection) -> Response:

    (activity_cells, earliest_date, latest_date) = get_activity_cells_by_staff(
        connection
    )
    y_axis = get_staff(connection)
    dates = [
        earliest_date + datetime.timedelta(days=i)
        for i in range((latest_date - earliest_date).days + 1)
    ]
    activity_cells._logging = True
    return templates.TemplateResponse(
        "table.html.j2",
        {
            "request": request,
            "date": datetime.date.today(),
            "dates": [d.isoformat for d in dates],
            "y_axis": y_axis,
            "activity_cells": activity_cells,
            "grid_type": "staff",
        },
    )


class LocationGridCell(BaseModel):
    date: datetime.date
    location: str | None = None


class MoveActivityInLocationGrid(BaseModel):

    activityId: str
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
):
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
                "activity_id": entry.activityId,
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
                    "activity_id": entry.activityId,
                },
            )

    except ReallocationError as e:
        return {"toasts": [{"class": "error", "message": str(e)}]}
    activity_cells = get_activity_cells_by_location(
        connection,
        min(entry.from_cell.date, entry.to_cell.date),
        max(entry.from_cell.date, entry.to_cell.date),
        specifically_include=[
            (entry.from_cell.date, original_location),
            (entry.to_cell.date, entry.to_cell.location),
        ],
    )[0]
    return templates.TemplateResponse(
        "table_cells.html.j2",
        {
            "replacement_cells": activity_cells.values(),
            "grid_type": "location",
            "request": request,
            "toasts": [
                {
                    "class": "success",
                    "message": f"Move successful",
                }
            ],
        },
        media_type="text/vnd.turbo-stream.html",
    )


@router.post("/rota_grid/location/drag_staff", operation_id="moveStaffInLocationGrid")
def move_staff_in_location_grid(
    request: Request, entry: MoveStaffInLocationGrid, connection: Connection
):
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
        return {"toasts": [{"class": "error", "message": str(e)}]}
    start1, location_id1 = original_activities[0]
    start2, location_id2 = original_activities[1]
    # print("start1", start1, location_id1)
    # print("start2", start2, location_id2)
    activity_cells = get_activity_cells_by_location(
        connection,
        min(start1, start2),
        max(start1, start2),
        specifically_include=[(start1, location_id1), (start2, location_id2)],
    )[0]

    return templates.TemplateResponse(
        "table_cells.html.j2",
        {
            "replacement_cells": activity_cells.values(),
            "request": request,
            "grid_type": "location",
            "toasts": [
                {
                    "class": "success",
                    "message": f"Move successful",
                }
            ],
        },
        media_type="text/vnd.turbo-stream.html",
    )


class StaffGridCell(BaseModel):
    date: datetime.date
    staff: str | None = None


class MoveActivityInStaffGrid(BaseModel):
    dragEffect: Literal["move", "copy"]
    activityId: str
    from_cell: StaffGridCell
    to_cell: StaffGridCell


@router.post("/rota_grid/staff/drag_activity", operation_id="moveActivityInStaffGrid")
def move_activity_in_staff_grid(
    request: Request, entry: MoveActivityInStaffGrid, connection: Connection
):
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
                        "activity_id": entry.activityId,
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
                            "activity_id": entry.activityId,
                            "staff_id": entry.to_cell.staff,
                        },
                    )
                except IntegrityError:
                    raise ReallocationError("Staff already assigned to activity")
        except ReallocationError as e:
            return {"toasts": [{"class": "error", "message": str(e)}]}
        activity_cells = get_activity_cells_by_staff(
            connection,
            entry.to_cell.date,
            entry.to_cell.date,
            specifically_include=[
                (entry.to_cell.date, entry.to_cell.staff),
                (entry.from_cell.date, entry.from_cell.staff),
            ],
        )[0]
        return templates.TemplateResponse(
            "table_cells.html.j2",
            {
                "replacement_cells": activity_cells.values(),
                "grid_type": "staff",
                "request": request,
                "toasts": [
                    {
                        "class": "success",
                        "message": f"Move successful",
                    }
                ],
            },
            media_type="text/vnd.turbo-stream.html",
        )


class AddActivityForm(Form):
    existing_activity = SelectField("Existing Activity", validate_choice=False)
    from_template = SelectField("Create from Template", validate_choice=False)
    action = SelectField("", choices=["existing", "template", "new"])
    staff = HiddenField("staff")
    date = HiddenField("date")
    location = HiddenField("location")


@router.get("/rota_grid/add_activity", operation_id="addActivity")
def add_activity_dialog(
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
    print(request.headers)
    activity_form.existing_activity.choices = [
        (activity.activity_id, activity.name) for activity in activities.values()
    ]
    # print("existing activities", activity_form.existing_activity.choices)
    return templates.TemplateResponse(
        "new_activity_dialog.html.j2",
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
                "action": "existing",
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
                "action": "existing",
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
            case {
                "action": "new",
                "date": date,
                "staff": staff_id,
            } if staff_id:
                return RedirectResponse(f'/create_new_activity?date={date}&staff_id={staff_id}',303)
            case {
                "action": "new",
                "date": date,
                "location": location_id
            } if location_id:
                return RedirectResponse(f'/create_new_activity?date={date}&location_id={location_id}',303)

    return HTMLResponse(
        """<turbo-frame id="add-activity-form">
                        Replacement text
                        </turbo-frame>"""
    )
class RequirementForm(Form):
    
    skills = SelectMultipleField(
        "Skills", choices=()
    )
    requirement = IntegerField(
        "Required people", default=1, validators=[NumberRange(min=0)]
    )
    optional = IntegerField(
        "Optional additional people", default=0, validators=[NumberRange(min=0)]
    )
    attendance = IntegerField(
        "Attendance",
        default=100,
        validators=[NumberRange(0, 100)],
        description="Will usually be 100%",
    )
    geofence = SelectField(
        "Geofence (if attendance not 100%)",
        default="_immediate",
        choices=[
            ("_immediate", "Local location"),
            ("main", "Main theatre"),
            ("dsu", "Day surgery"),
            ("hosp", "Whole hospital"),
            ("remote", "Remote"),
        ],
    )

    is_deleted = BooleanField("Delete requirement")
    is_open = BooleanField(render_kw={"class": "is-open"})

class EditActivityForm(Form):
    activity_id=HiddenField()
    name = StringField("Activity Name")
    activity_tags = SelectMultipleField(
        "Tags"
    )
    start_time = TimeField("Start time")
    finish_time = TimeField("Finish Time")
    duration = TimeField("Duration")
    location = SelectField(choices=())
    requirements = FieldList(FormField(RequirementForm))


@router.get("/create_new_activity")
def create_new_activity(request:Request,staff_id=None,location_id=None,date=None):
    form=EditActivityForm()
    return templates.TemplateResponse('edit_activity_template.html.j2',{'form':form,'request':request}
    )
