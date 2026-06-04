import webview
from .api import EditActivityApi


def create_window(activity_id: str):
    api = EditActivityApi()
    window = webview.create_window(
        "Woah dude!",
        "http://localhost:3000/#/edit-activity",
        js_api=api,
        menu=[],
    )
    api._window = window
    window.state.activityId = activity_id
    return window
