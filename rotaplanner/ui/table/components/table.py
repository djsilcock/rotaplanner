import datetime

import dominate.tags as tags
from logging import getLogger

from rotaplanner.ui.common_types import Activity, Location, Role, Staff, StaffAssignment
from rotaplanner.database import database_connection
from pydantic import BaseModel, Field

logger = getLogger(__name__)

from .ui import table


def activities_by_location_cell(
    activities: dict[str, Activity],
) -> dict[tuple[str, str], list[str]]:
    activities_by_cell: dict[tuple[str, str], list[str]] = {}
    for activity in sorted(activities.values(), key=lambda a: a.activity_start):
        activity_date = activity.activity_start.isoformat()[:10]
        location_id = activity.location
        activities_by_cell.setdefault((activity_date, location_id), []).append(
            activity.id
        )
    return activities_by_cell


def activities_by_staff_cell(
    activities: dict[str, Activity],
) -> dict[tuple[str, str], list[str]]:
    activities_by_cell: dict[tuple[str, str], list[str]] = {}
    for activity in sorted(activities.values(), key=lambda a: a.activity_start):
        activity_date = activity.activity_start.isoformat()[:10]
        assigned_staff_ids = {
            assn.staff for role in activity.roles for assn in role.assignments
        }
        if not assigned_staff_ids:
            activities_by_cell.setdefault((activity_date, None), []).append(activity.id)
        else:
            for staff_id in assigned_staff_ids:
                activities_by_cell.setdefault((activity_date, staff_id), []).append(
                    activity.id
                )
    return activities_by_cell


class TableState(BaseModel):

    locations: list[Location] = Field(default_factory=list)
    staff: list[Staff] = Field(default_factory=list)
    activities: dict[str, Activity] = Field(default_factory=dict)

    @property
    def dates(self):
        min_date = min(
            (activity.activity_start.date() for activity in self.activities.values()),
            default=datetime.date.today(),
        )
        max_date = max(
            (activity.activity_finish.date() for activity in self.activities.values()),
            default=datetime.date.today(),
        )

        dates = []
        dates = [
            min_date + datetime.timedelta(days=i)
            for i in range((max_date - min_date).days + 1)
        ]
        return dates


def load_table_state() -> TableState:
    with database_connection() as db:
        with db:
            activities: dict[str, Activity] = {}
            staff: dict[str, Staff] = {}
            locations: dict[str, Location] = {}

            staffassignments: dict[str, StaffAssignment] = {}
            roles: dict[str, Role] = {}
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
                    activities.start, 
                    activities.finish,
                    activity_roles.id,
                    activity_roles.name as role_name,
                    staff_assignments.assignment_id, 
                    staff_assignments.staff_id
                FROM activities
                LEFT JOIN activity_roles ON activities.id = activity_roles.activity_id
                LEFT JOIN staff_assignments on activity_roles.id = staff_assignments.role_id"""
            for row in db.execute(activities_sqlquery).fetchall():

                (
                    activities_id,
                    activities_name,
                    locations_id,
                    activities_start,
                    activities_finish,
                    role_id,
                    role_name,
                    staffassignments_id,
                    staffassignments_staff_id,
                ) = row

                if activities_id not in activities:
                    activities[activities_id] = Activity(
                        id=activities_id,
                        name=activities_name,
                        location=locations_id,
                        activity_start=activities_start,
                        activity_finish=activities_finish,
                    )
                activity = activities[activities_id]
                if role_id not in roles:
                    roles[role_id] = Role(id=role_id, name=role_name)
                    activity.roles.append(roles[role_id])
                role = roles[role_id]
                if staffassignments_id is not None:
                    if staffassignments_id not in staffassignments:
                        staffassignments[staffassignments_id] = StaffAssignment(
                            id=staffassignments_id,
                            staff=staffassignments_staff_id,
                            flags=[],
                        )
                    role.assignments.append(staffassignments[staffassignments_id])
    return TableState(
        locations=list(locations.values()),
        staff=list(staff.values()),
        activities=activities,
    )


def render_table(table_type):
    state = load_table_state()
    if table_type == "location":
        cells = activities_by_location_cell(state.activities)
        print("rendering table with activities:", cells)
        return table(state.dates, cells, state.activities, locations=state.locations)
    elif table_type == "staff":
        cells = activities_by_staff_cell(state.activities)
        return table(state.dates, cells, state.activities, staff=state.staff)
    else:
        logger.warning(f"!{table_type}")
