from dataclasses import fields
import strawberry

from strawberry.fastapi import BaseContext
from strawberry.dataloader import DataLoader
from strawberry.relay import Node
from strawberry.scalars import JSON

import sqlite3
from .context import CustomContext


@strawberry.type
class Location(Node):
    id: strawberry.relay.NodeID[str]
    name: str

    @classmethod
    async def resolve_nodes(
        cls, info: strawberry.Info, node_ids: list[str], required: bool
    ) -> list["Location"]:
        context = info.context
        nodes = await context.data_loaders.location_loader.load_many(node_ids)
        if required and any(node is None for node in nodes):
            raise ValueError("One or more nodes not found")
        return nodes

    @strawberry.field
    async def activities(
        self, info: strawberry.Info, start: str = "1970-01-01", end: str = "2100-01-01"
    ) -> list["Activity"]:
        context = info.context
        # You can access the database connection from the context
        connection = context.connection
        cursor = connection.execute(
            """
        SELECT 
            activities.id as activity_id,
            location_id,
            min(timeslots.start) as activity_start,
			max(timeslots.finish) as activity_finish
        FROM activities
        LEFT JOIN timeslots on timeslots.activity_id = activities.id
        WHERE activities.location_id = ?
        AND date(timeslots.start) >= date(?)
        AND date(timeslots.start) <= date(?)
		GROUP BY activities.id
        ORDER BY timeslots.start
        """,
            (self.id, start, end),
        )
        activities = [row["activity_id"] for row in cursor.fetchall()]
        return await context.data_loaders.activity_loader.load_many(activities)

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
class Staff(Node):
    id: strawberry.relay.NodeID[str]
    name: str

    @classmethod
    async def resolve_nodes(
        cls, info: strawberry.Info, node_ids: list[str], required: bool
    ) -> list["Staff"]:
        context = info.context
        nodes = await context.data_loaders.staff_loader.load_many(node_ids)
        if required and any(node is None for node in nodes):
            raise ValueError("One or more nodes not found")
        return nodes

    @strawberry.field
    async def assignments(
        self, info: strawberry.Info, start: str = "1970-01-01", end: str = "2100-01-01"
    ) -> list["StaffAssignment"]:
        context = info.context
        # You can access the database connection from the context
        assignment_ids = await context.data_loaders.assignments_for_staff_loader.load(
            self.id
        )
        return await context.data_loaders.staff_assignments_loader.load_many(
            assignment_ids
        )

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
class ActivityTag:
    id: strawberry.ID
    name: str


@strawberry.type
class StaffAssignment(Node):
    _assignment_id: strawberry.relay.NodeID[int]
    _staff_id: strawberry.Private[str]
    _timeslot: strawberry.Private[tuple[str, str]]  # activity_id + start_time

    @strawberry.field
    def staff(self, info: strawberry.Info) -> Staff:
        return info.context.data_loaders.staff_loader.load(self._staff_id)

    @strawberry.field
    def timeslot(self, info: strawberry.Info) -> "TimeSlot":
        return info.context.data_loaders.timeslots_loader.load(self._timeslot)

    @strawberry.field
    def flags(self, info: strawberry.Info) -> list[AssignmentFlags]:
        context = info.context
        return context.data_loaders.assignment_flags_loader.load(
            (self._staff_id, *self._timeslot)
        )


@strawberry.type
class TimeSlot(Node):
    id: strawberry.relay.NodeID[int]
    activity_id: strawberry.Private[str]
    start: str  # Using string for simplicity
    finish: str  # Using string for simplicity

    @strawberry.field
    def activity(self, info: strawberry.Info[CustomContext]) -> "Activity":
        context = info.context
        return context.data_loaders.activity_loader.load(self.activity_id)

    @strawberry.field
    async def assignments(
        self, info: strawberry.Info[CustomContext]
    ) -> list[StaffAssignment]:
        context = info.context
        assignment_ids = (
            await context.data_loaders.assignments_for_timeslot_loader.load(self.id)
        )
        return await context.data_loaders.staff_assignments_loader.load_many(
            assignment_ids
        )

    @classmethod
    async def resolve_nodes(
        cls, info: strawberry.Info, node_ids: list[int], required: bool
    ) -> list["TimeSlot"]:
        context = info.context

        nodes = await context.data_loaders.timeslots_loader.load_many(node_ids)
        if required and any(node is None for node in nodes):
            raise ValueError("One or more nodes not found")
        return nodes


@strawberry.type
class Activity(Node):
    id: strawberry.relay.NodeID[str]
    name: str
    type: str
    template_id: str
    location_id: strawberry.Private[str]

    @classmethod
    async def resolve_nodes(
        cls, info: strawberry.Info, node_ids: list[str], required: bool
    ) -> list["Activity"]:
        context = info.context
        nodes = await context.data_loaders.activity_loader.load_many(node_ids)
        if required and any(node is None for node in nodes):
            raise ValueError("One or more nodes not found")
        return nodes

    @strawberry.field
    async def activity_start(self, info: strawberry.Info[CustomContext]) -> str:
        timeslots = await self.timeslots(info)
        return min(t.start for t in timeslots) if timeslots else ""

    @strawberry.field
    async def activity_finish(self, info: strawberry.Info[CustomContext]) -> str:
        timeslots = await self.timeslots(info)
        return max(t.finish for t in timeslots) if timeslots else ""

    @strawberry.field
    async def timeslots(self, info: strawberry.Info[CustomContext]) -> list[TimeSlot]:
        context = info.context
        return await context.data_loaders.timeslots_loader.load_many(
            await context.data_loaders.timeslots_for_activity_loader.load(self.id)
        )

    @strawberry.field
    async def location(self, info: strawberry.Info[CustomContext]) -> Location | None:
        context = info.context
        return await context.data_loaders.location_loader.load(self.location_id)

    @strawberry.field
    async def assignments(
        self, info: strawberry.Info[CustomContext]
    ) -> list[StaffAssignment]:

        context = info.context

        assignment_ids = (
            await context.data_loaders.assignments_for_activity_loader.load(self.id)
        )
        return await context.data_loaders.staff_assignments_loader.load_many(
            assignment_ids
        )

    @strawberry.field
    async def tags(self, info: strawberry.Info[CustomContext]) -> list[ActivityTag]:
        context = info.context
        return await context.data_loaders.activity_tags_for_activity_loader.load(
            self.id
        )

    @strawberry.field
    async def requirements(self, info: strawberry.Info[CustomContext]) -> JSON:
        context = info.context
        return {}

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Activity":
        columns = {col: row[col] for col in row.keys()}
        return cls(**columns)


@strawberry.type
class DateRange:
    start: str
    end: str
