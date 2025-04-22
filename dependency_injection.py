import inspect
from typing import Any, Callable, Optional, Annotated, get_origin, get_args
import typing
import asyncio
import contextvars
import contextlib
import logging

logger = logging.getLogger(__name__)


class RunContext:
    def __init__(self):
        self.dependencies = {}
        self.plugins = {}

    def call_with_dependencies(self, function: Callable):
        annotations = typing.get_type_hints(function, include_extras=True)
        kwargs = {}
        for name, annotation in annotations.items():
            if typing.get_origin(annotation) == typing.Annotated:
                kwargs[name] = annotation.__metadata__[0].resolve(self)
            elif issubclass(annotation, BasePlugin):
                kwargs[name] = self.plugins[annotation]
            elif annotation == RunContext:
                kwargs[name] = self
        return function(**kwargs)

    def run_hook(self, hook_name, warn_if_async=True):
        if len(self.plugins) == 0:
            logger.info("setting up plugins")
            self.plugins = {
                plugin_class: plugin_class(self)
                for plugin_class in plugin_registry.get()
            }
        results = []
        logger.info(f"calling hook:{hook_name}")
        for plugin in self.plugins.values():
            if hasattr(plugin, hook_name):
                result = self.call_with_dependencies(getattr(plugin, hook_name))
                if warn_if_async and inspect.iscoroutine(result):
                    logger.warning("Async hook called synchronously")
                results.append(result)
        if len(results) == 0:
            logger.warning(f"no registered hooks for {hook_name}")
        return results

    async def run_hook_async(self, hook_name):
        results = []

        class FakeTask:
            def __init__(self, result):
                self._result = result

            def result(self):
                return self._result

        async with asyncio.TaskGroup() as tg:
            for result in self.run_hook(hook_name, warn_if_async=False):
                if inspect.iscoroutine(result):
                    results.append(tg.create_task(result))
                else:
                    results.append(FakeTask(result))
        return [t.result() for t in results]


class Dependency:
    def __init__(
        self, dependency: Optional[Callable[..., Any]] = None, *, use_cache: bool = True
    ):
        self.dependency = dependency
        self.use_cache = use_cache

    def __repr__(self) -> str:
        attr = getattr(self.dependency, "__name__", type(self.dependency).__name__)
        cache = "" if self.use_cache else ", use_cache=False"
        return f"{self.__class__.__name__}({attr}{cache})"

    def resolve(self, ctx: RunContext):
        if self.use_cache and self.dependency in ctx.dependencies:
            logger.info(f"using cached result for {self}")
            return ctx.dependencies[self.dependency]
        ctx.dependencies[self.dependency] = ctx.call_with_dependencies(self.dependency)
        return ctx.dependencies[self.dependency]


class Registerable:
    _registry = None

    def __init_subclass__(cls, auto_register=True, **kwargs):
        super().__init_subclass__(**kwargs)
        if auto_register:
            cls.register()

    @classmethod
    @contextlib.contextmanager
    def temporary_registry(cls, include_parent=False):
        new_registry = cls._registry.get()[:] if include_parent else []
        token = cls._registry.set(new_registry)
        yield
        cls._registry.reset(token)

    @classmethod
    def register(cls):
        if cls._registry is not None:
            if cls not in cls._registry.get():
                cls._registry.get().append(cls)


plugin_registry = contextvars.ContextVar("plugin_registry", default=[])


class BasePlugin(Registerable):
    _registry = plugin_registry

    def __init__(self, ctx: RunContext):
        self.ctx = ctx


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    def dependency1():
        print("setting up dependency 1")
        return 1

    def dependency2():
        print("setting up dependency 2")
        return 2

    def dependency3(
        one: Annotated[int, Dependency(dependency1)],
        two: Annotated[int, Dependency(dependency2)],
    ):
        print("setting up dependency 3")
        return one + two

    def dependency4(
        three: Annotated[int, Dependency(dependency3)],
        one: Annotated[int, Dependency(dependency1)],
    ):
        print("setting up dependency 4")
        return one + three

    class MyPlugin(BasePlugin):
        def run(self, a: Annotated[int, Dependency(dependency4)]):
            print("Plugin result", a)

    class MyPlugin2(BasePlugin):
        async def run(self, ctx: RunContext, other_plugin: MyPlugin):
            print(ctx)

    async def main():
        ctx = RunContext()
        await ctx.run_hook_async("run")
        await ctx.run_hook_async("fly")

    asyncio.run(main())
