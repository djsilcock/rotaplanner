import logging
from queue import Queue
from threading import Thread
import webview
from rotaplanner.table import create_window
import json

logger = logging.getLogger(__name__)


logger_html = """
<html>
<head>
    <style>
        body {
            font-family: monospace;
            white-space: pre;
        }
    </style>
    <script>
        function addLog({header,message}) {
            const logContainer = document.getElementById('log');
            const logEntry = document.createElement('details');
            const logSummary = document.createElement('summary');
            logSummary.textContent = header;
            logEntry.appendChild(logSummary);
            const logContent = document.createElement('div');
            logContent.textContent = message;
            logEntry.appendChild(logContent);
            logContainer.appendChild(logEntry);
            console.log(header + " - " + message);
        }
    </script>
</head>
<body>
    <div id="log"></div>
</body>
</html>
"""


def redirect_logs_to_webview(log_queue):
    class WebViewLogHandler(logging.Handler):
        log_level = logging.DEBUG

        def emit(self, record: logging.LogRecord):
            try:
                log_entry = self.format(record)
                header = f"{record.levelname} - {record.name}"
                log_queue.put((header, log_entry))
            except Exception as e:
                print(
                    f"Error in log handler for {record.name}: {e.__class__.__name__}: {e}"
                )

    handler = WebViewLogHandler()
    formatter = logging.Formatter("%(asctime)s - %(message)s")
    handler.setFormatter(formatter)
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.DEBUG)


def main():
    create_window()
    log_window = webview.create_window("Log", html=logger_html)
    log_queue = Queue()
    log_window.events.loaded += lambda: redirect_logs_to_webview(log_queue)

    def process_log_queue():
        while True:
            header, log_entry = log_queue.get()
            log_window.run_js(
                f"addLog({json.dumps({'header':header, 'message':log_entry})})"
            )

    Thread(target=process_log_queue, daemon=True).start()
    webview.start(debug=True)


if __name__ == "__main__":
    import os
    import sys

    print(os.path.dirname(os.path.realpath(sys.argv[0])))
    main()
