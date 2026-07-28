import webview
from rotaplanner.utils import TaskRunner
from dominate import tags as html
from dominate.document import document
from pydantic import BaseModel, Field
from ..form_inputs import SearchableMultiSelect
from ..components.assets import collect_assets
import logging

logger = logging.getLogger(__name__)


class ActivityModel(BaseModel):
    name: str
    location: str
    activity_start: str
    activity_finish: str
    role_id: str | None = None
    staff_id: str | None = None
    cell: tuple[str, str] | None = None
    render_type: str | None = None


def edit_activity(activity_id: str):
    """
    Opens the edit activity window for the given activity ID.
    """
    logger.info(f"Opening edit activity window for activity ID: {activity_id}")
    document_html = document(title="Edit Activity")
    with collect_assets(document_html):
        with document_html.body:
            html.h1("Edit Activity")
            html.div(f"Activity ID: {activity_id}")
            # Here you would add the form inputs for editing the activity
            # For example, you could use SearchableMultiSelect for staff selection
            html.div(
                SearchableMultiSelect(
                    name="staff",
                    label_text="Staff",
                    options=[
                        {"label": "Staff 1", "value": "staff_1"},
                        {"label": "Staff 2", "value": "staff_2"},
                    ],
                ).render()
            )
            html.div(
                SearchableMultiSelect(
                    name="role",
                    label_text="Role",
                    options=[
                        {"label": "Role 1", "value": "role_1"},
                        {"label": "Role 2", "value": "role_2"},
                    ],
                ).render()
            )
            html.button("Save Changes", id="save-button")
    webview.create_window(
        "Edit Activity",
        html=document_html.render(),
        width=600,
        height=400,
        resizable=True,
        fullscreen=False,
    )
