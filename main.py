import asyncio
from new_rotaplanner.ui import app

killswitch = asyncio.Event()


@app.get("/api/abort")
def abort():
    killswitch.set()


if __name__ == "__main__":
    app.run(use_reloader=True, debug=True)
