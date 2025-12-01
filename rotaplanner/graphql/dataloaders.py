from strawberry.dataloader import DataLoader
from .object_types import (
    ActivityTag,
    Location,
    Staff,
    Activity,
    TimeSlot,
    AssignmentFlags,
    StaffAssignment,
    DateRange,
)
import sqlite3


class DataLoaders:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection
        self.activity_loader = DataLoader(self.batch_load_activities)
        self.location_loader = DataLoader(self.batch_load_locations)
        self.timeslots_loader = DataLoader(self.batch_load_timeslots)
        self.staff_assignments_loader = DataLoader(self.batch_load_assignments)
        self.timeslots_for_activity_loader = DataLoader(
            self.batch_get_timeslots_for_activity
        )
        self.staff_loader = DataLoader(self.batch_load_staff)
        self.assignment_flags_loader = DataLoader(self.batch_load_assignment_flags)
        self.assignments_for_staff_loader = DataLoader(
            self.batch_get_assignments_for_staff
        )
        self.assignments_for_timeslot_loader = DataLoader(
            self.batch_get_assignments_for_timeslot
        )
        self.assignments_for_timeslot_loader = DataLoader(
            self.batch_get_assignments_for_timeslot
        )
        self.assignments_for_activity_loader = DataLoader(
            self.batch_get_assignments_for_activity
        )
        self.activity_tags_for_activity_loader = DataLoader(
            self.batch_get_tags_for_activity
        )

    async def batch_get_assignments_for_activity(self, activity_ids):
        print(f"Batch loading assignments for {len(activity_ids)} activity IDs")
        cursor = self.connection.execute(
            f"""SELECT 
                staff_assignments.assignment_id
            FROM staff_assignments
            JOIN timeslots ON timeslots.id=staff_assignments.timeslot_id
            WHERE timeslots.activity_id IN ({','.join('?' for _ in activity_ids)})
            """,
            activity_ids,
        )
        assignments_map = {activity_id: [] for activity_id in activity_ids}
        for row in cursor.fetchall():
            assignments_map[row[1]].append(row[0])
        return [assignments_map.get(activity_id, []) for activity_id in activity_ids]

    async def batch_get_assignments_for_timeslot(self, timeslot_ids):
        print(f"Batch loading assignments for {len(timeslot_ids)} timeslot IDs")
        cursor = self.connection.execute(
            f"""SELECT 
                staff_assignments.assignment_id,
                staff_assignments.timeslot_id
                
            FROM staff_assignments
            WHERE staff_assignments.timeslot_id IN ({','.join('?' for _ in timeslot_ids)})
            """,
            timeslot_ids,
        )
        assignments_map = {timeslot_id: [] for timeslot_id in timeslot_ids}
        for row in cursor.fetchall():
            assignments_map[row[1]].append(row[0])
        return [assignments_map.get(timeslot_id, []) for timeslot_id in timeslot_ids]

    async def batch_load_assignments(self, assignment_ids):
        print(f"Batch loading assignments for {len(assignment_ids)} assignment IDs")
        cursor = self.connection.execute(
            f"""SELECT 
                staff_assignments.assignment_id,
                staff_assignments.staff_id,
                staff_assignments.timeslot_id
            FROM staff_assignments
            WHERE staff_assignments.assignment_id IN ({','.join('?' for _ in assignment_ids)})
            """,
            assignment_ids,
        )
        assignments_map = {}
        for row in cursor.fetchall():
            assignments_map[row[0]] = StaffAssignment(
                _staff_id=row[1],
                _timeslot=row[2],
            )
        return [
            assignments_map.get(assignment_id, None) for assignment_id in assignment_ids
        ]

    async def batch_get_assignments_for_staff(self, staff_ids: list[str]):
        print(f"Batch loading assignments for {len(staff_ids)} staff IDs")
        cursor = self.connection.execute(
            f"""SELECT 
                staff_assignments.assignment_id,
                staff_assignments.staff_id,
                staff_assignments.timeslot_id
            FROM staff_assignments
            WHERE staff_assignments.staff_id IN ({','.join('?' for _ in staff_ids)})
            """,
            staff_ids,
        )
        assignments_map = {staff_id: [] for staff_id in staff_ids}
        for row in cursor.fetchall():
            assignments_map[row[0]].append(row[0])  #
        return [assignments_map.get(staff_id, []) for staff_id in staff_ids]

    async def batch_load_assignment_flags(
        self, assignment_ids: list[tuple[str, str, str]]
    ):
        print(
            f"Batch loading assignment flags for {len(assignment_ids)} assignment IDs"
        )

        cursor = self.connection.execute(
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
        cursor = self.connection.execute(
            f"SELECT id, name FROM staff WHERE id IN ({','.join('?' for _ in ids)})",
            ids,
        )
        staff = {}
        for row in cursor.fetchall():
            staff[row[0]] = Staff(id=row[0], name=row[1])
        return list(staff.get(id) for id in ids)

    async def batch_load_activities(self, ids):
        print(f"Batch loading activities for {len(ids)} IDs")

        cursor = self.connection.execute(
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
        cursor = self.connection.execute(
            f"""SELECT id, activity_id, start, finish FROM timeslots
            WHERE id IN ({','.join('?' for _ in keys)})""",
            keys,
        )
        timeslots = {}
        for row in cursor.fetchall():
            timeslots[row[0]] = TimeSlot(**row)
        return [timeslots.get(key) for key in keys]

    async def batch_load_locations(self, ids):
        print(f"Batch loading locations for {len(ids)} IDs")
        cursor = self.connection.execute(
            f"SELECT id, name FROM locations WHERE id IN ({','.join('?' for _ in ids)})",
            ids,
        )
        locations = {}
        for row in cursor.fetchall():
            locations[row[0]] = Location(id=row[0], name=row[1])
        return list(locations.get(id) for id in ids)

    async def batch_get_timeslots_for_activity(self, activity_ids):
        print(f"Batch loading timeslots for {len(activity_ids)} activity IDs")

        cursor = self.connection.execute(
            f"""SELECT id, activity_id, start, finish FROM timeslots
            WHERE activity_id IN ({','.join('?' for _ in activity_ids)})""",
            activity_ids,
        )
        timeslots_for_activity = {}
        for row in cursor.fetchall():
            timeslots_for_activity.setdefault(row["activity_id"], set()).add(row["id"])
            self.timeslots_loader.prime(row["id"], TimeSlot(**row))

        return [
            timeslots_for_activity.get(activity_id, set())
            for activity_id in activity_ids
        ]

    async def batch_get_tags_for_activity(self, activity_ids):
        print(f"Batch loading tags for {len(activity_ids)} activity IDs")

        cursor = self.connection.execute(
            f"""SELECT 
                activity_tag_assocs.activity_id,
                activity_tags.id,
                activity_tags.name
            FROM activity_tag_assocs
            JOIN activity_tags ON activity_tags.id=activity_tag_assocs.tag_id
            WHERE activity_tag_assocs.activity_id IN ({','.join('?' for _ in activity_ids)})""",
            activity_ids,
        )
        tags_for_activity = {}
        for row in cursor.fetchall():
            tags_for_activity.setdefault(row["activity_id"], []).append(
                ActivityTag(id=row["id"], name=row["name"])
            )
        return [tags_for_activity.get(activity_id, []) for activity_id in activity_ids]
