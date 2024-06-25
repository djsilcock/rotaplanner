import asyncio


thisvar=[0]

async def timeout(timeout,message,cond:asyncio.Condition):
    async with cond:
        print(f'I have the lock:{message}')
        print(f'barrier:{await cond.wait_for(lambda:thisvar[0]>timeout)} for {message}')
    
    print(message)

async def taskgroupinner(cond):
    try:    
        async with asyncio.TaskGroup() as tg:
            tg.create_task(timeout(2,'After 2s',cond))
            tg.create_task(timeout(6,'After 6s',cond))
            tg.create_task(timeout(4,'After 4s',cond))
    except asyncio.CancelledError:
        print('outer task was cancelled')
        raise

async def timer(cond):
    while True:
        await asyncio.sleep(1)
        async with cond:
            print ('timer has lock')
            thisvar[0]+=1
            cond.notify_all()

async def taskgroupouter():
    cond=asyncio.Condition()
    timertask=asyncio.create_task(timer(cond))
    tsk=asyncio.create_task(taskgroupinner(cond))
    await tsk    
    timertask.cancel()
    print (f'done? {tsk.cancelled()}')

asyncio.run(taskgroupouter())
