import webview
from webview.menu import Menu, MenuAction


def navigate_to(path):
    current_window = webview.active_window()
    if current_window:
        current_window.run_js(f'window.navigateTo("{path}");')


def to_do():
    current_window = webview.active_window()
    if current_window:
        current_window.run_js('alert("To do!");')


def set_state(**values):
    current_window = webview.active_window()
    if current_window:
        for key, value in values.items():
            setattr(current_window.state, key, value)


menu = [
    Menu(
        "Rota",
        [
            MenuAction("By Person", lambda: set_state(tableType="staff")),
            MenuAction("By Location", lambda: set_state(tableType="location")),
            MenuAction("Quit", lambda: webview.active_window().destroy()),
        ],
    ),
    Menu(
        "Manage",
        [
            MenuAction("Activity templates", to_do),
            MenuAction("Supply templates", to_do),
            MenuAction("Rota Solver", to_do),
            MenuAction("Import from CLW", to_do),
        ],
    ),
]
