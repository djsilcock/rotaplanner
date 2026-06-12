from rotaplanner.app import app
import pywry
from rotaplanner.table import LocationTableWindow, StaffTableWindow
import logging
import asyncio

class TaskRunner:
    def __init__(self):
        self.ready_event = asyncio.Event()
        self.runner_task = asyncio.create_task(self._run())
    async def add_task(self, coro):
        self.taskgroup.create_task(coro)
    async def _run(self):
        async def run_forever():
            while True:
              await asyncio.sleep(1)
        self.taskgroup=asyncio.TaskGroup()
        self.ready_event.set()
        async with self.taskgroup:
            self.taskgroup.create_task(run_forever())
            self.ready_event.set()
    @classmethod
    async def create(cls):
        self = cls()
        await self.ready_event.wait()  # Wait until the runner is ready
        return self


async def show_table():
    l = LocationTableWindow()
    await l.show()

from pywry import (
    HtmlContent,
    PyWry,
    MenuConfig,
    MenuItemConfig,
    CheckMenuItemConfig,
    SubmenuConfig,
    PredefinedMenuItemConfig,
    PredefinedMenuItemKind
)


def main_window(create_task):
    # ── Define handlers FIRST ────────────────────────────────────────
    def on_new(data, event_type, label):
        app.show(HtmlContent(html="<h1>Untitled</h1>"), title="New File")


    def on_open(data, event_type, label):
        create_task(show_table())


    def on_quit(data, event_type, label):
        app.destroy()


    # ── Build menu items — every item gets its handler inline ────────
    file_menu = SubmenuConfig(
        id="file",
        text="File",
        items=[
            MenuItemConfig(id="new", text="New", handler=on_new, accelerator="CmdOrCtrl+N"),
            MenuItemConfig(
                id="open", text="Open", handler=on_open, accelerator="CmdOrCtrl+O"
            ),
            PredefinedMenuItemConfig(kind_name=PredefinedMenuItemKind.SEPARATOR),
            MenuItemConfig(
                id="quit", text="Quit", handler=on_quit, accelerator="CmdOrCtrl+Q"
            ),
        ],
    )

    edit_menu = SubmenuConfig(
        id="edit",
        text="Edit",
        items=[
            PredefinedMenuItemConfig(kind_name=PredefinedMenuItemKind.CUT),
            PredefinedMenuItemConfig(kind_name=PredefinedMenuItemKind.COPY),
            PredefinedMenuItemConfig(kind_name=PredefinedMenuItemKind.PASTE),
        ],
    )

    menu = MenuConfig(id="main-menu", items=[file_menu, edit_menu])

    # ── Show with menu — handlers are wired BEFORE the window appears
    handle = app.show("<h1>Hello Menu!</h1>", menu=menu)



async def main():
    runner = await TaskRunner.create()
    loop = asyncio.get_running_loop()
    def create_task(coro):
        loop.call_soon_threadsafe(lambda: runner.taskgroup.create_task(coro))
    runner.runner_task  # Ensure the runner task is started
    await show_table()
    #main_window(create_task)
    await asyncio.sleep(10)
    runner.runner_task.cancel()

    print("Location table is stopped")


asyncio.run(main())
