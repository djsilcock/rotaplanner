import uuid

import webview
from webview.menu import Menu, MenuAction, MenuSeparator

from rotaplanner.table import table_window
import logging
import asyncio
import janus
import threading
from typing import Optional
from dominate import tags as html
from dominate.document import document


import json

from rotaplanner.utils import TaskRunner


async def show_location_table(*_):
    await table_window("location", uuid.uuid4().hex)


async def show_staff_table(*_):
    await table_window("staff", uuid.uuid4().hex)


runner = TaskRunner()


def logger_html():
    html_doc = document(title="RotaPlanner")
    with html_doc.head:
        html.style("""
            body {
                font-family: monospace;
                white-space: pre;
            }
            """)
    with html_doc.body:
        with html.div(
            id="container",
            cls="pywry-scroll-container",
            style="height: 100vh; width: 80vw; overflow: auto;",
        ):
            html.div(id="log")
    return str(html_doc)


def log_fragment(header, message):
    log_entry = html.details()
    with log_entry:
        html.summary(header)
        html.div(message)
    return str(log_entry)


def main_window():
    # ── Define handlers FIRST ────────────────────────────────────────
    async def on_new(*_):
        webview.create_window("New File", html="<h1>Untitled</h1>")

    def on_quit(*_):
        runner.abort()
        if webview.windows:
            webview.windows[0].destroy()

    # Build menu items using pywebview menu primitives.
    file_menu = Menu(
        title="File",
        items=[
            MenuAction("New", runner.wrap_callback(on_new)),
            MenuAction(
                "Open Location Table", runner.wrap_callback(show_location_table)
            ),
            MenuAction("Open Staff Table", runner.wrap_callback(show_staff_table)),
            MenuSeparator(),
            MenuAction("Quit", on_quit),
        ],
    )

    edit_menu = Menu(
        title="Edit",
        items=[],
    )

    menu = [file_menu, edit_menu]

    window = webview.create_window(
        "RotaPlanner",
        html=logger_html(),
        menu=menu,
    )
    window.events.closed += on_quit
    return window


logger = logging.getLogger(__name__)

log_queue = janus.Queue()
shutdown_event = threading.Event()


def redirect_logs_to_webview():
    class WebViewLogHandler(logging.Handler):
        log_level = logging.DEBUG

        def emit(self, record: logging.LogRecord):
            try:
                log_entry = self.format(record)
                header = f"{record.levelname} - {record.name}"
                log_queue.sync_q.put((header, log_entry))
            except Exception as e:
                print(
                    f"Error in log handler for {record.name}: {e.__class__.__name__}: {e}"
                )

    handler = WebViewLogHandler()
    formatter = logging.Formatter("%(asctime)s - %(message)s")
    handler.setFormatter(formatter)
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.DEBUG)


async def process_log_queue(window: webview.Window):
    while True:
        item: Optional[tuple[str, str]] = await log_queue.async_q.get()
        if item is None:
            break
        header, log_entry = item
        window.dom.get_element("#log").append(log_fragment(header, log_entry))


def start_background_tasks(window: webview.Window):
    runner.schedule(process_log_queue(window))
    asyncio.run(runner.run())


def main():
    # ── Show the main window with menu ───────────────────────────────
    window = main_window()
    redirect_logs_to_webview()
    webview.start(start_background_tasks, args=(window,), debug=True)
    runner.abort()


main()
