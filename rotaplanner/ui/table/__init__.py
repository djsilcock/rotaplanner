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
import jsonpatch
import datetime
from typing import cast
from sqlite3 import Connection
from collections import OrderedDict
from uuid import uuid4, UUID
from rotaplanner.typedefs import (
    StaffAssignment,
    Location,
    Staff,
    ActivityTag,
    Activity,
    TimeSlot,
)

table_blueprint = Blueprint(
    "table", __name__, template_folder="templates", url_prefix="/api/table"
)

location_query_cache = OrderedDict()
latest_location_query = None
staff_query_cache = OrderedDict()
latest_staff_query = None
latest_queries = {"location": None, "staff": None}


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

    return await table_by_location(force_refresh=True)


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

    return await table_by_staff(force_refresh=True)


def serialise_activity(activity: Activity):
    return {
        "id": activity.id,
        "name": activity.name,
        "activity_start": activity.activity_start.hour,
        "activity_finish": activity.activity_finish.hour,
        "location": activity.location.id if activity.location else None,
        "timeslots": [
            {
                "id": timeslot.id,
                "start": timeslot.start.hour,
                "finish": timeslot.finish.hour,
                "assignments": [
                    {
                        "id": assignment.id,
                        "staff": {
                            "id": assignment.staff.id,
                            "name": assignment.staff.name,
                        },
                    }
                    for assignment in timeslot.assignments
                ],
            }
            for timeslot in activity.timeslots
        ],
    }


def serialise_result(table_query_result):
    return {
        "dates": [date.isoformat() for date in table_query_result["dates"]],
        "staff": {
            str(staff_id): {"id": staff.id, "name": staff.name}
            for staff_id, staff in table_query_result["staff"].items()
        },
        "locations": {
            str(location_id): {"id": location.id, "name": location.name}
            for location_id, location in table_query_result["locations"].items()
        },
        "cells": {
            f"{str(row_id)}-{date.isoformat()}": content
            for (row_id, date), content in table_query_result["cells"].items()
        },
        "activities": {
            str(activity_id): serialise_activity(activity)
            for activity_id, activity in table_query_result["activities"].items()
        },
    }


@table_blueprint.get("/by_staff")
async def table_by_staff(force_refresh=True):
    if (
        old_query_result := staff_query_cache.get(latest_queries["staff"]) is None
        or force_refresh
    ):
        result = await get_staff_query()

        latest_queries["staff"] = str(uuid4())
        staff_query_cache[latest_queries["staff"]] = {
            "queryVersion": latest_queries["staff"],
            "rowHeaders": list(result["staff"].keys()),
            **serialise_result(result),
        }
    return staff_query_cache.get(latest_queries["staff"])


@table_blueprint.get("/by_location")
async def table_by_location(force_refresh=True):
    if (
        old_query_result := location_query_cache.get(latest_queries["location"]) is None
        or force_refresh
    ):
        result = await get_location_query()

        latest_queries["location"] = str(uuid4())
        location_query_cache[latest_queries["location"]] = {
            "queryVersion": latest_queries["location"],
            "rowHeaders": list(result["locations"].keys()),
            **serialise_result(result),
        }
    return location_query_cache.get(latest_queries["location"])


async def get_core_query():
    db = cast(Connection, current_app.db_connection)
    with db:
        activities: dict[str, Activity] = {}
        staff: dict[str, Staff] = {}
        locations = {}
        timeslots: dict[str, TimeSlot] = {}
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
                    type="",
                    template_id=None,
                    location=locations.get(locations_id),
                )
            activity = activities[activities_id]
            if timeslots_id not in timeslots:
                timeslots[timeslots_id] = TimeSlot(
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
                    staff=staff[staffassignments_staff_id],
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

    dates = [
        (min_date + datetime.timedelta(days=i))
        for i in range(max((max_date - min_date).days + 1, 30))
    ]

    location_cells = {}
    for activity_id, activity in activities.items():
        cell = location_cells.setdefault(
            (
                activity.location.id if activity.location else None,
                activity.activity_start.date(),
            ),
            [],
        )
        cell.append(activity_id)

    staff_cells = {}
    for activity in activities.values():
        target_cells = set()
        for timeslot in activity.timeslots:
            for assignment in timeslot.assignments:
                target_cells.add((assignment.staff.id, timeslot.start.date()))
            if not timeslot.assignments:
                target_cells.add((None, timeslot.start.date()))
        for cell_id in target_cells:
            cell = staff_cells.setdefault(
                cell_id,
                [],
            )
            cell.append(activity.id)
    return dates, locations, activities, staff, location_cells, staff_cells


async def get_location_query():
    core_query_result = await get_core_query()
    dates, locations, activities, staff, location_cells, staff_cells = core_query_result

    table_query_result = {
        "dates": dates,
        "locations": locations,
        "cells": location_cells,
        "activities": activities,
        "staff": staff,
    }
    return table_query_result


async def get_staff_query():
    core_query_result = await get_core_query()
    dates, locations, activities, staff, location_cells, staff_cells = core_query_result
    table_query_result = {
        "dates": dates,
        "staff": staff,
        "cells": staff_cells,
        "activities": activities,
        "locations": locations,
    }
    return table_query_result
