from datastar_py import ServerSentEventGenerator
from datastar_py.quart import DatastarResponse, read_signals
import sqlite3
from quart import (
    Blueprint,
    render_template,
    current_app,
    request,
    get_template_attribute,
)
from quart_schema import validate_request, validate_response
import jsonpatch
import datetime
from typing import cast
from sqlite3 import Connection
from collections import OrderedDict
from uuid import uuid4, UUID


from pydantic import BaseModel, Field, computed_field

table_blueprint = Blueprint(
    "table", __name__, template_folder="templates", url_prefix="/api/table"
)


class Location(BaseModel):
    id: str | None
    name: str


class Staff(BaseModel):
    id: str | None
    name: str


class StaffAssignment(BaseModel):
    id: int
    staff: str


class Timeslot(BaseModel):
    id: int
    start: datetime.datetime
    finish: datetime.datetime
    assignments: list[StaffAssignment] = Field(default_factory=list)


class Activity(BaseModel):
    id: str
    name: str

    @computed_field
    @property
    def activity_start(self) -> datetime.datetime:
        return min(t.start for t in self.timeslots)

    @computed_field
    @property
    def activity_finish(self) -> datetime.datetime:
        return max(t.finish for t in self.timeslots)

    location: str | None
    timeslots: list[Timeslot] = Field(default_factory=list)


class DateRange(BaseModel):
    start: datetime.date
    end: datetime.date


class TableDataResult(BaseModel):
    queryVersion: UUID = Field(default_factory=uuid4)
    dateRange: DateRange
    staff: list[str]
    locations: list[str]
    staffData: dict[str | None, Staff]
    locationsData: dict[str | None, Location]
    activities: dict[str, Activity]


class QueryCache:
    def __init__(self):
        self.cache = OrderedDict()
        self.latest_query_id = None

    def get(self, query_id) -> TableDataResult | None:
        return self.cache.get(query_id)

    def set(self, result: TableDataResult):
        query_key = result.queryVersion
        self.latest_query_id = query_key
        self.cache[query_key] = result

    def get_latest(self):
        if self.latest_query_id:
            return self.cache.get(self.latest_query_id)
        return None

    def get_delta(self, old_query_id):
        if old_query_id and old_query_id in self.cache:
            old_result = self.cache.get(old_query_id)
            if old_result is None:
                old_result = {}
            else:
                old_result = old_result.model_dump()
            new_result = self.get_latest()
            if new_result:

                patch = jsonpatch.JsonPatch.from_diff(
                    old_result, new_result.model_dump()
                )
                return {
                    "queryVersion": new_result.queryVersion,
                    "delta": patch.to_string(),
                }
        return None


query_cache = QueryCache()


def valid_uuid_or_none(value):
    try:
        return str(UUID(value))

    except (ValueError, TypeError):
        return None


@table_blueprint.post("/by_location")
async def update_location():
    payload = await request.get_json()
    print(payload)
    match payload:
        case {
            "draggedId": dragged_id,
            "droptargetId": droptarget_id,
            "initialDropzoneId": initial_dropzone_id,
        }:
            pass
        case _:
            raise ValueError("did not understand instruction")
    draginfo = tuple(dragged_id.split("--"))
    dropinfo = tuple(droptarget_id.split("--"))
    initial_info = tuple(initial_dropzone_id.split("--"))
    affected_cells = []
    db = cast(Connection, current_app.db_connection)
    try:
        match (draginfo, initial_info, dropinfo):
            case (
                ("act", activity_id),
                ("cell", from_location, from_date),
                ("cell", to_location, to_date),
            ):
                date1 = datetime.date.fromisoformat(from_date)
                date2 = datetime.date.fromisoformat(to_date)
                date_delta = (date2 - date1).days
                from_location = valid_uuid_or_none(from_location)
                to_location = valid_uuid_or_none(to_location)
                with db:
                    timeslot_ids_sqlquery = """UPDATE timeslots SET start=DATETIME(start,:delta), finish=DATETIME(finish,:delta) WHERE activity_id = :id"""
                    db.execute(
                        timeslot_ids_sqlquery,
                        {"id": activity_id, "delta": f"{date_delta} DAYS"},
                    )

                    update_sqlquery = (
                        """UPDATE activities SET location_id = ? WHERE id = ?"""
                    )
                    db.execute(
                        update_sqlquery,
                        (valid_uuid_or_none(to_location), activity_id),
                    )
                    affected_cells = [(from_location, date1), (to_location, date2)]
            case (
                ("assn", assn_id, staff_id),
                ("timeslot", from_timeslot_id),
                ("timeslot", to_timeslot_id),
            ):
                with db:
                    affected = db.execute(
                        """SELECT activities.location_id,DATE(MIN(timeslots.start)) from timeslots 
                        LEFT JOIN activities ON timeslots.activity_id=activities.id
                        WHERE timeslots.id IN (:from_timeslot,:to_timeslot)
                        GROUP BY activities.id
                        """,
                        {
                            "from_timeslot": from_timeslot_id,
                            "to_timeslot": to_timeslot_id,
                        },
                    )
                    print([tuple(a) for a in affected.fetchall()])
                    db.execute(
                        "UPDATE staff_assignments SET timeslot_id=:new_timeslot_id WHERE assignment_id=:assn_id",
                        ({"assn_id": assn_id, "new_timeslot_id": to_timeslot_id}),
                    )
    except sqlite3.IntegrityError as e:
        print("Integrity error:", e)
        affected_cells = []

    return await table_data(force_refresh=True)


@table_blueprint.post("/by_staff")
async def update_staff():
    payload = await request.get_json()
    print(payload)
    match payload:
        case {
            "draggedId": dragged_id,
            "droptargetId": droptarget_id,
            "initialDropzoneId": initial_dropzone_id,
            "ctrlKey": should_copy,
        }:
            pass
        case _:
            raise ValueError("did not understand instruction")
    draginfo = tuple(dragged_id.split("--"))
    dropinfo = tuple(droptarget_id.split("--"))
    initial_info = tuple(initial_dropzone_id.split("--"))
    affected_cells = []
    if dropinfo != initial_info:
        db = cast(Connection, current_app.db_connection)
        try:

            def move_timeslot_assignment(from_staff_id, to_staff_id, timeslot_id):
                from_staff_id = valid_uuid_or_none(from_staff_id)
                to_staff_id = valid_uuid_or_none(to_staff_id)
                print(
                    f"moving assignment of timeslot {timeslot_id} from staff {from_staff_id} to staff {to_staff_id}"
                )
                if from_staff_id is not None and to_staff_id is not None:
                    db.execute(
                        "UPDATE OR IGNORE staff_assignments SET staff_id=:new_staff_id WHERE staff_id=:old_staff_id AND timeslot_id =:timeslot_id",
                        (
                            {
                                "timeslot_id": timeslot_id,
                                "new_staff_id": to_staff_id,
                                "old_staff_id": from_staff_id,
                            }
                        ),
                    )
                elif from_staff_id is None:
                    db.execute(
                        "INSERT OR IGNORE INTO staff_assignments (staff_id, timeslot_id) VALUES (:new_staff_id, :timeslot_id)",
                        {
                            "timeslot_id": timeslot_id,
                            "new_staff_id": to_staff_id,
                        },
                    )
                elif to_staff_id is None:
                    db.execute(
                        "DELETE FROM staff_assignments WHERE staff_id=:old_staff_id AND timeslot_id =:timeslot_id",
                        {
                            "timeslot_id": timeslot_id,
                            "old_staff_id": from_staff_id,
                        },
                    )

            match (draginfo, initial_info, dropinfo):
                case (
                    ("timeslot", timeslot_id),
                    ("cell", from_staff_id, from_date),
                    ("cell", to_staff_id, to_date),
                ):
                    with db:
                        if should_copy:
                            from_staff_id = None

                        move_timeslot_assignment(
                            from_staff_id, to_staff_id, timeslot_id
                        )

                case (
                    ("act", activity_id),
                    ("cell", from_staff_id, from_date),
                    ("cell", to_staff_id, to_date),
                ):
                    from_staff_id = valid_uuid_or_none(from_staff_id)
                    to_staff_id = valid_uuid_or_none(to_staff_id)
                    if should_copy:
                        from_staff_id = None
                    with db:

                        if from_staff_id is None:
                            timeslot_ids = db.execute(
                                """SELECT id FROM timeslots WHERE activity_id=:activity_id""",
                                {
                                    "activity_id": activity_id,
                                },
                            ).fetchall()
                        else:
                            timeslot_ids = db.execute(
                                """SELECT timeslots.id FROM timeslots 
                                LEFT JOIN staff_assignments ON timeslots.id=staff_assignments.timeslot_id
                                WHERE timeslots.activity_id=:activity_id AND staff_assignments.staff_id=:from_staff_id""",
                                {
                                    "activity_id": activity_id,
                                    "from_staff_id": from_staff_id,
                                },
                            ).fetchall()
                        for (timeslot_id,) in timeslot_ids:
                            move_timeslot_assignment(
                                from_staff_id, to_staff_id, timeslot_id
                            )

                case _:
                    print("unhandled case")
                    print(draginfo, initial_info, dropinfo)
        except sqlite3.IntegrityError as e:
            print("Integrity error:", e)

    return await table_data(force_refresh=True)


@table_blueprint.get("/data")
@validate_response(TableDataResult)
async def table_data(force_refresh=True):
    if old_query_result := query_cache.get_latest() is None or force_refresh:
        dates, locations, activities, staff = await get_core_query()

        query_cache.set(
            TableDataResult(
                dateRange=(
                    DateRange(start=dates[0], end=dates[1])
                    if dates
                    else DateRange(
                        start=datetime.date.today(), end=datetime.date.today()
                    )
                ),
                staff=[l for l in staff.keys() if l is not None],
                locations=[l for l in locations.keys() if l is not None],
                staffData=staff,
                locationsData=locations,
                activities=activities,
            )
        )
    response = query_cache.get_latest()
    print(response)
    return response


async def get_core_query():
    db = cast(Connection, current_app.db_connection)
    with db:
        activities: dict[str, Activity] = {}
        staff: dict[str, Staff] = {}
        locations: dict[str, Location] = {}
        timeslots: dict[str, Timeslot] = {}
        staffassignments: dict[str, StaffAssignment] = {}
        locations_sqlquery = """SELECT id, name FROM locations"""
        for row in db.execute(locations_sqlquery).fetchall():
            locations[row["id"]] = Location(id=row["id"], name=row["name"])
        locations[None] = Location(id=None, name="No Location")

        staff_sqlquery = """SELECT id, name FROM staff"""
        for row in db.execute(staff_sqlquery).fetchall():
            staff[row["id"]] = Staff(id=row["id"], name=row["name"])
        staff[None] = Staff(id=None, name="Unassigned")
        activities_sqlquery = """
            SELECT 
                activities.id, 
                activities.name, 
                location_id, 
                timeslots.id,
                timeslots.start, 
                timeslots.finish, 
                staff_assignments.assignment_id, 
                staff_assignments.staff_id
            FROM activities
            LEFT JOIN timeslots on activities.id = timeslots.activity_id
            LEFT JOIN staff_assignments on timeslots.id = staff_assignments.timeslot_id"""
        for row in db.execute(activities_sqlquery).fetchall():

            (
                activities_id,
                activities_name,
                locations_id,
                timeslots_id,
                timeslots_start,
                timeslots_finish,
                staffassignments_id,
                staffassignments_staff_id,
            ) = row

            if activities_id not in activities:
                activities[activities_id] = Activity(
                    id=activities_id,
                    name=activities_name,
                    location=locations_id,
                )
            activity = activities[activities_id]
            if timeslots_id not in timeslots:
                timeslots[timeslots_id] = Timeslot(
                    id=timeslots_id,
                    activity=activity,
                    start=timeslots_start,
                    finish=timeslots_finish,
                )
                activity.timeslots.append(timeslots[timeslots_id])
            timeslot = timeslots[timeslots_id]
            if (
                staffassignments_id is not None
                and staffassignments_id not in staffassignments
            ):
                staffassignments[staffassignments_id] = StaffAssignment(
                    id=staffassignments_id,
                    staff=staffassignments_staff_id,
                    timeslot=timeslot,
                    flags=[],
                )
                timeslot.assignments.append(staffassignments[staffassignments_id])
    min_date = min(
        (ts.start.date() for ts in timeslots.values()), default=datetime.date.today()
    )
    max_date = max(
        (ts.finish.date() for ts in timeslots.values()), default=datetime.date.today()
    )

    dates = (min_date, max_date)

    return dates, locations, activities, staff
