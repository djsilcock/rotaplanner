import datetime
from typing import Awaitable, Callable, Self

import dominate.tags as tags
from logging import getLogger

from .types import Activity, Location, Role, Staff, StaffAssignment
from rotaplanner.database import database_connection, database_version
from pydantic import BaseModel, Field
import inspect

logger = getLogger(__name__)

from .ui import table
import asyncio
import weakref
import reaktiv

__all__ = ["locations", "staff", "activities", "dates"]


@reaktiv.Computed
def locations() -> list[Location]:
    logger.info("Loading locations from database")
    database_version.get()  # Establish dependency on database_version signal for cache invalidation
    with database_connection() as db:
        locations = []
        for row in db.execute("""SELECT id, name FROM locations""").fetchall():
            locations.append(Location(id=row["id"], name=row["name"]))
        return locations


@reaktiv.Computed
def staff() -> list[Staff]:
    logger.info("Loading staff from database")
    database_version.get()  # Establish dependency on database_version signal for cache invalidation
    with database_connection() as db:
        staff = []
        for row in db.execute("""SELECT id, name FROM staff""").fetchall():
            staff.append(Staff(id=row["id"], name=row["name"]))
        return staff


@reaktiv.Computed
def activities() -> dict[str, Activity]:
    logger.info("Loading activities from database")
    database_version.get()  # Establish dependency on database_version signal for cache invalidation
    staff_dict = {s.id: s for s in staff()}
    with database_connection() as db:
        activities: dict[str, Activity] = {}
        staffassignments: dict[str, StaffAssignment] = {}
        roles: dict[str, Role] = {}
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
            
            LEFT JOIN staff_assignments on activities.id = staff_assignments.activity_id
            LEFT JOIN activity_roles ON activity_roles.id = staff_assignments.role_id"""
        for row in db.execute(activities_sqlquery).fetchall():
            try:

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
                if role_id is not None:
                    if role_id not in roles:
                        roles[role_id] = Role(id=role_id, name=role_name)
                        activity.roles.append(roles[role_id])
                    role = roles[role_id]
                else:
                    role = None
                if staffassignments_id is not None:
                    if staffassignments_id not in staffassignments:
                        staffassignments[staffassignments_id] = StaffAssignment(
                            id=staffassignments_id,
                            staff=staff_dict.get(staffassignments_staff_id),
                            flags=[],
                            role=role,
                        )
                    activity.assignments.append(staffassignments[staffassignments_id])
            except Exception as e:
                logger.error(f"Error processing row {tuple(row)}: {e}")
                raise e
        return activities


@reaktiv.Computed
def dates() -> list[datetime.date]:
    logger.info("Calculating dates from activities")
    min_date = min(
        (activity.activity_start.date() for activity in (activities.get()).values()),
        default=datetime.date.today(),
    )
    max_date = max(
        (activity.activity_finish.date() for activity in (activities.get()).values()),
        default=datetime.date.today(),
    )

    dates = []
    dates = [
        min_date + datetime.timedelta(days=i)
        for i in range((max_date - min_date).days + 1)
    ]
    return dates
