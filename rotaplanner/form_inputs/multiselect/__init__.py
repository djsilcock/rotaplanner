from dominate.tags import div, label, select, option, span, ul, li, input_, script
from dominate.util import raw
from dominate.svg import svg, path
import uuid
import pathlib
from ...components.assets import register_asset


class SearchableMultiSelect:
    """
    A reusable, fully scoped, searchable multi-select component.
    Generates isolated HTML/JS markup with custom standard CSS class styling.
    Seamlessly integrates with native <form> and FormData.
    """

    cssfile = pathlib.Path(__file__).parent / "multiselect.css"
    jsfile = pathlib.Path(__file__).parent / "multiselect.js"

    def __init__(
        self,
        name,
        label_text,
        options,
        placeholder="Select options...",
        id_prefix="multiselect",
        value=None,
    ):
        self.name = (
            name  # The name attribute used for standard form submissions (FormData)
        )
        self.label_text = label_text
        self.options = (
            options  # List of dicts, e.g., [{"value": "py", "label": "Python"}]
        )
        self.placeholder = placeholder
        self.value = value if value is not None else []  # Pre-selected values
        self.uid = f"{id_prefix}_{uuid.uuid4().hex[:8]}"
        register_asset("multiselect", js=self.jsfile, css=self.cssfile)

    def render(self):
        # Create a container block unique to this component instance
        container = div(
            id=f"container-{self.uid}", _class="ms-container", data_uid=self.uid
        )

        with container:
            # 1. Label
            label(self.label_text, cls="ms-label")

            # 2. Native hidden select element to back standard HTML Form and FormData
            hidden_select = select(
                name=self.name,
                id=f"native-select-{self.uid}",
                multiple=True,
                _class="ms-hidden-select",
            )
            with hidden_select:
                for opt in self.options:
                    option(
                        opt["label"],
                        value=opt["value"],
                        selected=opt["value"] in self.value,
                    )

            # 3. Interactive Custom Trigger display box
            with div(id=f"trigger-{self.uid}", _class="ms-trigger"):
                # Placeholder
                span(
                    self.placeholder,
                    id=f"placeholder-{self.uid}",
                    _class="ms-placeholder",
                )

                # Tag Pills render target
                div(id=f"tags-{self.uid}", _class="ms-tags")

                # Chevron Arrow Container
                with div(_class="ms-chevron-wrapper"):
                    with svg(
                        _class="ms-chevron-icon",
                        id=f"chevron-{self.uid}",
                        fill="none",
                        stroke="currentColor",
                        viewBox="0 0 24 24",
                    ):
                        path(
                            stroke_linecap="round",
                            stroke_linejoin="round",
                            stroke_width="2.5",
                            d="M19 9l-7 7-7-7",
                        )

            # 4. Dropdown Panel Container
            with div(id=f"panel-{self.uid}", _class="ms-panel"):
                # Filter Search Container
                with div(_class="ms-search-container"):
                    with div(_class="ms-search-wrapper"):
                        with div(_class="ms-search-icon-wrapper"):
                            with svg(
                                _class="ms-search-icon",
                                fill="none",
                                stroke="currentColor",
                                viewBox="0 0 24 24",
                            ):
                                path(
                                    stroke_linecap="round",
                                    stroke_linejoin="round",
                                    stroke_width="2.5",
                                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z",
                                )
                        input_(
                            type="text",
                            id=f"search-{self.uid}",
                            placeholder="Type to search...",
                            _class="ms-search-input",
                        )

                # Scrollable Options List
                with ul(id=f"options-{self.uid}", _class="ms-options custom-scrollbar"):
                    for opt in self.options:
                        with li(
                            _class="ms-option",
                            data_value=opt["value"],
                            data_name=opt["label"],
                        ):
                            # Custom check box box-indicator
                            with span(_class="ms-checkbox-indicator"):
                                with svg(
                                    _class="ms-check-mark hidden",
                                    fill="none",
                                    stroke="currentColor",
                                    stroke_width="3",
                                    viewBox="0 0 24 24",
                                ):
                                    path(
                                        stroke_linecap="round",
                                        stroke_linejoin="round",
                                        d="M4.5 12.75l6 6 9-13.5",
                                    )

                            span(opt["label"], _class="ms-option-label")

                    # Empty template for fallback
                    li(
                        "No matches found",
                        id=f"no-results-{self.uid}",
                        _class="ms-no-results ms-hidden",
                    )

            # 5. Scoped Controller Script (IIFE ensures no global namespace collisions)
            with script():
                raw(f"setupDropdown('{self.uid}');")

        return container
