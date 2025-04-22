from typing import Callable, Optional, Protocol
from dataclasses import dataclass, field
from typing import TypedDict
import json
import datetime
import uuid
from pydantic import BaseModel, Field

from nicegui import ui
from nicegui.binding import bindable_dataclass, BindableProperty
from blinker import signal, Signal

from rotaplanner.database import get_database_connection

# These classes only contain the fields that are used in the grid.


@bindable_dataclass
class Staff:
    id: uuid.UUID
    name: str


@bindable_dataclass
class Location:
    id: uuid.UUID
    name: str


@bindable_dataclass
class StaffAssignment:
    staff: Staff
    activity: uuid.UUID
    start_time: datetime.datetime
    finish_time: datetime.datetime
    tags: list[str]


@bindable_dataclass
class Activity:
    id: uuid.UUID
    name: str
    location: Location | None
    activity_start: datetime.datetime
    activity_finish: datetime.datetime
    staff_assignments: set[StaffAssignment] = field(default_factory=set)
    activity_tags: list[str] = field(default_factory=list)


redraw_table = Signal("redraw_table")
recalculate_cell = Signal("recalculate_cell")
activity_changed = Signal("activity_changed")

datastore: dict[tuple[int, int], list] = {}
activity_store: dict[uuid.UUID, Activity] = {}
grid_mode = "staff"

staff = {}
locations = {}
start_date = datetime.date(2023, 1, 1)
end_date = datetime.date(2025, 1, 31)
dates = [
    start_date + datetime.timedelta(days=i)
    for i in range((end_date - start_date).days + 1)
]
staff_assignments = []


def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}


def refresh_data() -> None:
    with get_database_connection() as connection:
        cur = connection.cursor()
        cur.row_factory = dict_factory
        staff_list = [
            Staff(**row)
            for row in cur.execute("SELECT id,name FROM staff ORDER BY name").fetchall()
        ]
        locations_list = [
            Location(**row)
            for row in cur.execute(
                "SELECT id,name FROM locations ORDER BY name"
            ).fetchall()
        ]

        staff.clear()
        locations.clear()
        staff.update({staff.id: staff for staff in staff_list})
        locations.update({location.id: location for location in locations_list})
        print(staff)
        print(locations)
        activities = [
            Activity(location=locations.get(row.pop("location_id")), **row)
            for row in cur.execute(
                "SELECT id,name,location_id,activity_start,activity_finish FROM activities ORDER BY name"
            ).fetchall()
        ]
        activity_store.clear()
        activity_store.update({activity.id: activity for activity in activities})
        result = cur.execute(
            "SELECT staff_id,activity_id,start_time,finish_time FROM staff_assignments ORDER BY start_time"
        )
        while (row := result.fetchone()) is not None:
            activity = activity_store.get(row.pop("activity_id"))
            staff_assignment = StaffAssignment(**row)
            activity.staff_assignments.append(staff_assignment)

        for sa in staff_assignments:
            activity = activity_store.get(sa.activity.id)
            if activity is not None:
                activity.staff_assignments.add(sa)


def staff_grid_from_assignments(
    staff_assignments,
) -> dict[tuple[uuid.UUID, datetime.date], list[uuid.UUID]]:
    grid = {}
    unallocated_activities = {act.id for act in activity_store.values()}
    for sa in staff_assignments:
        cell_date = sa.start_time.date()
        cell_key = (sa.staff.id, cell_date)
        if cell_key not in grid:
            grid[cell_key] = []
        grid[cell_key].append(sa.activity.id)
        unallocated_activities.discard(sa.activity.id)
    for act in unallocated_activities:
        cell_date = activity_store[act].activity_start.date()
        cell_key = (None, cell_date)
        if cell_key not in grid:
            grid[cell_key] = []
        grid[cell_key].append(activity_store[act].id)
    return grid


def location_grid_from_activities(
    activities,
) -> dict[tuple[uuid.UUID, datetime.date], list[uuid.UUID]]:
    grid = {}
    for act in activities:
        cell_date = act.activity_start.date()
        cell_key = (act.location.id if act.location is not None else None, cell_date)
        if cell_key not in grid:
            grid[cell_key] = []
        grid[cell_key].append(act.id)
    return grid


class table_cell(ui.element):
    activities = BindableProperty(
        on_change=lambda self, value: self.draw_contents.refresh()
    )

    def __init__(self, row: Staff | Location, col: datetime.date) -> None:
        super().__init__("div")
        if row is not None:
            self.props["data-row"] = row.id
        self.props["data-col"] = col.strftime("%Y-%m-%d")
        self.row = row
        self.col = col
        self.activities = set()
        self.classes("bg-grey-1 rounded shadow-2 table-cell")
        with self:
            self.draw_contents()

    @ui.refreshable_method
    def draw_contents(self) -> None:
        try:
            activity_list = sorted(
                [activity_store[act] for act in self.activities],
                key=lambda x: x.activity_start,
            )
        except AttributeError:
            return

        for item in activity_list:
            activity(item, cell=self)


class activity:

    def __init__(self, item, cell):
        self.cell = cell
        self.item = item
        redraw_table.connect(self.draw_contents.refresh, sender=item)
        el = (
            ui.element("div")
            .props(f"draggable data-item={item.id} data-row={cell.row}")
            .classes("cursor-pointer bg-blue-grey-2 activity")
        )
        with el:
            self.draw_contents()

    @ui.refreshable_method
    def draw_contents(self) -> None:
        print(self.item)
        ui.label(self.item.name)
        if self.item.location is not None and self.item.location.id != self.cell.row:
            if self.item.location:
                ui.label(f"({self.item.location.name})").classes("text-xs")

        for sa in self.item.staff_assignments:
            if sa.staff.id == self.cell.row:
                continue
            ui.label(f"{sa.staff.name} ({sa.start_time.strftime('%H:%M')})").classes(
                "text-xs"
            )

    def on_dragstart(self):
        dragged["activity"] = self


class staff_in_activity:
    def __init__(self, staff_assignment: StaffAssignment) -> None:
        self.assignment = staff_assignment

        el = (
            ui.element("div")
            .props(f"draggable")
            .classes("cursor-pointer bg-blue-grey-2 activity")
        )
        el.props.update(
            {
                "data-staff": staff_assignment.staff.id,
                "data-activity": staff_assignment.activity.id,
            }
        )
        with el:
            self.draw_contents()
        el.on(
            "dragstart",
            js_handler="""(e) => {
                e.dataTransfer.setData('application/x-name', e.target.dataset.payload)
                }""",
        )


ui.add_css(
    """
    .table-cell:has(.dragover-activity),.table-cell.dragover-activity {
        background-color: #e0f7fa !important;
    }
    .activity:has(.dragover-name),.activity.dragover-name {
        background-color: #e0f7fa !important;
    }
    
    """
)

ui_cells: dict[tuple[int, int], table_cell] = {}
dragged = {}


def move_card(e) -> None:
    drag_info = e.args["detail"]

    print("move_card", drag_info)

    return


class main_table(ui.element, component="main_table.vue"):
    def __init__(self, rows, cols):
        super().__init__()
        self.props["rows"] = rows
        self.props["cols"] = cols


with ui.element("div").style("border:5px solid red") as header:

    with ui.element("div").style("width:90vw") as container:
        '''
        container.on(
            "dragenter",
            js_handler="""(event)=>{
                if (event.dataTransfer.types.includes('application/x-activity')) {
                    //dragged item is an activity
                    event.target.classList.add('dragover-activity')
                    event.preventDefault()
                    } else if (event.dataTransfer.types.includes('application/x-name')) {
                    //dragged item is a name
                    event.target.classList.add('dragover-name')
                    event.preventDefault()
                    }
                 }""",
        )
        container.on(
            "dragleave",
            js_handler="""(event)=>{
                console.log('dragleave',event.target)
                event.target.classList.remove('dragover-activity')
                event.target.classList.remove('dragover-name')
                }""",
        )
        container.on(
            "dragover",
            js_handler="""(event)=>{
                if (event.dataTransfer.types.includes('application/x-activity')) {
                    event.preventDefault()

                }
                else if (event.dataTransfer.types.includes('application/x-name') && event.target.closest('.activity')) {
                    event.preventDefault()
                    }
                    }""",
        )
        container.on(
            "drop",
            js_handler="""(event)=>{
                event.target.classList.remove('dragover-activity')
                event.target.classList.remove('dragover-name')
                let dropData,draggedData,dragType
                if (event.dataTransfer.types.includes('application/x-activity')) {
                        dropData = event.target.dataset
                        draggedData = JSON.parse(event.dataTransfer.getData('application/x-activity'))
                        dragType = 'activity'
                    } else if (event.dataTransfer.types.includes('application/x-name')) {
                        dropData = event.target.closest('.activity')?.dataset
                        if (!dropData) return
                        draggedData = JSON.parse(event.dataTransfer.getData('application/x-name'))
                        dragType = 'name'
                    } else return

                event.preventDefault()
                console.log('drop',event)

                event.target.dispatchEvent(new CustomEvent('drop_done', {
                    bubbles: true,
                    detail: {
                        source_row:draggedData.row,
                        dragged_item:draggedData.item,
                        dest_row:dropData.row,
                        dest_col:dropData.col,
                        mode:draggedData.mode,
                        dragType:dragType}
                        }
                    ))
                }
            """,
        )
        container.on(
            "dragstart",
            js_handler="""(e) => {
                console.log('dragstart',e)
                let mode
                if (e.ctrlKey) {
                        mode = 'copy'
                    } else {
                        mode = 'move'
                    }
                if (e.target.matches('.activity')) {
                console.log('activity',e.target.dataset)
                e.dataTransfer.setData('application/x-activity', JSON.stringify({mode,...e.target.dataset}))
                } else if (e.target.matches('.activity-name')) {
                console.log('name',e.target.dataset)
                e.dataTransfer.setData('application/x-name', JSON.stringify({mode,...e.target.dataset}))
                } else {
                console.warn('unidentified target',e.target)
                return
                }
                //e.preventDefault()

                }""",
        )

        '''
        cols = len(dates)
        rows = len(staff)
        refresh_data()
        with main_table(rows=rows, cols=cols).style(
            "border: 5px solid blue;overflow:auto"
        ) as staff_grid:
            ui.label("")
            for row in staff.values():
                ui.label(row.name).style(
                    "position:sticky;left:0;z-index:1;background-color: white;opacity:0.8"
                )
            ui.label("Unallocated")
            for col in dates:
                ui.label(col.strftime("%d %b %Y")).style(
                    "white-space:nowrap;position:sticky;top:0;z-index:1"
                )

                for row in staff.values():
                    ui_cells[row.id, col] = table_cell(row, col)

                ui_cells[None, col] = table_cell(None, col)
        act_grid = staff_grid_from_assignments(staff_assignments)
        for key, activities in act_grid.items():
            cell = ui_cells[key]
            cell.activities = tuple(activities)


ui.run(title="Drag and Drop Example", port=8080)
