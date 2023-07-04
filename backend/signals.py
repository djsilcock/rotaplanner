"Implement pub-sub signalling"

import asyncio
from inspect import signature
from typing import Callable

namespace = {}


def signal(name=None):
    "create or retrieve named signal"
    if name is None:
        return Signal()
    else:
        return namespace.setdefault(name, Signal(name))

def run_async(coro):
    try:
        loop=asyncio.get_running_loop()
        task=loop.create_task(coro)
        while not task.done():
            loop._run_once()
        return task.result()
    except:
        return asyncio.run(coro)
class Signal:
    def __init__(self,name=None):
        self.name=name
        self.sync_handlers=[]
        self.async_handlers=[]
        self.mandatory_args=set()
    def wrap_handler(self,func:Callable):
        sig=signature(func)
        param_names=[]
        for name,param in sig.parameters.items():
            if param.kind in (param.POSITIONAL_ONLY,param.VAR_POSITIONAL):
                raise TypeError('positional-only arguments are not allowed in handlers')
            if param.kind==param.VAR_KEYWORD:
                def pass_all_params(func,params):
                    return func(**params)
                return pass_all_params
            if param.default==param.empty:
                self.mandatory_args.add(name)
            param_names.append(name)
        def pass_selected_params(func,params):
            picked_params={name:params[name] for name in param_names if name in params}
            return func(**picked_params)
        return pass_selected_params
    def check_signature(self,kwargs):
        if not self.mandatory_args.issubset(set(kwargs)):
            raise TypeError(f'parameters ({",".join(self.mandatory_args-set(kwargs))}) are missing')
    def connect(self,func):
        if asyncio.iscoroutinefunction(func):
            if func not in self.async_handlers:
                self.async_handlers.append((self.wrap_handler(func),func))
        else:
            if func not in self.sync_handlers:
                self.sync_handlers.append((self.wrap_handler(func),func))
        return func

    def emit(self,**kwargs):
        self.check_signature(kwargs)
        if len(self.async_handlers)>0:
            return run_async(self.emit_async(**kwargs))
        return [wrapper(handler,kwargs) for wrapper,handler in self.sync_handlers]
    async def emit_async_generator(self,**kwargs):
        self.check_signature(kwargs)        
        for wrapper,handler in self.sync_handlers:
            await asyncio.sleep(0)
            yield wrapper(handler,kwargs)
        for wrapper,handler in self.async_handlers:
            yield await wrapper(handler,kwargs)

    async def emit_concurrent_generator(self,**kwargs):
        self.check_signature(kwargs)
        async_handlers=[asyncio.create_task(w(h,kwargs)) for w,h in self.async_handlers]
        for h in self.sync_handlers:
            await asyncio.sleep(0)
            yield h(**kwargs)
        for r in asyncio.as_completed(async_handlers):
            yield await r
    async def emit_async(self,**kwargs):
        return [i async for i in self.emit_async_generator(**kwargs)]
    async def emit_concurrent(self,**kwargs):
        return [i async for i in self.emit_concurrent_generator(**kwargs)]
