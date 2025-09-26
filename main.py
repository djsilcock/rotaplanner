import asyncio
import uvicorn
from fastapi_version import app

killswitch = asyncio.Event()


async def run_server(server, stop_signal):
    async def wait_for_quit():
        await stop_signal.wait()
        server.should_exit = True

    async def runserver():
        await server.serve()
        stop_signal.set()

    async with asyncio.TaskGroup() as group:
        tsk = group.create_task(runserver())
        tsk2 = group.create_task(wait_for_quit())


async def main():
    config = uvicorn.Config(app=app)
    server = uvicorn.Server(config)
    print("Hello from rotaplanner!")
    async with asyncio.TaskGroup() as group:
        tsk = group.create_task(run_server(server, killswitch))


@app.get("/api/abort")
def abort():
    killswitch.set()


if __name__ == "__main__":

    asyncio.run(main())
