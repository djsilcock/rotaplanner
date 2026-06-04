import pywry
import logging

logging.basicConfig(level=logging.DEBUG)

app = pywry.PyWry(
    title="RotaPlanner",
    theme=pywry.ThemeMode.LIGHT,
    settings=pywry.PyWrySettings(window={"resizeable": True}),
    mode=pywry.WindowMode.MULTI_WINDOW,
)
