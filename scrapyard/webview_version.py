import webview

import contextlib
import contextvars
import re

import webview.dom
import uuid

current_element = contextvars.ContextVar("current_element", default=None)
current_window = contextvars.ContextVar[webview.Window]("current_window", default=None)


def on_ready(window: webview.Window):
    # This function will be called when the window is ready
    print("WebView is ready!")
    el = window.dom.create_element("<h1>WebView Version</h1>")
    main = window.dom.create_element("<p>This is a simple WebView application.</p>")
    tbl = main.append("<table></table>")
    tb = tbl.append("<tbody></tbody>", webview.dom.ManipulationMode.LastChild)
    cells = {}
    tbc = []
    for row in range(100):
        tr = []
        for col in range(100):

            tr.append(
                f"<td data-date={col} data-name={col} data-pywebview-id={uuid.uuid4()}>...</td>"
            )
        tb.append(f"<tr>{''.join(tr)}</tr>", webview.dom.ManipulationMode.LastChild)
    #
    window.run_js(
        """ 
            const cache=new Map();   
            const io=new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const nodeId = pywebview._getNodeId(entry.target);
                    console.log('Element is in view:', nodeId);
                    if (!cache.has(nodeId)) {
                    window.pywebview.api.getElement(nodeId).then(function(val) {
                        cache.set(nodeId, val);
                        entry.target.innerText = val;
                    })};
                } else {
                    const nodeId = pywebview._getNodeId(entry.target);
                    console.log('Element is out of view:', nodeId);
                }
            });
            
            });
            document.querySelectorAll('td').forEach(cell => {
                io.observe(cell);
                })


            
        """
    )
    print("Cells:", cells)

    def on_click(e):
        print("Element clicked:", e["target"]["attributes"]["data-pywebview-id"])
        el = window.dom.get_element(
            f'[data-pywebview-id="{e["target"]["attributes"]["data-pywebview-id"]}"]'
        )
        el.style["background-color"] = "red"

    window.run_js(
        """
    const cells = document.querySelectorAll('td');
    cells.forEach(cell => {
        cell.addEventListener('click', function() {
            cell.style.backgroundColor = 'red';
        });
    });
"""
    )


def main():
    window = webview.create_window("WebView Version")

    @window.expose
    def getElement(node_id):
        print("Get element:", node_id)
        return node_id

    webview.start(func=on_ready, args=window, debug=True)


if __name__ == "__main__":
    main()
