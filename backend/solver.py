# pylint: disable=invalid-name
"""Rota solver"""


from contextlib import suppress
from datetime import date
from threading import Lock
from typing import TYPE_CHECKING, Callable, cast
import dataclasses
import asyncio
import queue


from ortools.sat.python import cp_model
from constraint_ctx import ConstraintContext
from datatypes import SessionDuty

from signals import signal
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



class SolutionPrinter(cp_model.CpSolverSolutionCallback):
    """Print intermediate solutions (objective, variable values, time)."""

    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def on_solution_callback(self):
        "solution callback"
        self.callback(self)

class CoreContext(ConstraintContext):
    core:CoreConfig

async def solve_async(datastore,config,progress_callback):
    """Solve rota
    data: initial duty data as dict of (name,date):duties
    config: configuration for constraints
    callback:feed results back to main thread
    """
    print('Setting up...')
    model = cp_model.CpModel()
    solver = cp_model.CpSolver()
    data=datastore.data
    ctx=ConstraintContext(
        model=model,
        core_config = CoreConfig(
            days=sorted({d[1] for d in data}),
            minimize_targets=[],
            constraint_atoms=[],
            shifts=('am', 'pm', 'oncall'),
            staff={n[0] for n in data},
            locations=set(('ICU', 'Theatre')),
        ))
    
    @ctx.signals.after_apply.connect
    def minimize_targets():
        model.Minimize(sum(ctx.core_config.minimize_targets))
    await signal('apply_constraint').send_async(ctx=ctx,**config)
    await ctx.signals.after_apply.send_async()

    def process_result(solver):
        outputdict = {}
        assert ctx.core_config.days is not None
        for day in ctx.core_config.days: 
            for staff in ctx.core_config.staff:
                for shift in ctx.core_config.shifts:
                    sd=SessionDuty()
                    ctx.signals.result.send(
                        staff=staff,
                        day=day,
                        shift=shift,
                        sessionduty=sd, 
                        solver=solver)
                    outputdict[(day,staff,shift)]=sd
        return outputdict

    def post_result(solver: cp_model.CpSolver):
        print('callback')
        result = process_result(solver)
        print(solver.ObjectiveValue())
        progress_callback(result)

    print('starting solver')
    printer = SolutionPrinter(post_result)
    try:
        await asyncio.to_thread(lambda:solver.Solve(model, printer))
    finally:
        solver.StopSearch()
    status = solver.StatusName()
    if status in ['FEASIBLE', 'OPTIMAL']:
        post_result(solver)
    return status
        
async def solver_runner(solver_queue:asyncio.Queue[tuple|None]):
    current_solver:asyncio.Task|None=None
    try:
        while True:
            solver_args=await solver_queue.get()
            if current_solver:
                current_solver.cancel()
            with suppress(asyncio.CancelledError):
                await current_solver
            if solver_args is not None:
                current_solver=asyncio.create_task(solve_async(*solver_args))
    finally:
        if current_solver:
            current_solver.cancel()
            



async def async_solver_ctx(app):
    solver_queue=asyncio.Queue()
    runner=asyncio.create_task(solver_runner(solver_queue))
    async def solve(
        datastore: DataStore,
        config: dict,
        progress_callback: Callable
    ):
        await solver_queue.put((datastore,config,progress_callback))
    app['solve']=solve
    yield
    runner.cancel()
    with suppress(asyncio.CancelledError):
        await runner




