import collections
from dataclasses import fields
import strawberry

from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter, BaseContext
from strawberry.dataloader import DataLoader
from rotaplanner.database import Connection
from strawberry.printer import print_schema
from strawberry.relay import Node
from enum import Enum

import sqlite3


@strawberry.type
class Location:
    id: strawberry.ID
    name: str

    @classmethod
    def get_loader(cls, ctx: BaseContext) -> DataLoader[str, "Location"]:
        async def batch_load_locations(ids):
            print(f"Batch loading locations for IDs: {ids}")
            cursor = ctx.connection.execute(
                f"SELECT id, name FROM locations WHERE id IN ({','.join('?' for _ in ids)})",
                ids,
            )
            locations = {}
            for row in cursor.fetchall():
                locations[row[0]] = Location(id=row[0], name=row[1])
            return list(locations.get(id) for id in ids)

        return DataLoader(batch_load_locations)


@strawberry.type
class Staff:
    id: strawberry.ID
    name: str

    @strawberry.field
    def assignments(
        self, info: strawberry.Info, start: str = "1970-01-01", end: str = "2100-01-01"
    ) -> list["StaffAssignment"]:
        context = info.context
        # You can access the database connection from the context
        connection = context.connection
        cursor = connection.execute(
            """
        SELECT 
            staff_assignments.staff_id,
            staff_assignments.activity_id,
            staff_assignments.start_time
        FROM staff_assignments
        WHERE staff_assignments.staff_id = ?
        AND date(staff_assignments.start_time) >= date(?)
        AND date(staff_assignments.start_time) <= date(?)
        ORDER BY staff_assignments.start_time
        """,
            (self.id, start, end),
        )
        assignments = [
            StaffAssignment(
                _staff_id=row[0],
                _timeslot=(row[1], row[2]),
            )
            for row in cursor.fetchall()
        ]
        return assignments

    @classmethod
    def get_loader(cls, ctx: BaseContext) -> DataLoader[str, "Staff"]:
        async def batch_load_staff(ids):
            print(f"Batch loading staff for IDs: {ids}")
            cursor = ctx.connection.execute(
                f"SELECT id, name FROM staff WHERE id IN ({','.join('?' for _ in ids)})",
                ids,
            )
            staff = {}
            for row in cursor.fetchall():
                staff[row[0]] = Staff(id=row[0], name=row[1])
            return list(staff.get(id) for id in ids)

        return DataLoader(batch_load_staff)


@strawberry.type
class AssignmentFlags:
    id: strawberry.ID
    name: str


@strawberry.type
class StaffAssignment:
    _staff_id: strawberry.Private[str]
    _timeslot: strawberry.Private[tuple[str, str]]  # activity_id + start_time

    @strawberry.field
    def staff(self, info: strawberry.Info) -> Staff:
        return info.context.get_loader(Staff).load(self._staff_id)

    @strawberry.field
    def timeslot(self, info: strawberry.Info) -> "TimeSlot":
        return info.context.get_loader(TimeSlot).load(self._timeslot)

    @strawberry.field
    def flags(self, info: strawberry.Info) -> list[AssignmentFlags]:
        context = info.context
        return context.assignment_flags_loader.load((self._staff_id, *self._timeslot))


@strawberry.type
class TimeSlot:
    activity_id: strawberry.Private[str]
    start: str  # Using string for simplicity
    finish: str  # Using string for simplicity

    @strawberry.field
    def activity(self, info: strawberry.Info) -> "Activity":
        context = info.context
        return context.get_loader(Activity).load(self.activity_id)

    @strawberry.field
    def staff_assigned(self, info: strawberry.Info) -> list[StaffAssignment]:
        context = info.context
        # You can access the database connection from the context
        connection = context.connection
        cursor = connection.execute(
            """
        SELECT staff_id
        FROM staff_assignments
        WHERE staff_assignments.activity_id = ?
        AND staff_assignments.start_time = ?
        
        """,
            (self.activity_id, self.start),
        )
        return [
            StaffAssignment(_staff_id=row[0], _timeslot=(self.activity_id, self.start))
            for row in cursor.fetchall()
        ]

    @classmethod
    def get_loader(cls, ctx: BaseContext) -> DataLoader[tuple[str, str], "TimeSlot"]:
        async def batch_load_timeslots(keys):
            print(f"Batch loading timeslots for keys: {keys}")
            cursor = ctx.connection.execute(
                f"""SELECT activity_id, start, finish FROM timeslots
                WHERE (activity_id, start) IN ({','.join('(?, ?)' for _ in keys)})""",
                [item for sublist in keys for item in sublist],
            )
            timeslots = {}
            for row in cursor.fetchall():
                timeslots[(row[0], row[1])] = TimeSlot(**row)
            return [timeslots.get(key) for key in keys]

        return DataLoader(batch_load_timeslots)


@strawberry.type
class Activity:
    id: strawberry.ID
    name: str
    type: str
    template_id: str
    location_id: strawberry.Private[str]
    recurrence_rules: str
    requirements: str

    @strawberry.field
    async def activity_start(self, info: strawberry.Info) -> str:
        context = info.context
        timeslots = await context.data_loaders.timeslots_for_activity_loader.load(
            self.id
        )
        return min(timeslots) if timeslots else ""

    @strawberry.field
    async def activity_finish(self, info: strawberry.Info) -> str:
        context = info.context
        timeslots = await self.timeslots(info)
        return max(t.finish for t in timeslots) if timeslots else ""

    @strawberry.field
    async def timeslots(self, info: strawberry.Info) -> list[TimeSlot]:
        context = info.context
        return await context.data_loaders.timeslots_loader.load_many(
            [
                (self.id, t)
                for t in await context.data_loaders.timeslots_for_activity_loader.load(
                    self.id
                )
            ]
        )

    @strawberry.field
    async def location(self, info: strawberry.Info) -> Location:
        context = info.context
        return await context.data_loaders.location_loader.load(self.location_id)

    @strawberry.field
    async def assignments(self, info: strawberry.Info) -> list[StaffAssignment]:
        context = info.context
        return await context.data_loaders.assignments_for_activity_loader.load(self.id)

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Activity":
        columns = {col: row[col] for col in row.keys()}
        return cls(**columns)


@strawberry.type
class DateRange:
    start: str
    end: str


@strawberry.type
class Query:

    @strawberry.field
    async def activities(
        self,
        info: strawberry.Info,
        start_date: str = "1970-01-01",
        end_date: str = "2199-12-31",
    ) -> list[Activity]:
        context = info.context

        # You can access the database connection from the context
        connection = context.connection

        cursor = connection.execute(
            """
        SELECT distinct activities.id

        FROM activities
        LEFT JOIN timeslots ON activities.id = timeslots.activity_id
        WHERE date(timeslots.start) >= date(:start_date)
        AND date(timeslots.finish) <= date(:finish_date)
        ORDER BY timeslots.start""",
            {"start_date": start_date, "finish_date": end_date},
        )
        return await context.data_loaders.activity_loader.load_many(
            [row[0] for row in cursor.fetchall()]
        )

    @strawberry.field
    async def all_locations(self, info: strawberry.Info) -> list[Location]:
        context = info.context
        # You can access the database connection from the context
        connection = context.connection
        cursor = connection.execute("SELECT id FROM locations")
        return await context.data_loaders.location_loader.load_many(
            [row[0] for row in cursor.fetchall()]
        )

    @strawberry.field
    async def all_staff(self, info: strawberry.Info) -> list[Staff]:
        context = info.context
        # You can access the database connection from the context
        connection = context.connection
        cursor = connection.execute("SELECT id FROM staff")
        return await context.data_loaders.staff_loader.load_many(
            [row[0] for row in cursor.fetchall()]
        )

    @strawberry.field
    async def location_by_id(
        self, info: strawberry.Info, id: strawberry.ID
    ) -> Location:
        context = info.context
        return await context.data_loaders.location_loader.load(id)  # type: ignore

    @strawberry.field
    async def staff_by_id(self, info: strawberry.Info, id: strawberry.ID) -> Staff:
        context = info.context
        return await context.data_loaders.staff_loader.load(id)  # type: ignore

    @strawberry.field
    async def activity_by_id(
        self, info: strawberry.Info, id: strawberry.ID
    ) -> Activity:
        context = info.context
        return await context.data_loaders.activity_loader.load(id)  # type: ignore

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


@strawberry.input
class TimeSlotInput:
    activity_id: str
    start_time: str


@strawberry.input
class RequirementInput:
    requirement_id: strawberry.ID
    attendance: int
    minimum: int
    maximum: int


@strawberry.input
class DailyRecurrenceInput:
    interval: int


@strawberry.input
class WeeklyRecurrenceInput:
    interval: int
    weekday: int


@strawberry.input
class MonthlyRecurrenceInput:
    interval: int
    day_in_month: int


@strawberry.input
class WeekInMonthRecurrenceInput:
    interval: int
    weekday: int
    week_no: int


@strawberry.input(one_of=True)
class RecurrenceGroup:
    all_of: list["RecurrenceRule"]
    any_of: list["RecurrenceRule"]
    none_of: list["RecurrenceRule"]


@strawberry.input(one_of=True)
class RecurrenceRule:
    group: strawberry.Maybe[RecurrenceGroup]
    daily: strawberry.Maybe[DailyRecurrenceInput]
    weekly: strawberry.Maybe[WeeklyRecurrenceInput]
    monthly: strawberry.Maybe[MonthlyRecurrenceInput]
    week_in_month: strawberry.Maybe[WeekInMonthRecurrenceInput]


@strawberry.input
class NewStaffAssignmentInput:
    timeslot: strawberry.Maybe[TimeSlotInput]
    staff: strawberry.Maybe[strawberry.ID | None]
    tags: strawberry.Maybe[list[str]]
    attendance: strawberry.Maybe[int]


@strawberry.input
class ActivityInput:
    id: strawberry.Maybe[strawberry.ID]
    template_id: strawberry.Maybe[strawberry.ID | None]
    name: strawberry.Maybe[str]
    location_id: strawberry.Maybe[strawberry.ID]
    recurrence_rules: strawberry.Maybe[RecurrenceGroup]
    requirements: strawberry.Maybe[list[RequirementInput]]
    timeslots: strawberry.Maybe[list[TimeSlotInput]]


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


@strawberry.type
class Mutation:
    change_staff_assignment = strawberry.mutation(resolver=change_staff_assignment)

    @strawberry.mutation
    def edit_activity(self, info: strawberry.Info, activity: ActivityInput) -> None:
        return None


schema = strawberry.Schema(Query, Mutation)

import os

with open(os.path.join(os.getcwd(), "schema.graphql"), "w") as f:
    f.write(print_schema(schema))


class DataLoaders:
    def __init__(self, context: "CustomContext"):
        self._context = context
        self.activity_loader = DataLoader(self.batch_load_activities)
        self.location_loader = DataLoader(self.batch_load_locations)
        self.timeslots_loader = DataLoader(self.batch_load_timeslots)
        self.timeslots_for_activity_loader = DataLoader(
            self.batch_get_timeslots_for_activity
        )
        self.staff_loader = DataLoader(self.batch_load_staff)
        self.assignment_flags_loader = DataLoader(self.batch_load_assignment_flags)
        self.assignments_for_staff_loader = DataLoader(
            self.batch_load_assignments_for_staff
        )
        self.assignments_for_activity_loader = DataLoader(
            self.batch_load_assignments_for_activity
        )

    async def batch_load_assignments_for_activity(self, activity_ids: list[str]):
        print(f"Batch loading assignments for {len(activity_ids)} activity IDs")
        cursor = self._context.connection.execute(
            f"""SELECT 
                staff_assignments.staff_id,
                staff_assignments.activity_id,
                staff_assignments.start_time
            FROM staff_assignments
            WHERE staff_assignments.activity_id IN ({','.join('?' for _ in activity_ids)})
            ORDER BY staff_assignments.start_time""",
            activity_ids,
        )
        assignments_map = {activity_id: [] for activity_id in activity_ids}
        for row in cursor.fetchall():
            assignments_map[row[1]].append(
                StaffAssignment(
                    _staff_id=row[0],
                    _timeslot=(row[1], row[2]),
                )
            )
        return [assignments_map.get(activity_id, []) for activity_id in activity_ids]

    async def batch_load_assignments_for_staff(self, staff_ids: list[str]):
        print(f"Batch loading assignments for {len(staff_ids)} staff IDs")
        cursor = self._context.connection.execute(
            f"""SELECT 
                staff_assignments.staff_id,
                staff_assignments.activity_id,
                staff_assignments.start_time
            FROM staff_assignments
            WHERE staff_assignments.staff_id IN ({','.join('?' for _ in staff_ids)})
            ORDER BY staff_assignments.start_time""",
            staff_ids,
        )
        assignments_map = {staff_id: [] for staff_id in staff_ids}
        for row in cursor.fetchall():
            assignments_map[row[0]].append(
                StaffAssignment(
                    _staff_id=row[0],
                    _timeslot=(row[1], row[2]),
                )
            )
        return [assignments_map.get(staff_id, []) for staff_id in staff_ids]

    async def batch_load_assignment_flags(
        self, assignment_ids: list[tuple[str, str, str]]
    ):
        print(
            f"Batch loading assignment flags for {len(assignment_ids)} assignment IDs"
        )

        cursor = self._context.connection.execute(
            f"""SELECT staff_id, activity_id, start_time,tag_id, assignment_tags.name as tag_name FROM assignment_tag_assocs
            left join assignment_tags on assignment_tags.id=assignment_tag_assocs.tag_id
            WHERE (staff_id, activity_id, start_time) IN ({','.join('(?, ?, ?)' for _ in assignment_ids)})""",
            [item for sublist in assignment_ids for item in sublist],
        )
        flags_map = {
            (staff_id, activity_id, start_time): []
            for staff_id, activity_id, start_time in assignment_ids
        }
        for row in cursor.fetchall():
            flags_map[(row[0], row[1], row[2])].append(
                AssignmentFlags(id=row[3], name=row[4])
            )
        return [flags_map.get(staff_id, []) for staff_id in assignment_ids]

    async def batch_load_staff(self, ids):
        print(f"Batch loading staff for {len(ids)} IDs")
        cursor = self._context.connection.execute(
            f"SELECT id, name FROM staff WHERE id IN ({','.join('?' for _ in ids)})",
            ids,
        )
        staff = {}
        for row in cursor.fetchall():
            staff[row[0]] = Staff(id=row[0], name=row[1])
        return list(staff.get(id) for id in ids)

    async def batch_load_activities(self, ids):
        print(f"Batch loading activities for {len(ids)} IDs")

        cursor = self._context.connection.execute(
            f"""SELECT * FROM activities
            WHERE activities.id IN ({','.join('?' for _ in ids)})""",
            ids,
        )

        activities = {}
        for row in cursor.fetchall():
            new_activity = Activity.from_row(row)
            activities[new_activity.id] = new_activity
        return list(activities.get(id) for id in ids)

    async def batch_load_timeslots(self, keys):
        print(f"Batch loading timeslots for {len(keys)} keys")
        cursor = self._context.connection.execute(
            f"""SELECT activity_id, start, finish FROM timeslots
            WHERE (activity_id, start) IN ({','.join('(?, ?)' for _ in keys)})""",
            [item for sublist in keys for item in sublist],
        )
        timeslots = {}
        for row in cursor.fetchall():
            timeslots[(row[0], row[1])] = TimeSlot(**row)
        return [timeslots.get(key) for key in keys]

    async def batch_load_locations(self, ids):
        print(f"Batch loading locations for {len(ids)} IDs")
        cursor = self._context.connection.execute(
            f"SELECT id, name FROM locations WHERE id IN ({','.join('?' for _ in ids)})",
            ids,
        )
        locations = {}
        for row in cursor.fetchall():
            locations[row[0]] = Location(id=row[0], name=row[1])
        return list(locations.get(id) for id in ids)

    async def batch_get_timeslots_for_activity(self, activity_ids):
        print(f"Batch loading timeslots for {len(activity_ids)} activity IDs")

        cursor = self._context.connection.execute(
            f"""SELECT activity_id, start, finish FROM timeslots
            WHERE activity_id IN ({','.join('?' for _ in activity_ids)})""",
            activity_ids,
        )
        timeslots_for_activity = {}
        for row in cursor.fetchall():
            timeslots_for_activity.setdefault(row["activity_id"], set()).add(
                row["start"]
            )
            self.timeslots_loader.prime(
                (row["activity_id"], row["start"]), TimeSlot(**row)
            )

        return [
            timeslots_for_activity.get(activity_id, set())
            for activity_id in activity_ids
        ]


class CustomContext(BaseContext):
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection
        self.data_loaders = DataLoaders(self)


async def get_context(connection: Connection):

    yield CustomContext(connection)


graphql_app = GraphQLRouter(schema, context_getter=get_context)
