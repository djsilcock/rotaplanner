# pylint: disable=invalid-name
"""Rota solver"""


from contextlib import suppress
from datetime import date
from typing import Callable
import dataclasses
import asyncio


from ortools.sat.python import cp_model
from constraint_ctx import ConstraintContext
from datatypes import SessionDuty

from datastore import DataStore

# from constraints import get_all_constraint_classes


@dataclasses.dataclass
class CoreConfig:
    "Generic config information"
    days: list[date]
    minimize_targets: list[cp_model.IntVar]
    constraint_atoms: list[cp_model.IntVar]
    shifts: tuple
    staff: set[str]
    locations: set[str]
    pubhols:set[date]


class SolutionPrinter(cp_model.CpSolverSolutionCallback):
    """Print intermediate solutions (objective, variable values, time)."""

    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def on_solution_callback(self):
        "solution callback"
        self.callback(self)


async def solve_async(datastore:DataStore, config, result_queue:asyncio.Queue):
    """Solve rota
    data: initial duty data as dict of (name,date):duties
    config: configuration for constraints
    callback:feed results back to main thread
    """

    data = datastore.data
    pubhols=datastore.pubhols
    ctx = ConstraintContext(
        {'core':CoreConfig(
            days=sorted({d[1] for d in data}),
            minimize_targets=[],
            constraint_atoms=[],
            shifts=('am', 'pm', 'oncall'),
            staff={n[0] for n in data},
            locations=set(('ICU', 'Theatre')),
            pubhols=pubhols
        ),**config})

    await ctx.apply_constraints()
    ctx.model.Minimize(sum(ctx.core_config.minimize_targets))

    async def process_result(solution):
        outputdict = {}
        assert ctx.core_config.days is not None
        for day in ctx.core_config.days:
            for staff in ctx.core_config.staff:
                for shift in ctx.core_config.shifts:
                    sd = SessionDuty()
                    await ctx.result(
                        staff=staff,
                        day=day,
                        shift=shift,
                        sessionduty=sd,
                        solution=solution
                        )
                    outputdict[(day, staff, shift)] = sd
        await result_queue.put(outputdict)

    loop=asyncio.get_running_loop()
    def post_result(solution: cp_model.CpSolver|cp_model.CpSolverSolutionCallback):
        asyncio.run_coroutine_threadsafe(process_result(solution),loop)

    print('starting solver')
    printer = SolutionPrinter(post_result)
    solver = cp_model.CpSolver()
    try:
        await asyncio.to_thread(lambda: solver.Solve(ctx.model, printer))
    finally:
        solver.StopSearch()
    status = solver.StatusName()
    if status in ['FEASIBLE', 'OPTIMAL']:
        await process_result(solver)
    return status


async def solver_runner(solver_queue: asyncio.Queue[tuple | None]):
    "background task to run solver"
    current_solver: asyncio.Task | None = None
    try:
        while True:
            solver_args = await solver_queue.get()
            if current_solver:
                current_solver.cancel()
                with suppress(asyncio.CancelledError):
                    await current_solver
            if solver_args is not None:
                current_solver = asyncio.create_task(solve_async(*solver_args))
    finally:
        if current_solver:
            current_solver.cancel()


async def async_solver_ctx(app):
    "set up solver context on aiohttp app"
    solver_queue = asyncio.Queue()
    runner = asyncio.create_task(solver_runner(solver_queue))

    async def solve(
        datastore: DataStore,
        config: dict,
        progress_callback: Callable
    ):
        await solver_queue.put((datastore, config, progress_callback))
    app['solve'] = solve
    yield
    runner.cancel()
    with suppress(asyncio.CancelledError):
        await runner
