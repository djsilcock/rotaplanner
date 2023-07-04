
def test_general():
    import constraints
    assert constraints is not None

import pytest
from constraint_ctx import Signal,ConstraintContext
import asyncio

def test_sync_signal():
    signal1=Signal()
    @signal1.connect
    def myfunc(hello):
        return ('myfunc1',hello)
    @signal1.connect
    def myfunc2(hello):
        return ('myfunc2',hello)
    signal1.emit(hello='world')
    with pytest.raises(TypeError):
        signal1.emit(bar='baz')

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
            signal2.emit(hello='async',world='flat')
        await signal2.emit_async(hello='async',world='world')
        await signal2.emit_concurrent(hello='concurrent',world='world')
        async for s in signal2.emit_async_generator(hello='async gen',world='world'):
            pass
        async for s in signal2.emit_concurrent_generator(hello='concurrent gen',world='world'):
            pass
            

    await emitter()

def test_constraintctx():
    ctx=ConstraintContext(99)
    ctx.otherattrib=77
    with pytest.raises(TypeError):
        ctx.model=99