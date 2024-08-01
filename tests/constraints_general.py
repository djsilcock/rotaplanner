
def test_general():
    import constraints
    assert constraints is not None

import contextlib
import pytest
import pytest_asyncio
from backend.solver import async_solver_ctx
from old.constraint_ctx import Signal,ConstraintContext
import asyncio

def test_sync_signal():
    signal1=Signal()
    @signal1.connect
    def myfunc(hello):
        return ('myfunc1',hello)
    @signal1.connect
    def myfunc2(hello):
        return ('myfunc2',hello)
    signal1.send(hello='world')
    with pytest.raises(TypeError):
        signal1.send(bar='baz')

@pytest.mark.asyncio
async def test_async_signal():
    signal2=Signal()
    @signal2.connect
    async def myfunc3(hello):
        await asyncio.sleep(2)
        return ('myfunc3',hello)
    @signal2.connect
    async def myfunc4(world):
        await asyncio.sleep(1)
        return ('myfunc4',world)
    


    async def emitter():
        with pytest.raises(TypeError):
            signal2.send(hello='async',world='flat')
        await signal2.send_async(hello='async',world='world')
        await signal2.send_concurrent(hello='concurrent',world='world')
        async for s in signal2.async_generator(hello='async gen',world='world'):
            pass
        async for s in signal2.concurrent_generator(hello='concurrent gen',world='world'):
            pass
            

    await emitter()

def test_constraintctx():
    ctx=ConstraintContext(99)
    ctx.otherattrib=77
    with pytest.raises(TypeError):
        ctx.model=99

@pytest.mark.asyncio
async def test_mockcalled():
    from unittest.mock import Mock
    m=Mock()
    m()
    m.assert_called()
    app={}
    async with contextlib.asynccontextmanager(async_solver_ctx)(app):
        assert 'solve' in app
        
