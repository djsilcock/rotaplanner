import datetime
import sqlite3
from collections import ChainMap
from logging import getLogger
from uuid import UUID, uuid4

import pydantic

from pydantic import BaseModel, Field


from rotaplanner.database import database_connection, database_version

from .types import Activity, Location, Role, Staff, StaffAssignment

logger = getLogger(__name__)


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
    activities: list[Activity]


def valid_uuid_or_none(value):
    try:
        return str(UUID(value))

    except (ValueError, TypeError):
        return None


class UpdateLocationRequest(BaseModel):
    activityId: str
    toRowId: str
    toColId: str
    fromRowId: str | None = None
    fromColId: str | None = None
    shiftKey: bool = False
    altKey: bool = False
    ctrlKey: bool = False


class UpdateStaffRequest(BaseModel):
    toRowId: str
    toColId: str
    fromRowId: str | None = None
    fromColId: str | None = None
    shiftKey: bool = False
    altKey: bool = False
    ctrlKey: bool = False


class UpdateAssignmentRequest(BaseModel):
    assignmentId: str
    toActivityId: str


class UpdateRoleRequest(BaseModel):
    activityId: str
    staffId: str
    roleId: str


class DeleteActivitiesRequest(BaseModel):
    activity_ids: list[str] = Field(alias="activityIds")


@pydantic.validate_call
def update_staff(payload: UpdateStaffRequest) -> bool:

    logger.info("Update staff payload: %s", payload)
    match payload:
        case UpdateStaffRequest(
            draggedId=dragged_id,
            droptargetId=droptarget_id,
            initialDropzoneId=initial_dropzone_id,
            ctrlKey=should_copy,
        ):
            pass
        case _:
            raise ValueError("did not understand instruction")
    draginfo = tuple(dragged_id.split("--"))
    dropinfo = tuple(droptarget_id.split("--"))
    initial_info = tuple(initial_dropzone_id.split("--"))
    if dropinfo != initial_info:
        with database_connection() as db:
            try:

                def move_activity_assignment(from_staff_id, to_staff_id, activity_id):
                    from_staff_id = valid_uuid_or_none(from_staff_id)
                    to_staff_id = valid_uuid_or_none(to_staff_id)
                    logger.info(
                        "Moving assignment of activity %s from staff %s to staff %s",
                        activity_id,
                        from_staff_id,
                        to_staff_id,
                    )
                    print(
                        f"moving assignment of activity {activity_id} from staff {from_staff_id} to staff {to_staff_id}"
                    )
                    if from_staff_id is not None and to_staff_id is not None:
                        db.execute(
                            "UPDATE OR IGNORE staff_assignments SET staff_id=:new_staff_id WHERE staff_id=:old_staff_id AND activity_id =:activity_id",
                            (
                                {
                                    "activity_id": activity_id,
                                    "new_staff_id": to_staff_id,
                                    "old_staff_id": from_staff_id,
                                }
                            ),
                        )
                    elif from_staff_id is None:
                        db.execute(
                            "INSERT OR IGNORE INTO staff_assignments (staff_id, activity_id) VALUES (:new_staff_id, :activity_id)",
                            {
                                "activity_id": activity_id,
                                "new_staff_id": to_staff_id,
                            },
                        )
                    elif to_staff_id is None:
                        db.execute(
                            "DELETE FROM staff_assignments WHERE staff_id=:old_staff_id AND activity_id =:activity_id",
                            {
                                "activity_id": activity_id,
                                "old_staff_id": from_staff_id,
                            },
                        )

                match (draginfo, initial_info, dropinfo):
                    case (
                        ("act", activity_id, staff_id),
                        ("cell", from_date, from_staff_id),
                        ("cell", to_date, to_staff_id),
                    ) if (
                        from_date == to_date
                    ):  # same date, just moving between staff
                        assert (
                            staff_id == from_staff_id
                        ), "Dragged staff ID does not match initial dropzone staff ID"
                        with db:
                            if should_copy:
                                from_staff_id = None

                            move_activity_assignment(
                                from_staff_id, to_staff_id, activity_id
                            )

                    case _:
                        print("unhandled case")
                        print(draginfo, initial_info, dropinfo)
            except sqlite3.IntegrityError as e:
                logger.error("Integrity error:", e)
                return False
    database_version.update(lambda v: v + 1)
    return True


@pydantic.validate_call
def update_location(payload: UpdateLocationRequest) -> bool:

    with database_connection() as db:
        try:

            date1 = datetime.date.fromisoformat(payload.fromColId)
            date2 = datetime.date.fromisoformat(payload.toColId)
            date_delta = (date2 - date1).days
            from_location = valid_uuid_or_none(payload.fromRowId)
            to_location = valid_uuid_or_none(payload.toRowId)

            with db:
                activity_id = valid_uuid_or_none(payload.activityId)
                activity_query = """SELECT start, finish, location_id FROM activities WHERE id = :id"""
                activity_row = db.execute(
                    activity_query, {"id": activity_id}
                ).fetchone()
                if activity_row is None:
                    raise ValueError(f"activity with id {activity_id} not found")
                if activity_row["location_id"] != from_location:
                    raise ValueError(
                        f"activity {activity_id} is not located at {from_location}"
                    )
                if to_location is not None:
                    location_query = """SELECT id FROM locations WHERE id = :id"""
                    location_row = db.execute(
                        location_query, {"id": to_location}
                    ).fetchone()
                    if location_row is None:
                        raise ValueError(f"location with id {to_location} not found")
                if activity_row["start"].date() != date1:
                    raise ValueError(
                        f"activity {activity_id} does not start on {date1}"
                    )

                update_sqlquery = """UPDATE activities SET location_id = :location_id, start=DATETIME(start,:delta), finish=DATETIME(finish,:delta) WHERE id = :id"""
                db.execute(
                    update_sqlquery,
                    {
                        "location_id": valid_uuid_or_none(to_location),
                        "delta": f"{date_delta} DAYS",
                        "id": activity_id,
                    },
                )

        except sqlite3.IntegrityError as e:
            logger.error("Integrity error:", e)
            return False
        except ValueError as e:
            logger.error("Value error:", e)
            return False
    database_version.update(lambda v: v + 1)
    return True


@pydantic.validate_call
def update_role(request: UpdateRoleRequest) -> bool:
    logger.info("Update role payload: %s", request)
    match request:
        case UpdateRoleRequest(
            activityId=activity_id,
            staffId=staff_id,
            roleId=role_id,
        ):
            pass
        case _:
            raise ValueError("did not understand instruction")
    with database_connection() as db:
        try:
            with db:
                if role_id == "None":
                    role_id = None
                db.execute(
                    "UPDATE OR IGNORE staff_assignments SET role_id=:role_id WHERE staff_id=:staff_id AND activity_id=:activity_id",
                    {
                        "activity_id": activity_id,
                        "staff_id": staff_id,
                        "role_id": role_id,
                    },
                )
        except sqlite3.IntegrityError as e:
            logger.error("Integrity error:", e)
            return False
    database_version.update(lambda v: v + 1)
    return True


@pydantic.validate_call
def update_assignment(payload: UpdateAssignmentRequest) -> bool:

    with database_connection() as db:
        try:

            with db:
                old_association_query = """SELECT staff_id,activity_id FROM staff_assignments WHERE assignment_id = :assn_id"""
                old_association_row = db.execute(
                    old_association_query, {"assn_id": payload.assignmentId}
                ).fetchone()
                if old_association_row is None:
                    raise ValueError(
                        f"assignment with id {payload.assignmentId} not found"
                    )
                db.execute(
                    "UPDATE staff_assignments SET activity_id=:new_activity_id WHERE assignment_id=:assn_id",
                    (
                        {
                            "assn_id": payload.assignmentId,
                            "new_activity_id": payload.toActivityId,
                        }
                    ),
                )
        except sqlite3.IntegrityError as e:
            logger.error("Integrity error:", e)
            return False
        except ValueError as e:
            logger.error("Value error:", e)
            return False
    database_version.update(lambda v: v + 1)
    return True


@pydantic.validate_call
def delete_activities(request: DeleteActivitiesRequest) -> bool:
    logger.info("Delete activities payload: %s", request)
    match request:
        case DeleteActivitiesRequest(activity_ids=activity_ids):
            pass
        case _:
            raise ValueError("did not understand instruction")

    with database_connection() as db:
        try:
            with db:
                for activity in activity_ids:
                    activity_id_tpl = tuple(activity.split("--"))
                    match activity_id_tpl:
                        case ("act", activity_id):
                            db.execute(
                                "DELETE FROM activities WHERE id=:activity_id",
                                {"activity_id": activity_id},
                            )
                        case _:
                            logger.warning(f"Unexpected activity_id format: {activity}")
        except sqlite3.IntegrityError as e:
            logger.error("Integrity error:", e)
            return False
    database_version.update(lambda v: v + 1)
    return True
