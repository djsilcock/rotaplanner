from rotaplanner.app import app
import pywry
from rotaplanner.ui.table.components.table import render_table
import logging

app.show(
    pywry.HtmlContent(
        html=str(render_table("staff")),
        css_files=["./rotaplanner/ui/table/components/table.css"],
        script_files=["./rotaplanner/ui/table/components/table.js"],
        hot_reload=True,
    ),
    callbacks={
        "table:dropped": lambda event: logging.info(f"Table dropped event: {event}"),
    },
)
app.alert("Welcome to RotaPlanner!")
app.block()
