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
        print(f'creating signal:{name or "(anonymous)"}')
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

    async def dispatch_corofunction(self, func, threaded, sender, kwargs):
        "wrap coroutine function to work async"
        if asyncio.iscoroutinefunction(func):
            return (sender, await func(sender, **kwargs))
        elif threaded:
            return (sender, await asyncio.to_thread(func, sender, **kwargs))
        else:
            return (sender, func(sender, **kwargs))

    def _send(self, sender, dispatcher, kwargs):
        output = []
        print(self.name or '<anonymous>')
        for func in self.listeners:
            try:
                print('   ', self.name,end='')
                result = dispatcher(func, sender, kwargs)
                output.append(result)
                print(result)
            except Exception as e:
                raise
        print('done')
        return output

    def send(self, *args, _threaded=False, **kwargs):
        "Send message to all attached receivers"
        if self.has_coroutine_listeners or _threaded:
            return asyncio.run(self.send_async(*args, _threaded=_threaded, **kwargs))
        def dispatcher(func, sender, kwargs):
            return (func, func(sender, **kwargs))
        return self._send(self.get_sender(args), dispatcher, kwargs)

    async def send_async(self, *args, _threaded=True, **kwargs):
        "Send message asynchronously"
        sender = self.get_sender(args)
        if self.has_coroutine_listeners or _threaded:
            def dispatcher(func, sender, kwargs):
                return self.dispatch_corofunction(func, _threaded, sender, **kwargs)
            return await asyncio.gather(*self._send(sender, dispatcher, kwargs))
        return self.send(*args, **kwargs)
