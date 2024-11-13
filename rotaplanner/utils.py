import inspect


def discard_extra_kwargs(fn, kwargs={}, **_kwargs):

    kwargs = {**kwargs, **_kwargs}
    kwargs.update(_kwargs)
    sig = inspect.signature(fn)
    new_kwargs = {}
    for p in sig.parameters.values():
        if p.kind == inspect.Parameter.VAR_KEYWORD:
            return fn(**kwargs)
        if p.name in kwargs:
            new_kwargs[p.name] = kwargs[p.name]
    return fn(**new_kwargs)
