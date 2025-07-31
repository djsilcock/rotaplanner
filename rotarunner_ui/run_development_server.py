# runs the vite development server
import os
from winpty import PtyProcess
import threading
import time
import re
import queue
import asyncio
import pathlib
import subprocess


def de_ansify(text):
    """Remove ANSI escape sequences from a string."""
    ansi_escape = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
    return ansi_escape.sub("", text)


def get_output(process: PtyProcess, queue: queue.Queue):
    """Read output from the process."""
    while process.isalive():
        line = process.readline()
        match = re.search(r"(http.+:\d+)", de_ansify(line))
        print(line)
        if match:
            queue.put(match.group(1))


async def run_vite_dev_server2():
    proc = PtyProcess.spawn(
        "npm run dev", cwd=str(pathlib.Path(__file__, "..").resolve())
    )
    q = queue.Queue()
    threading.Thread(target=get_output, args=(proc, q)).start()
    while q.empty():
        await asyncio.sleep(0.1)
    devserver_url = q.get()
    print("Vite development server started at:", devserver_url)
    yield {"devserver": devserver_url}
    proc.write("q\r\n")


def generate_types():
    """Generate types for the application."""
    subprocess.run(
        "npm run generate-client",
        shell=True,
        check=True,
        cwd=str(pathlib.Path(__file__, "..").resolve()),
    )
    print("Types generated successfully.")


def build_frontend():
    """Build the frontend application."""
    subprocess.run(
        "npm run build",
        shell=True,
        check=True,
        cwd=str(pathlib.Path(__file__, "..").resolve()),
    )
    print("Frontend built successfully.")
