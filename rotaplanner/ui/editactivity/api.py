import datetime
import sqlite3
from collections import ChainMap
from logging import getLogger
from uuid import UUID, uuid4

import webview
from pydantic import BaseModel, Field

from old_rotaplanner.models import RequirementGroup
from rotaplanner.apigen import JSApi, generate_typescript
from rotaplanner.database import database_connection

from ...signals import activity_updated
from ..common_types import (
    Activity,
    Location,
    Staff,
    StaffAssignment,
    Timeslot,
    Requirement,
    Role,
)

logger = getLogger(__name__)


def valid_uuid_or_none(value):
    try:
        return str(UUID(value))

    except (ValueError, TypeError):
        return None


class AvailableForTimeslotQuery(BaseModel):
    activity_id: UUID


class AvailableForTimeslotResult(BaseModel):
    staff: Staff
    availability_type: list[str]
    existing_activity: str | None = None


class EditActivityApi(JSApi):
    _window: webview.Window = None

    def get_activity(self, activity_id: str) -> Activity:
        with database_connection() as db:
            activities_sqlquery = """
                SELECT 
                    activities.id, 
                    activities.name, 
                    activities.location_id, 
                    activities.start, 
                    activities.finish, 
                    staff_assignments.assignment_id, 
                    staff_assignments.staff_id,
                    activity_roles.id as role_id,
                    activity_roles.name as role_name,
                    requirement_groups.id as requirement_group_id,
                    requirement_groups.parent_group_id as requirement_group_parent_id,
                    requirement_groups.activity_id as requirement_group_activity_id,
                    requirement_groups.group_type as requirement_group_type,

                    requirements.id as requirement_id,
                    requirements.min_required,
                    requirements.max_required

                FROM activities
                LEFT JOIN staff_assignments on activities.id = staff_assignments.activity_id
                LEFT JOIN activity_roles ON staff_assignments.role_id = activity_roles.id
                LEFT JOIN requirement_groups ON activities.id = requirement_groups.activity_id
                LEFT JOIN requirements ON requirement_groups.id = requirements.group_id
                WHERE activities.id = :activity_id"""
            activity: dict[str, Activity] = None
            staffassignments: dict[str, StaffAssignment] = {}
            roles: dict[str, Role] = {}
            requirement_groups: dict[str, RequirementGroup] = {}
            requirements: dict[str, Requirement] = {}
            lazy_associations: list[tuple[dict, str, str, object]] = (
                []
            )  # (dict to update, key of object, attribute to append to,object to append)
            for row in db.execute(
                activities_sqlquery, {"activity_id": activity_id}
            ).fetchall():

                (
                    activities_id,
                    activities_name,
                    locations_id,
                    activities_start,
                    activities_finish,
                    staffassignments_id,
                    staffassignments_staff_id,
                    role_id,
                    role_name,
                    requirement_group_id,
                    requirement_group_parent_id,
                    requirement_group_activity_id,
                    requirement_group_type,
                    requirement_id,
                    requirements_min_required,
                    requirements_max_required,
                ) = row

                if activity is None:
                    activity = Activity(
                        id=activities_id,
                        name=activities_name,
                        location=locations_id,
                        activity_start=activities_start,
                        activity_finish=activities_finish,
                    )
                if role_id is not None and role_id not in roles:
                    roles[role_id] = Role(
                        id=role_id, name=role_name, assignments=[], requirements=[]
                    )
                    lazy_associations.append((None, None, "roles", roles[role_id]))

                if (
                    requirement_group_id is not None
                    and requirement_group_id not in requirement_groups
                ):
                    requirement_groups[requirement_group_id] = RequirementGroup(
                        id=requirement_group_id,
                        parent_group_id=requirement_group_parent_id,
                        group_type=requirement_group_type,
                    )
                    if requirement_group_parent_id is not None:
                        lazy_associations.append(
                            (
                                requirement_groups,
                                requirement_group_parent_id,
                                "child_groups",
                                requirement_groups[requirement_group_id],
                            )
                        )
                    elif requirement_group_activity_id is not None:
                        lazy_associations.append(
                            (
                                None,
                                None,
                                "append",
                                requirement_groups[requirement_group_id],
                            )
                        )
                    else:
                        logger.warning(
                            f"Requirement group {requirement_group_id} is not associated with either an activity or a parent requirement group"
                        )

                if (
                    staffassignments_id is not None
                    and staffassignments_id not in staffassignments
                ):
                    staffassignments[staffassignments_id] = StaffAssignment(
                        id=staffassignments_id,
                        staff=staffassignments_staff_id,
                        flags=[],
                    )
                    lazy_associations.append(
                        (
                            roles,
                            role_id,
                            "assignments",
                            staffassignments[staffassignments_id],
                        )
                    )

                if requirement_id is not None and requirement_id not in requirements:
                    requirement = Requirement(
                        id=requirement_id,
                        quantity=requirements_min_required,
                        minimum_required=requirements_min_required,
                        maximum_allowed=requirements_max_required,
                        skills=[],
                    )
                    requirements[requirement_id] = requirement
                    if requirement_group_id is not None:
                        lazy_associations.append(
                            (
                                requirement_groups,
                                requirement_group_id,
                                "requirements",
                                requirement,
                            )
                        )

                    else:
                        logger.warning(
                            f"Requirement {requirement_id} is not associated with a requirement group"
                        )
            for dict_to_update, key, attribute, object_to_append in lazy_associations:
                logger.debug(
                    f"Associating {object_to_append} to {attribute} of {key} in {dict_to_update}"
                )
                object_to_update = (
                    activity if dict_to_update is None else dict_to_update[key]
                )
                getattr(object_to_update, attribute).append(object_to_append)
            return activity

    def available_for_timeslot(
        self, query_args: AvailableForTimeslotQuery
    ) -> list[AvailableForTimeslotResult]:
        with database_connection() as db:
            with db:
                activity_id = query_args.activity_id
                availability_sqlquery = """
                WITH relevant_assignments AS (
                    SELECT activities.id as activity_id, activities.name as activity_name, staff_assignments.staff_id as staff_assignment_id FROM activities
                    LEFT JOIN staff_assignments ON activities.id = staff_assignments.activity_id
                    WHERE start < (SELECT finish FROM activities WHERE id = :activity_id)
                    AND finish > (SELECT start FROM activities WHERE id = :activity_id)
                    AND activities.id != :activity_id
                )
                SELECT
                    staff.id, 
                    staff.name,
                    relevant_assignments.activity_id,
                    relevant_assignments.activity_name as relevant_activity_name
                    
                FROM staff
                LEFT JOIN relevant_assignments ON staff.id = relevant_assignments.staff_assignment_id
                
                
                
            """
                availability = []
                for row in db.execute(
                    availability_sqlquery, {"activity_id": activity_id}
                ).fetchall():
                    staff_id, staff_name, activity_id, relevant_activity_name = row
                    availability.append(
                        AvailableForTimeslotResult(
                            staff=Staff(id=staff_id, name=staff_name),
                            availability_type=(
                                ["Available"]
                                if "9" in staff_name
                                else ["Timeshift", "Payment"]
                            ),
                            existing_activity=relevant_activity_name,
                        )
                    )
                return availability

    def get_locations(self) -> list[Location]:
        with database_connection() as db:
            return [
                Location(id=row["id"], name=row["name"])
                for row in db.execute("SELECT id, name FROM locations").fetchall()
            ]

    def update_activity(self, payload: Activity) -> bool:
        with database_connection() as db:
            with db:
                try:
                    update_sqlquery = """UPDATE activities SET name=:name, location_id=:location_id, start=:start, finish=:finish WHERE id = :id"""
                    db.execute(
                        update_sqlquery,
                        {
                            "id": payload.id,
                            "name": payload.name,
                            "location_id": valid_uuid_or_none(payload.location),
                            "start": payload.activity_start,
                            "finish": payload.activity_finish,
                        },
                    )
                    db.execute(
                        "DELETE FROM staff_assignments WHERE activity_id=:activity_id",
                        {"activity_id": payload.id},
                    )

                    for assignment in payload.assignments:

                        db.execute(
                            "INSERT INTO staff_assignments (staff_id, activity_id) VALUES (:staff_id, :activity_id)",
                            {
                                "staff_id": valid_uuid_or_none(assignment.staff),
                                "activity_id": payload.id,
                            },
                        )

                except sqlite3.IntegrityError as e:
                    raise ValueError("invalid location or staff id")
        activity_updated.send(self)
        self._window.destroy()
        return True


generate_typescript(EditActivityApi(), "EditActivityApi", __file__, "../types.ts")
