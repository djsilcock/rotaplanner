import asyncio


log_queue=asyncio.Queue()


def log(message):
    log_queue.put_nowait(str(message))