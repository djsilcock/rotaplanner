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

class Signal:
    def __init__(self,name=None):
        self.name=name
        self.sync_handlers=[]
        self.async_handlers=[]
        self.mandatory_args=set()
    def _wrap_handler(self,func:Callable):
        "inspect handler and generate wrapper"
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
    def _check_signature(self,kwargs):
        "check signature of send call"
        if not self.mandatory_args.issubset(set(kwargs)):
            raise TypeError(f'parameters ({",".join(self.mandatory_args-set(kwargs))}) are missing')
    def connect(self,func):
        "Register a listener"
        if asyncio.iscoroutinefunction(func):
            if func not in self.async_handlers:
                self.async_handlers.append((self._wrap_handler(func),func))
        else:
            if func not in self.sync_handlers:
                self.sync_handlers.append((self._wrap_handler(func),func))
        return func

    def _send(self,**kwargs):
        "Call registered handlers"
        self._check_signature(kwargs)
        if len(self.async_handlers)>0:
            raise TypeError('cannot run async handler synchronously')
        return [wrapper(handler,kwargs) for wrapper,handler in self.sync_handlers]
    def send(self,**kwargs):
        return list(self._send(**kwargs))
    
    async def async_generator(self,**kwargs):
        "Asynchronously iterate handlers"
        self._check_signature(kwargs)        
        for wrapper,handler in self.sync_handlers:
            await asyncio.sleep(0)
            yield wrapper(handler,kwargs)
        for wrapper,handler in self.async_handlers:
            yield await wrapper(handler,kwargs)

    async def concurrent_generator(self,**kwargs):
        "Call handlers concurrently and iterate responses"
        self._check_signature(kwargs)
        for handler in self.sync_handlers:
            await asyncio.sleep(0)
            yield handler(**kwargs)
        async_handlers=[asyncio.create_task(wrapper(handler,kwargs)) for wrapper,handler in self.async_handlers]
        for result in asyncio.as_completed(async_handlers):
            yield await result
    async def send_async(self,**kwargs):
        "Call handlers asynchronously"
        return [i async for i in self.async_generator(**kwargs)]
    async def send_concurrent(self,**kwargs):
        "Call handlers concurrently"
        return [i async for i in self.concurrent_generator(**kwargs)]
    def first(self,**kwargs):
        for r in self._send(**kwargs):
            if r is not None:
                return r
    async def first_async(self,**kwargs):
        async for r in self.async_generator(**kwargs):
            if r is not None:
                return r
            

