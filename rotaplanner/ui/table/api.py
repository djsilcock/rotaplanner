import datetime
import sqlite3
from collections import ChainMap
from logging import getLogger
from uuid import UUID, uuid4

import webview
from pydantic import BaseModel, Field

from rotaplanner.apigen import JSApi, generate_typescript
from rotaplanner.database import database_connection

from ..common_types import Activity, Location, Role, Staff, StaffAssignment, Timeslot
from ..editactivity import create_window as create_edit_activity_window

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


class LayerCache:
    def __init__(self):
        self.chainmap = ChainMap()

    def save_layer(self, data: dict, layer_id: str = None):
        if layer_id is None:
            layer_id = str(uuid4())
        new_layer = {"__layer_id__": layer_id}
        new_layer.update({k: v for k, v in data.items() if self.chainmap.get(k) != v})
        new_layer.update({k: None for k in self.chainmap if k not in data})
        self.chainmap = self.chainmap.new_child(new_layer)
        return layer_id

    def get_layers_from(self, layer_id: str):
        layers = []
        for layer in self.chainmap.maps:
            if layer.get("__layer_id__") == layer_id:
                break
            layers.append(layer)

        new_map = ChainMap(*layers)

        return new_map


class TableDataCache:
    def __init__(self):
        self.staff_and_location_cache = LayerCache()
        self.activity_cache = LayerCache()
        self.latest_version = None

    def save_new_data(self, data: TableDataResult):
        self.staff_and_location_cache.save_layer(
            {"staff": data.staffData, "locations": data.locationsData},
            layer_id=str(data.queryVersion),
        )
        activities_dict = {activity.id: activity for activity in data.activities}
        self.activity_cache.save_layer(activities_dict, layer_id=str(data.queryVersion))
        self.latest_version = str(data.queryVersion)

    def get_updates_from_version(self, query_version: str):
        staff_and_location = self.staff_and_location_cache.get_layers_from(
            query_version
        )
        activities = dict(self.activity_cache.get_layers_from(query_version))
        activities.pop("__layer_id__", None)

        return TableDataResult(
            queryVersion=UUID(self.latest_version),
            dateRange=DateRange(start=datetime.date.min, end=datetime.date.max),
            staff=[
                l for l in staff_and_location.get("staff", {}).keys() if l is not None
            ],
            locations=[
                l
                for l in staff_and_location.get("locations", {}).keys()
                if l is not None
            ],
            staffData=staff_and_location.get("staff", {}),
            locationsData=staff_and_location.get("locations", {}),
            activities=list(activities.values()),
        )


table_data_cache = TableDataCache()


def valid_uuid_or_none(value):
    try:
        return str(UUID(value))

    except (ValueError, TypeError):
        return None


class UpdateLocationRequest(BaseModel):
    draggedId: str
    droptargetId: str
    initialDropzoneId: str


class UpdateStaffRequest(BaseModel):
    draggedId: str
    droptargetId: str
    initialDropzoneId: str
    ctrlKey: bool


class AvailableForTimeslotQuery(BaseModel):
    activity_id: UUID


class AvailableForTimeslotResult(BaseModel):
    staff: Staff
    availability_type: str
    existing_activity: str | None = None


class TableApi(JSApi):
    _window: webview.Window = None
    _activity_windows: dict[str, webview.Window]

    def __init__(self):
        super().__init__()
        self._window = None
        self._activity_windows = {}

    def data(self, force_refresh=True) -> TableDataResult:
        if table_data_cache.latest_version is None or force_refresh:
            dates, locations, activities, staff = self._get_core_query()

            #    table_data_cache.save_new_data(
            return TableDataResult(
                dateRange=(
                    DateRange(start=dates[0], end=dates[1])
                    if dates
                    else DateRange(
                        start=datetime.date.today(), end=datetime.date.today()
                    )
                ),
                staff=[l for l in staff.keys() if l is not None],
                locations=[l for l in locations.keys() if l is not None],
                staffData=staff,
                locationsData=locations,
                activities=list(activities.values()),
            )
        #    )
        response = table_data_cache.get_updates_from_version(None)
        print(response)
        return response

    def _get_core_query(self):
        with database_connection() as db:
            with db:
                activities: dict[str, Activity] = {}
                staff: dict[str, Staff] = {}
                locations: dict[str, Location] = {}
                timeslots: dict[str, Timeslot] = {}
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
        min_date = min(
            (activity.activity_start.date() for activity in activities.values()),
            default=datetime.date.today(),
        )
        max_date = max(
            (activity.activity_finish.date() for activity in activities.values()),
            default=datetime.date.today(),
        )

        dates = (min_date, max_date)

        return dates, locations, activities, staff

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
                    print(staff_id, staff_name, activity_id, relevant_activity_name)
                    availability.append(
                        AvailableForTimeslotResult(
                            staff=Staff(id=staff_id, name=staff_name),
                            availability_type=(
                                "Available"
                                if relevant_activity_name is None
                                else "Assigned"
                            ),
                            existing_activity=relevant_activity_name,
                        )
                    )

                return availability

    def update_staff(self, payload: UpdateStaffRequest) -> TableDataResult:

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
        affected_cells = []
        if dropinfo != initial_info:
            with database_connection() as db:
                try:

                    def move_activity_assignment(
                        from_staff_id, to_staff_id, activity_id
                    ):
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
                            ("act", activity_id),
                            ("cell", from_staff_id, from_date),
                            ("cell", to_staff_id, to_date),
                        ):
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
                    print("Integrity error:", e)

        return self.data(force_refresh=True)

    def update_location(self, payload: UpdateLocationRequest) -> TableDataResult:

        match payload:
            case UpdateLocationRequest(
                draggedId=dragged_id,
                droptargetId=droptarget_id,
                initialDropzoneId=initial_dropzone_id,
            ):
                pass
            case _:
                raise ValueError("did not understand instruction")
        draginfo = tuple(dragged_id.split("--"))
        dropinfo = tuple(droptarget_id.split("--"))
        initial_info = tuple(initial_dropzone_id.split("--"))

        with database_connection() as db:
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
                            activity_id = valid_uuid_or_none(activity_id)
                            activity_query = """SELECT start, finish, location_id FROM activities WHERE id = :id"""
                            activity_row = db.execute(
                                activity_query, {"id": activity_id}
                            ).fetchone()
                            if activity_row is None:
                                raise ValueError(
                                    f"activity with id {activity_id} not found"
                                )
                            if activity_row["location_id"] != from_location:
                                raise ValueError(
                                    f"activity {activity_id} is not located at {from_location}"
                                )
                            if to_location is not None:
                                location_query = (
                                    """SELECT id FROM locations WHERE id = :id"""
                                )
                                location_row = db.execute(
                                    location_query, {"id": to_location}
                                ).fetchone()
                                if location_row is None:
                                    raise ValueError(
                                        f"location with id {to_location} not found"
                                    )
                            if activity_row["start"].date() != date1:
                                raise ValueError(
                                    f"activity {activity_id} does not start on {from_date}"
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

                    case (
                        ("assn", assn_id, staff_id),
                        ("act", from_activity_id),
                        ("act", to_activity_id),
                    ):
                        with db:
                            old_association_query = """SELECT staff_id,activity_id FROM staff_assignments WHERE assignment_id = :assn_id"""
                            old_association_row = db.execute(
                                old_association_query, {"assn_id": assn_id}
                            ).fetchone()
                            if old_association_row is None:
                                raise ValueError(
                                    f"assignment with id {assn_id} not found"
                                )
                            if old_association_row["staff_id"] != staff_id:
                                raise ValueError(
                                    f"assignment {assn_id} is not associated with staff {staff_id}"
                                )
                            if old_association_row["activity_id"] != from_activity_id:
                                raise ValueError(
                                    f"assignment {assn_id} is not associated with activity {from_activity_id}"
                                )
                            db.execute(
                                "UPDATE staff_assignments SET activity_id=:new_activity_id WHERE assignment_id=:assn_id",
                                (
                                    {
                                        "assn_id": assn_id,
                                        "new_activity_id": to_activity_id,
                                    }
                                ),
                            )
            except sqlite3.IntegrityError as e:
                print("Integrity error:", e)
            except ValueError as e:
                print("Value error:", e)

        return self.data(force_refresh=True)

    def open_activity_editor(self, activity_id: str):
        if activity_id in self._activity_windows:
            window = self._activity_windows[activity_id]
            if window is not None:
                window.show()
                return
        self._activity_windows[activity_id] = create_edit_activity_window(activity_id)
        self._activity_windows[
            activity_id
        ].events.closed += lambda: self._activity_windows.pop(activity_id, None)


generate_typescript(TableApi(), "TableApi", __file__, "../types.ts")
