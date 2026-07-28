from dominate.tags import script, style
from dominate.util import raw
from pathlib import Path
from contextlib import contextmanager

from contextvars import ContextVar
from pathlib import Path

js_context: ContextVar[dict[str, Path]] = ContextVar("js_context", default={})
css_context: ContextVar[dict[str, Path]] = ContextVar("css_context", default={})


@contextmanager
def collect_assets(document_node):
    """
    Context manager to collect JS and CSS assets from form input components.
    """

    # Initialize new contexts for this block
    js_reset = js_context.set({})
    css_reset = css_context.set({})

    try:
        yield  # Execute the block of code within this context
    finally:
        # Collect the assets from the current context
        collected_js = js_context.get()
        collected_css = css_context.get()

        # Restore the old context
        js_context.reset(js_reset)
        css_context.reset(css_reset)

        # Add collected assets to the document node
        if collected_css:

            for css in collected_css.values():
                document_node.head.add(style(raw(css.read_text())))

        if collected_js:

            for js in collected_js.values():
                document_node.head.add(script(raw(js.read_text())))


def register_asset(name, js: Path = None, css: Path = None):
    """
    Register JS and/or CSS assets for the current context.
    """
    if js:
        current_js = js_context.get()
        current_js[name] = js
        js_context.set(current_js)

    if css:
        current_css = css_context.get()
        current_css[name] = css
        css_context.set(current_css)
