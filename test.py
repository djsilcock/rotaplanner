import asyncio

async def coro1():
    try:
        print ('coro1 running')
        await asyncio.sleep(10)
        print('coro1 finished')
    except asyncio.CancelledError:
        print('coro1 aborted')
        raise

async def coro2():
    try:
        print ('coro2 running')
        await asyncio.create_task(coro1())
        print('coro2 finished')
    except asyncio.CancelledError:
        print('coro2 aborted')
        raise

async def coro3():
    try:
        print ('coro3 running')
        await asyncio.create_task(coro2())
        print('coro3 finished')
    except asyncio.CancelledError:
        print('coro3 aborted')
        raise
        
async def coro4():
    task=asyncio.create_task(coro3())
    await asyncio.sleep(3)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    
asyncio.run(coro4())