import webview
from .menu import menu
from .api import TableApi
from ...signals import activity_updated
from blinker import ANY
import datetime

from logging import getLogger

logger = getLogger(__name__)


def create_window():

    api = TableApi()
    window = webview.create_window(
        "Rotarunner", "http://localhost:3000", js_api=api, menu=menu
    )
    window.state += lambda *r: logger.info(repr(r))
    window.state.tableType = "location"
    window.state.version = 1

    @activity_updated.connect_via(ANY, weak=False)
    def on_activity_updated(sender, **kwargs):
        logger.info(
            "Activity updated signal received in table component, updating version"
        )
        print("logging...")
        logger.info("previous version %s", window.state.version)
        window.state.version = datetime.datetime.now().timestamp()

    def on_closed():
        logger.info("Table window closed, disconnecting signal")
        activity_updated.disconnect(on_activity_updated)
        while api._activity_windows:
            _, window = api._activity_windows.popitem()
            window.destroy()

    window.events.closed += on_closed

    return window
