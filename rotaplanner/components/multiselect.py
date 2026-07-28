from dominate.tags import dom_tag
from .assets import register_asset
import uuid
from pathlib import Path


class multiselect(dom_tag):
    tagname = "searchable-multiselect"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        register_asset(
            "multiselect",
            js=Path(__file__).parent / "multiselect.js",
            css=Path(__file__).parent / "multiselect.css",
        )
