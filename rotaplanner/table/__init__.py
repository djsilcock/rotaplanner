import uuid

import asyncstdlib
import reaktiv

from rotaplanner.app import app
from rotaplanner.table.ui import table, table_cell
from blinker import ANY
import datetime
import pywry
import pathlib
import difflib
from logging import getLogger
from pydantic import BaseModel, Field

logger = getLogger(__name__)


from rotaplanner.app import app

from . import table_state
from .types import Activity, Location, Role, Staff, StaffAssignment

import logging
import asyncio
import functools
from typing import Self, Literal

# rewrite the above code to use the new table state management system with reaktiv signals and async updates


def sort_cells_by_location(cells, tg):
    temp_cells = {}
    for activity in sorted(
        table_state.activities.get().values(), key=lambda a: a.activity_start
    ):
        activity_date = activity.activity_start.isoformat()[:10]
        location_id = activity.location
        temp_cells.setdefault((activity_date, location_id), []).append(activity)
        if (activity_date, location_id) not in cells:
            logger.info(f"Cell {(activity_date, location_id)} is new, adding")
            tg.create_task(cell_updater((activity_date, location_id)))

            if (
                cells[(activity_date, location_id)]
                != temp_cells[(activity_date, location_id)]
            ):
                logger.info(f"Cell {(activity_date, location_id)} changed, updating")
                cells[(activity_date, location_id)] = temp_cells[
                    (activity_date, location_id)
                ]


def sort_cells_by_staff(cells) -> dict[tuple[str, str], list[Activity]]:
    cells: dict[tuple[str, str], list[Activity]] = {}
    for activity in sorted(
        table_state.activities.get().values(), key=lambda a: a.activity_start
    ):
        activity_date = activity.activity_start.isoformat()[:10]
        assigned_staff_ids = {
            assn.staff for role in activity.roles for assn in role.assignments
        }
        if not assigned_staff_ids:
            cells.setdefault((activity_date, None), []).append(activity)
        else:
            for staff_id in assigned_staff_ids:
                cells.setdefault((activity_date, staff_id), []).append(activity)
    return cells


async def cell_updater(cell_key, contents, table_type):
    async for old_activities, new_activities in asyncstdlib.itertools.pairwise(
        reaktiv.to_async_iter(contents)
    ):

        if new_activities == old_activities:
            logger.info(f"Cell {cell_key} unchanged, skipping update")
            continue
        if new_activities != old_activities:
            old_order = tuple(old_activities.keys())
            new_order = tuple(new_activities.keys())
            if old_order == new_order:
                logger.info(f"Cell {cell_key} order unchanged, skipping re-ordering")
                diff = list(new_activities.values())
            else:
                differ = difflib.SequenceMatcher(a=old_order, b=new_order)
                new_items = []
                for opcode, a0, a1, b0, b1 in differ.get_opcodes():
                    if opcode == "equal":
                        for activity_id in old_order[a0:a1]:
                            new_items.append(new_activities[activity_id])
                    elif opcode == "replace":
                        logger.info(
                            f"Removing activities {','.join(old_order[a0:a1])} from cell {cell_key}"
                        )
                        for activity_id in old_order[a0:a1]:

                            new_items.append(
                                old_activities[activity_id].model_copy(
                                    update={"status": "remove"}
                                )
                            )
                        logger.info(
                            f"Adding activities {','.join(new_order[b0:b1])} to cell {cell_key}"
                        )

                        new_items.extend(
                            new_activities[activity_id].model_copy(
                                update={"status": "add"}
                            )
                            for activity_id in new_order[b0:b1]
                        )
                    elif opcode == "delete":

                        logger.info(
                            f"Removing activities {','.join(old_order[a0:a1])} from cell {cell_key}"
                        )
                        new_items.extend(
                            old_activities[activity_id].model_copy(
                                update={"status": "remove"}
                            )
                            for activity_id in old_order[a0:a1]
                        )
                    if opcode in ("replace", "insert"):
                        logger.info(
                            f"Adding activities {','.join(new_order[b0:b1])} to cell {cell_key}"
                        )
                        new_items.extend(
                            new_activities[activity_id].model_copy(
                                update={"status": "add"}
                            )
                            for activity_id in new_order[b0:b1]
                        )
                diff = new_items

            cell_content = str(
                table_cell(
                    cell_key[1],
                    datetime.date.fromisoformat(cell_key[0]),
                    diff,
                    table_type,
                )
            )
            cell_id = f"cell--{cell_key[0]}--{cell_key[1]}"
            logger.info(f"Updating cell {cell_id} with content: {cell_content}")
            app.emit("pywry:set-content", {"id": cell_id, "html": cell_content})


async def table_window_factory(
    table_type: Literal["location", "staff"], window_id: str
):
    if table_type == "location":
        cells = sort_cells_by_location
        rows = table_state.locations
    elif table_type == "staff":
        cells = sort_cells_by_staff
        rows = table_state.staff
    else:
        raise ValueError(f"Invalid table type: {table_type}")
    window_signal = reaktiv.Signal()

    cssfile = pathlib.Path(__file__).parent / "assets" / "table.css"
    jsfile = pathlib.Path(__file__).parent / "assets" / "table.js"

    def handle_close(_):
        logger.info("Table window is closing")

    def handle_table_dropped(event):
        logger.info(f"Table dropped event: {event}")
        # Handle the dropped event here, e.g., update the database or state based on the event data

    window = app.show(
        pywry.HtmlContent(
            html=str(
                table(
                    dates=table_state.dates(),
                    rows=rows(),
                )
            ),
            css_files=[str(cssfile)],
            script_files=[str(jsfile)],
            hot_reload=True,
        ),
        callbacks={
            "pywry:ready": lambda _: window_signal.set(window),
            "pywry:close": handle_close,
            "window:hidden": handle_close,
            "table:dropped": handle_table_dropped,
        },
        label=window_id,
    )

    cell_signals = {}

    async with asyncio.TaskGroup() as tg:

        @reaktiv.Effect
        def create_cell_effects():
            for cell_key in cells.get().keys():
                if cell_key not in cell_signals:
                    cell_signals[cell_key] = reaktiv.Signal([])
                    tg.create_task(
                        cell_updater(cell_key, cell_signals[cell_key], table_type)
                    )
            with reaktiv.batch():
                for cell_key, signal in cell_signals.items():
                    signal.set(cells()[cell_key])

    def make_cell_computed(cell_key):
        @reaktiv.Computed
        def cell_computed():
            cell_activities = cells.get().get(cell_key, [])
            return table_cell(
                cell_key[1],
                datetime.date.fromisoformat(cell_key[0]),
                cell_activities,
                table_type,
            )

    def make_cell_effect(cell_key):
        @reaktiv.Effect
        def cell_effect():
            cell_activities = cells.get().get(cell_key, [])
            cell_content = str(
                table_cell(
                    cell_key[1],
                    datetime.date.fromisoformat(cell_key[0]),
                    cell_activities,
                    table_type,
                )
            )
            cell_id = f"cell--{cell_key[0]}--{cell_key[1]}"
            logger.info(f"Updating cell {cell_id} with content: {cell_content}")
            app.emit("pywry:set-content", {"id": cell_id, "html": cell_content})
