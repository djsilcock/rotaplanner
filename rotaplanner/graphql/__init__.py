import strawberry


from strawberry.fastapi import GraphQLRouter, BaseContext
from rotaplanner.database import Connection
from strawberry.printer import print_schema
from strawberry.relay import Node
from enum import Enum
from typing import Literal


import sqlite3
from .context import CustomContext
from .object_types import (
    Location,
    Staff,
    Activity,
    TimeSlot,
    AssignmentFlags,
    StaffAssignment,
    DateRange,
)
from .input_types import (
    TimeSlotInput,
    RequirementInput,
    DailyRecurrenceInput,
    WeeklyRecurrenceInput,
    MonthlyRecurrenceInput,
    WeekInMonthRecurrenceInput,
    RecurrenceGroup,
    RecurrenceRule,
    NewStaffAssignmentInput,
    ActivityInput,
)
from .dataloaders import DataLoaders


@strawberry.type
class Query:
    @strawberry.field
    def hello(self, value: strawberry.Maybe[str | None] = None) -> str:
        return f"Hello, {value.value if value else 'world'}!"

    node: strawberry.relay.Node = strawberry.relay.node()

    @strawberry.field
    async def activities(
        self,
        info: strawberry.Info,
        start_date: str = "1970-01-01",
        end_date: str = "2199-12-31",
        location_id: strawberry.Maybe[strawberry.ID | None] = None,
        staff_id: strawberry.Maybe[strawberry.ID | None] = None,
    ) -> list[Activity]:
        context = info.context

        # You can access the database connection from the context
        connection = context.connection
        params = {"start_date": start_date, "finish_date": end_date}
        if location_id is not None:
            location_id = location_id.value
            if location_id is None:
                location_clause = "AND activities.location_id IS NULL"

            else:
                location_clause = "AND activities.location_id = :location_id"
                params["location_id"] = location_id
        else:
            location_clause = ""
        if staff_id is not None:
            staff_id = staff_id.value
            if staff_id is None:
                staff_clause = """
                AND NOT EXISTS (
                    SELECT 1 FROM staff_assignments WHERE staff_id IS NULL
                )"""
            else:
                staff_clause = """
                AND EXISTS (
                    SELECT 1 FROM staff_assignments WHERE staff_id = :staff_id
                )"""
                params["staff_id"] = staff_id
        else:
            staff_clause = ""
        cursor = connection.execute(
            f"""
        SELECT distinct activities.id

        FROM activities
        LEFT JOIN timeslots ON activities.id = timeslots.activity_id
        WHERE date(timeslots.start) >= date(:start_date)
        AND date(timeslots.finish) <= date(:finish_date)
        {location_clause}
        {staff_clause}
        ORDER BY timeslots.start""",
            params,
        )
        return await context.data_loaders.activity_loader.load_many(
            [row[0] for row in cursor.fetchall()]
        )

    @strawberry.field
    async def locations(self, info: strawberry.Info) -> list[Location]:
        context = info.context
        # You can access the database connection from the context
        connection = context.connection
        cursor = connection.execute("SELECT id FROM locations")
        return await context.data_loaders.location_loader.load_many(
            [row[0] for row in cursor.fetchall()]
        )

    @strawberry.field
    async def staff(self, info: strawberry.Info) -> list[Staff]:
        context = info.context
        # You can access the database connection from the context
        connection = context.connection
        cursor = connection.execute("SELECT id FROM staff")
        return await context.data_loaders.staff_loader.load_many(
            [row[0] for row in cursor.fetchall()]
        )

    @strawberry.field
    async def daterange(self, info: strawberry.Info) -> DateRange:
        context = info.context
        connection = context.connection
        cursor = connection.execute(
            """
        SELECT 
            MIN(date(timeslots.start)),
            MAX(date(timeslots.finish))
        FROM timeslots
        """
        )
        row = cursor.fetchone()
        if row is None or row[0] is None or row[1] is None:
            return DateRange(start="1970-01-01", end="1970-01-01")
        return DateRange(start=row[0], end=row[1])

    @strawberry.field
    async def assignments(
        self, info: strawberry.Info[CustomContext], start: str, end: str
    ) -> list[StaffAssignment]:
        context = info.context
        # You can access the database connection from the context

        connection = context.connection
        cursor = connection.execute(
            """
        SELECT 
            staff_assignments.assignment_id,
            staff_assignments.timeslot_id
        FROM staff_assignments
        JOIN timeslots ON timeslots.id=staff_assignments.timeslot_id
        WHERE date(timeslots.start) >= date(?)
        AND date(timeslots.start) <= date(?)
        ORDER BY timeslots.start
        """,
            (start, end),
        )
        assignments = await context.data_loaders.staff_assignments_loader.load_many(
            [row[0] for row in cursor.fetchall()]
        )
        # could obviously do this in the SQL query but this is clearer and is easier to maintain
        return assignments


async def change_staff_assignment(
    info: strawberry.Info["CustomContext"],
    staff_id: strawberry.ID | None,
    timeslot: TimeSlotInput,
    change: NewStaffAssignmentInput,
) -> list[str]:

    messages = []

    if staff_id is None:
        if change.staff is None:
            return ValueError("No staff is allocated")
        if change.staff.value is None:
            return ValueError("staff_id and change.staff cannot both be null")
        if not (change.staff and (change.staff.value is not None)):
            return ValueError(
                "Tried to allocate staff but change.staff is missing or null"
            )
    (new_activity_id, new_start_time) = (
        (timeslot.activity_id, timeslot.start_time)
        if change.timeslot is None
        else change.timeslot.value
    )
    new_staff = staff_id if change.staff is None else change.staff.value
    with info.context.connection as connection:
        try:
            if new_staff is None:
                messages.append(f"Remove {staff_id} from {timeslot}")
                connection.execute(
                    "DELETE FROM staff_assignments WHERE activity_id = ? AND staff_id = ? AND start_time = ?",
                    (timeslot.activity_id, staff_id, timeslot.start_time),
                )
            else:
                if staff_id is None:

                    connection.execute(
                        "INSERT INTO staff_assignments (activity_id, start_time, staff_id) VALUES (?, ?, ?)",
                        (new_activity_id, new_start_time, new_staff),
                    )

                locator_clause = (
                    "WHERE staff_id = ? AND activity_id = ? AND start_time = ?"
                )
                locator_tuple = (
                    staff_id,
                    timeslot.activity_id,
                    timeslot.start_time,
                )
                if (
                    new_activity_id != timeslot.activity_id
                    or new_start_time != timeslot.start_time
                ):
                    connection.execute(
                        f"UPDATE staff_assignments SET activity_id=?,start_time=? {locator_clause}",
                        (new_activity_id, new_start_time, *locator_tuple),
                    )
                if staff_id != new_staff:
                    connection.execute(
                        f"UPDATE staff_assignments SET staff_id=? {locator_clause}",
                        (new_staff, *locator_tuple),
                    )
                if change.attendance:
                    connection.execute(
                        f"UPDATE staff_assignments SET attendance= ? {locator_clause}",
                        (change.attendance.value, *locator_tuple),
                    )
                if change.tags:
                    connection.execute(
                        f"DELETE from assignment_tag_assocs {locator_clause}",
                        locator_tuple,
                    )

                    connection.executemany(
                        f"INSERT INTO assignment_tag_assocs (tag_id, activity_id, start_time, staff_id) VALUES (?, ?, ?, ?)",
                        [
                            (tag_id, new_activity_id, new_start_time, new_staff)
                            for tag_id in change.tags.value
                        ],
                    )

            if change.tags and (change.staff and change.staff.value is None):
                return ValueError("Assignment tags not required when removing staff")
            connection.commit()
        except sqlite3.IntegrityError as e:
            return ValueError(f"Already allocated to that session")

    return messages


class RowType(Enum):
    staff = "staff"
    location = "location"


async def move_activity(
    activity_id: str,
    from_row: str,
    to_row: str,
    row_type: RowType,
    info: strawberry.Info,
) -> Activity | None:
    # Placeholder implementation
    print(f"Moving activity {activity_id} from {from_row} to {to_row} by {row_type}")
    if row_type == RowType.location:
        with info.context.connection as connection:
            if (await info.context.data_loaders.location_loader.load(to_row)) is None:
                to_row = None

            connection.execute(
                "UPDATE activities SET location_id = ? WHERE id = ?",
                (to_row, activity_id),
            )
            connection.commit()
            return await info.context.data_loaders.activity_loader.load(activity_id)
    elif row_type == RowType.staff:
        with info.context.connection as connection:
            if (await info.context.data_loaders.staff_loader.load(to_row)) is None:
                to_row = None
            if (await info.context.data_loaders.staff_loader.load(from_row)) is None:
                from_row = None
            print(f"from_row: {from_row}, to_row: {to_row}")
            if to_row is not None:
                if from_row is not None:
                    connection.execute(
                        "UPDATE staff_assignments SET staff_id = ? WHERE staff_id = ? AND activity_id = ?",
                        (to_row, from_row, activity_id),
                    )
                else:
                    connection.execute(
                        "INSERT INTO staff_assignments (staff_id, activity_id, start_time) SELECT ?, activity_id, start FROM timeslots WHERE activity_id = ?",
                        (to_row, activity_id),
                    )
            else:
                if from_row is not None:
                    connection.execute(
                        "DELETE FROM staff_assignments WHERE staff_id = ? AND activity_id = ?",
                        (from_row, activity_id),
                    )
            connection.commit()
            return await info.context.data_loaders.activity_loader.load(activity_id)

    return None


@strawberry.type
class Mutation:
    change_staff_assignment = strawberry.mutation(resolver=change_staff_assignment)

    @strawberry.mutation
    def edit_activity(self, info: strawberry.Info, activity: ActivityInput) -> None:
        return None

    move_activity = strawberry.mutation(resolver=move_activity)


schema = strawberry.Schema(Query, Mutation)

import os

with open(os.path.join(os.getcwd(), "schema.graphql"), "w") as f:
    f.write(print_schema(schema))


async def get_context(connection: Connection):

    yield CustomContext(connection)


graphql_app = GraphQLRouter(schema, context_getter=get_context)
