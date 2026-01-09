from datastar_py import ServerSentEventGenerator
from datastar_py.quart import DatastarResponse, read_signals
from quart import (
    Blueprint,
    render_template,
    current_app,
    request,
    get_template_attribute,
)
import datetime
from typing import cast
from sqlite3 import Connection
from new_rotaplanner.types import (
    StaffAssignment,
    Location,
    Staff,
    ActivityTag,
    Activity,
    TimeSlot,
)

table_blueprint = Blueprint(
    "table", __name__, template_folder="templates", url_prefix="/table"
)


@table_blueprint.get("/by_staff")
async def table_by_staff():
    return "todo"


@table_blueprint.post("/by_location")
async def update_location():
    payload = await read_signals()
    print(payload)
    match payload:
        case {
            "draggedId": dragged_id,
            "droptargetId": droptarget_id,
            "initialDropzoneId": initial_dropzone_id,
        }:
            draginfo = tuple(dragged_id.split("--"))
            dropinfo = tuple(droptarget_id.split("--"))
            initial_info = tuple(initial_dropzone_id.split("--"))
            if initial_info[0] != dropinfo[0]:
                raise ValueError("incompatible drop types")
            if draginfo[0] == "act" and dropinfo[0] == "cell":
                db = cast(Connection, current_app.db_connection)
                date1 = datetime.date.fromisoformat(initial_info[2])
                date2 = datetime.date.fromisoformat(dropinfo[2])
                date_delta = (date2 - date1).days
                with db:
                    timeslot_ids_sqlquery = """UPDATE timeslots SET start=DATETIME(start,:delta), finish=DATETIME(finish,:delta) WHERE activity_id = :id"""
                    db.execute(
                        timeslot_ids_sqlquery,
                        {"id": draginfo[1], "delta": f"{date_delta} DAYS"},
                    )

                    update_sqlquery = (
                        """UPDATE activities SET location_id = ? WHERE id = ?"""
                    )
                    db.execute(
                        update_sqlquery,
                        (dropinfo[1] if dropinfo[1] != "None" else None, draginfo[1]),
                    )
                    affected_cells = [(initial_info[1], date1), (dropinfo[1], date2)]
                    table_query_result = await get_location_query()
                    response = []
                    for location_id, date in affected_cells:
                        cell_activities = table_query_result["cells"].get(
                            (
                                None if location_id == "None" else location_id,
                                date,
                            ),
                            [],
                        )
                        response.append(
                            await render_template(
                                "cell.html.j2",
                                row={"row_id": location_id},
                                date=date,
                                cell=cell_activities,
                            )
                        )

                    async def update_cells():
                        for r in response:
                            yield ServerSentEventGenerator.patch_elements(r)

                    return DatastarResponse(update_cells())
    raise ValueError("Invalid payload")


@table_blueprint.get("/by_location")
async def table_by_location():
    table_query_result = await get_location_query()
    return await render_template(
        "table.html.j2",
        dates=table_query_result["dates"],
        table_query_result=table_query_result,
    )


async def get_location_query():
    db = cast(Connection, current_app.db_connection)
    with db:
        activities: dict[str, Activity] = {}
        staff = {}
        locations = {None: Location(id=None, name="Unassigned")}
        timeslots = {}
        staffassignments = {}
        locations_sqlquery = """SELECT id, name FROM locations"""
        for row in db.execute(locations_sqlquery).fetchall():
            locations[row["id"]] = Location(id=row["id"], name=row["name"])
        staff_sqlquery = """SELECT id, name FROM staff"""
        for row in db.execute(staff_sqlquery).fetchall():
            staff[row["id"]] = Staff(id=row["id"], name=row["name"])
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
            print(dict(row))
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
    cells = {}
    for activity in activities.values():
        cell = cells.setdefault(
            (
                activity.location.id if activity.location else None,
                activity.activity_start.date(),
            ),
            [],
        )
        cell.append(activity)
    table_query_result = {
        "dates": dates,
        "locations": locations,
        "cells": cells,
        "rows": [
            {
                "row_id": location.id,
                "row_name": location.name,
                "data": {date: cells.get((location.id, date), []) for date in dates},
            }
            for location in locations.values()
        ],
    }
    return table_query_result
