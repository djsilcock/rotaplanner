import pytest
from dependency_injection import RunContext, Dependency, BasePlugin
from typing import Annotated
import asyncio


def test_dependency_resolution():
    def dependency1():
        return 1

    def dependency2():
        return 2

    def dependency3(
        one: Annotated[int, Dependency(dependency1)],
        two: Annotated[int, Dependency(dependency2)],
    ):
        return one + two

    ctx = RunContext()
    result = ctx.call_with_dependencies(dependency3)
    assert result == 3


def test_plugin_registration():
    with BasePlugin.temporary_registry():

        class TestPlugin(BasePlugin):
            def run(self):
                return "plugin running"

        ctx = RunContext()
        result = ctx.run_hook("run")
        assert result == ["plugin running"]


def test_async_plugin_registration():
    with BasePlugin.temporary_registry():

        class TestPlugin(BasePlugin):
            async def async_run(self):
                return "async plugin running"

        async def main():
            ctx = RunContext()
            result = await ctx.run_hook_async("async_run")
            assert result == ["async plugin running"]

        asyncio.run(main())


def test_dependency_caching():
    call_count = 0

    def dependency1():
        nonlocal call_count
        call_count += 1
        return 1

    ctx = RunContext()
    dep = Dependency(dependency1)
    dep.resolve(ctx)
    dep.resolve(ctx)
    assert call_count == 1


def test_dependency_no_caching():
    call_count = 0

    def dependency1():
        nonlocal call_count
        call_count += 1
        return 1

    ctx = RunContext()
    dep = Dependency(dependency1, use_cache=False)
    dep.resolve(ctx)
    dep.resolve(ctx)
    assert call_count == 2


def test_plugin_with_dependencies():
    with BasePlugin.temporary_registry():

        def dependency1():
            return 1

        def dependency2():
            return 2

        def dependency3(
            one: Annotated[int, Dependency(dependency1)],
            two: Annotated[int, Dependency(dependency2)],
        ):
            return one + two

        class TestPlugin(BasePlugin):
            def run(self, three: Annotated[int, Dependency(dependency3)]):
                return three

        ctx = RunContext()
        result = ctx.run_hook("run")
        assert result == [3]


def test_async_plugin_with_dependencies():
    with BasePlugin.temporary_registry():

        def dependency1():
            return 1

        def dependency2():
            return 2

        def dependency3(
            one: Annotated[int, Dependency(dependency1)],
            two: Annotated[int, Dependency(dependency2)],
        ):
            return one + two

        class TestPlugin(BasePlugin):
            async def run(self, three: Annotated[int, Dependency(dependency3)]):
                return three

        async def main():
            ctx = RunContext()
            result = await ctx.run_hook_async("run")
            assert result == [3]

        asyncio.run(main())
