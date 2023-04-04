"Implement pub-sub signalling"

import asyncio
from functools import partial

namespace = {}


def signal(name=None):
    "create or retrieve named signal"
    if name is None:
        return Signal()
    else:
        return namespace.setdefault(name, Signal(name))


class Signal:
    "Signal class. Use signal() factory function to create"
    def __init__(self, name=None):
        self.listeners = []
        self.name = name
        self.has_coroutine_listeners = False

    def connect(self, func):
        "connect receiver to signal"
        if asyncio.iscoroutinefunction(func):
            self.has_coroutine_listeners = True
        if func not in self.listeners:
            self.listeners.append(func)

    def get_sender(self, maybe_sender):
        "extract sender from call"
        if len(maybe_sender) == 1:
            sender = maybe_sender[0]
        elif len(maybe_sender) == 0:
            sender = None
        else:
            raise TypeError('Only one positional argument allowed')
        return sender

    def wrap_corofunction(self, func, threaded=False):
        "wrap coroutine function to work async"
        if asyncio.iscoroutinefunction(func):
            def asyncwrapper(sender, **kwargs):
                return asyncio.create_task(func(sender, **kwargs))
            return asyncwrapper
        elif threaded:
            def threaded_wrapper(sender, **kwargs):
                return asyncio.to_thread(func, sender, **kwargs)
            return threaded_wrapper
        else:
            async def wrapper(sender, **kwargs):
                return func(sender, **kwargs)
            return wrapper

    def _send(self, sender, wrapper, kwargs):
        output=[]
        print(self.name or '<anonymous>')
        for func in self.listeners:
            try:
                print ('   ',self.name,func,end='')
                result=wrapper(func)(sender, **kwargs)
                output.append((func, result) )
                print(output[-1][1])
            except Exception as e:
                output.append((func,e))
        print('done')
        return output

    def send(self, *args, _mode='sync', **kwargs):
        "Send message to all attached receivers"
        assert _mode in ('sync', 'async', 'thread')
        if _mode == 'async':
            return self.send_async(*args, **kwargs)
        if self.has_coroutine_listeners or _mode == 'thread':
            return asyncio.run(self.send_async(*args, _mode=_mode, **kwargs))
        return self._send(self.get_sender(args), lambda x: x, kwargs)

    async def send_async(self, *args, _mode='async', **kwargs):
        "Send message asynchronously"
        assert _mode in ('sync', 'async', 'thread')
        sender = self.get_sender(args)
        if self.has_coroutine_listeners:
            futures = self._send(sender, partial(
                self.wrap_corofunction, threaded=(_mode == 'thread')), kwargs)
            return [(l, await f) for l, f in futures]
        return self._send(sender, lambda x: x, kwargs)
