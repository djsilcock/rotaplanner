
import contextvars
import asyncio

async def main():
    async def innerwait():
        try:
            print('innerwait running')
            await asyncio.sleep(10)
        finally:
            print('innerwait exiting')
    async def wait():
        try:
            print('wait is running')
            await innerwait()
            print('wait was successful')
        finally:
            print('wait is exiting')
    async def wait2(tsk):
        print('wait2 is running')
        await asyncio.sleep(5)
        tsk.cancel()
    tsk=asyncio.create_task(wait())
    tsk2=asyncio.create_task(wait2(tsk))
    try:
        await tsk
    except asyncio.CancelledError:
        print('task was cancelled')
asyncio.run(main())

