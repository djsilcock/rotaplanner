import uuid

import asyncstdlib
import reaktiv
import webview

from rotaplanner.table.ui import table, table_cell
from blinker import ANY
import datetime
import pywry
import pathlib
import difflib
from logging import getLogger
from pydantic import BaseModel, Field
import reaktiv
import janus

from rotaplanner.utils import TaskRunner

logger = getLogger(__name__)


from . import table_state
from .types import Activity, Location, Role, Staff, StaffAssignment
from .updater import (
    update_location,
    update_staff,
    update_role,
    delete_activities,
    update_assignment,
)
from rotaplanner.edit_activity import edit_activity

import asyncio
import functools
from typing import Self, Literal, cast
import contextlib
from dominate import tags as html
from dominate.document import document
from dominate.util import raw

# rewrite the above code to use the new table state management system with reaktiv signals and async updates

type CellDict = dict[tuple[str, str], list[Activity]]


@reaktiv.Computed
def cells_by_location() -> CellDict:
    cells: CellDict = {}
    for activity in sorted(
        table_state.activities.get().values(), key=lambda a: a.activity_start
    ):
        activity_date = activity.activity_start.isoformat()[:10]
        location_id = activity.location
        cells.setdefault((activity_date, location_id), []).append(
            activity.model_copy(
                update={"cell": (activity_date, location_id), "render_type": "location"}
            )
        )
    logger.info(f"Computed cells_by_location")
    return cells


@reaktiv.Computed
def cells_by_staff() -> CellDict:
    cells: CellDict = {}
    for activity in sorted(
        table_state.activities.get().values(), key=lambda a: a.activity_start
    ):
        activity_date = activity.activity_start.isoformat()[:10]
        assigned_staff_ids = {assn.staff.id for assn in activity.assignments}
        if not assigned_staff_ids:
            cells.setdefault((activity_date, None), []).append(
                activity.model_copy(
                    update={"cell": (activity_date, None), "render_type": "staff"}
                )
            )
        else:
            for staff_id in assigned_staff_ids:
                cells.setdefault((activity_date, staff_id), []).append(
                    activity.model_copy(
                        update={
                            "cell": (activity_date, staff_id),
                            "render_type": "staff",
                        }
                    )
                )
    logger.info(f"Computed cells_by_staff")
    return cells


async def cell_updater(
    table_type: Literal["location", "staff"], window: webview.Window
):
    cells = cells_by_location if table_type == "location" else cells_by_staff
    async for (
        old_activities_all,
        new_activities_all,
    ) in asyncstdlib.itertools.pairwise(reaktiv.to_async_iter(cells)):
        all_keys = set(old_activities_all.keys()) | set(new_activities_all.keys())
        unchanged_cells = set()
        unreordered_cells = set()
        for cell_key in all_keys:
            old_activities_cell: dict[str, Activity] = {
                a.id: a for a in old_activities_all.get(cell_key, [])
            }
            new_activities_cell: dict[str, Activity] = {
                a.id: a for a in new_activities_all.get(cell_key, [])
            }

            if new_activities_cell == old_activities_cell:
                unchanged_cells.add(cell_key)
                continue
            old_order = tuple(old_activities_cell)
            new_order = tuple(new_activities_cell)
            if old_order == new_order:
                unreordered_cells.add(cell_key)
                diff = list(new_activities_cell.values())
            else:
                differ = difflib.SequenceMatcher(a=old_order, b=new_order)
                new_items = []
                for opcode, a0, a1, b0, b1 in differ.get_opcodes():
                    if opcode == "equal":
                        for activity_id in old_order[a0:a1]:
                            new_items.append(new_activities_cell[activity_id])
                    elif opcode == "replace":
                        logger.info(
                            f"Removing activities {','.join(old_order[a0:a1])} from cell {cell_key}"
                        )
                        for activity_id in old_order[a0:a1]:

                            new_items.append(
                                old_activities_cell[activity_id].model_copy(
                                    update={"status": "remove"}
                                )
                            )
                        logger.info(
                            f"Adding activities {','.join(new_order[b0:b1])} to cell {cell_key}"
                        )

                        new_items.extend(
                            new_activities_cell[activity_id].model_copy(
                                update={"status": "add"}
                            )
                            for activity_id in new_order[b0:b1]
                        )
                    elif opcode == "delete":

                        logger.info(
                            f"Removing activities {','.join(old_order[a0:a1])} from cell {cell_key}"
                        )
                        new_items.extend(
                            old_activities_cell[activity_id].model_copy(
                                update={"status": "remove"}
                            )
                            for activity_id in old_order[a0:a1]
                        )
                    if opcode in ("replace", "insert"):
                        logger.info(
                            f"Adding activities {','.join(new_order[b0:b1])} to cell {cell_key}"
                        )
                        new_items.extend(
                            new_activities_cell[activity_id].model_copy(
                                update={"status": "add"}
                            )
                            for activity_id in new_order[b0:b1]
                        )
                diff = new_items

            cell_content = str(
                table_cell(
                    diff,
                )
            )
            cell_id = f"cell--{cell_key[0]}--{cell_key[1]}"
            logger.info(f"Updating cell {cell_id} with content: {cell_content}")
            cell = window.dom.get_element("#" + cell_id)
            cell.empty()
            cell.append(str(cell_content))

        logger.info(
            f"Cell updater for {table_type}: {len(unchanged_cells)} unchanged, {len(unreordered_cells)} unreordered, {len(all_keys - unchanged_cells - unreordered_cells)} changed"
        )


class rota_table_wrapper(html.dom_tag):
    tagname = "rota-table-wrapper"


class TableApi:
    def __init__(self, table_type: Literal["location", "staff"]):
        self.table_type = table_type

    def activity_dropped(self, event):
        logger.info(f"Table dropped event: {event}")
        # Handle the dropped event here, e.g., update the database or state based on the event data
        if self.table_type == "location":
            update_location(event)
        elif self.table_type == "staff":
            update_staff(event)

    def assignment_dropped(self, event):
        logger.info(f"Assignment dropped event: {event}")
        update_assignment(event)

    def role_changed(self, event):
        update_role(event)

    def edit_activity(self, event):
        logger.info(f"Edit activity event: {event}")
        edit_activity(event)

    def delete_activities(self, event):
        logger.info(f"Delete activities event: {event}")
        delete_activities(event)


async def table_window(table_type: Literal["location", "staff"], window_id: str):
    runner = TaskRunner()
    if table_type == "location":
        cells = cells_by_location
        rows = [*table_state.locations(), Location(name="No Location", id=None)]
    elif table_type == "staff":
        cells = cells_by_staff
        rows = [*table_state.staff(), Staff(name="No Staff", id=None)]
    else:
        raise ValueError(f"Invalid table type: {table_type}")
    window_signal = reaktiv.Signal(None)

    cssfile = pathlib.Path(__file__).parent / "assets" / "table.css"
    jsfile = pathlib.Path(__file__).parent / "assets" / "table.js"

    def handle_close():
        runner.abort()

    doc = document(title="RotaPlanner")
    with doc.head:
        html.style(raw(cssfile.read_text()))
        html.script(raw(jsfile.read_text()))
    doc.body.add(
        rota_table_wrapper(
            table(
                dates=table_state.dates(),
                rows=rows,
                cells=cells(),
            )
        )
    )
    logger.info(f"Created table window for {table_type} with window ID {window_id}")
    logger.info(f"Table window HTML: {doc.render()}")
    window = webview.create_window(
        "RotaPlanner",
        html=str(doc),
        js_api=TableApi(table_type),
        width=1200,
        height=800,
    )

    window.events.loaded += lambda: window_signal.set(window)
    window.events.closing += handle_close

    try:

        runner.schedule(cell_updater(table_type, window))
        await runner.run()
    except asyncio.CancelledError:
        logger.info(f"Table window for {table_type} cancelled.")
    finally:
        window.destroy()
