# pylint: disable=invalid-name
"""Rota solver"""

from concurrent.futures import ThreadPoolExecutor
from datetime import date
from threading import Condition, Lock, Event
from typing import TYPE_CHECKING, Callable, Optional, cast
import dataclasses
import asyncio
import queue
from uuid import uuid4

from ortools.sat.python import cp_model
from constraint_ctx import ConstraintContext
from datatypes import SessionDuty

from signals import signal
from datastore import DataStore

# from constraints import get_all_constraint_classes

solvers_queue = queue.Queue()
solver_lock = Lock()


class DutyStore(dict):
    "creates cp_model.BoolVar instances"

    def __init__(self, model: cp_model.CpModel):
        super().__init__()
        self.model = model

    def __missing__(self, key):
        self[key] = self.model.NewBoolVar(repr(key))
        return self[key]


@dataclasses.dataclass
class GenericConfig:
    "Generic config information"
    initial_data: dict
    days: list[date]
    context: dict
    dutystore: dict[tuple, cp_model.IntVar]
    model: cp_model.CpModel
    minimize_targets: list[cp_model.IntVar]
    constraint_atoms: list[cp_model.IntVar]
    shifts: tuple
    staff: set[str]
    locations: set[str]
    condition: asyncio.Condition

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

class SolverManager:
    def __init__(self):
        self.executor=ThreadPoolExecutor()
        self.condition=Condition()
        self.active_model=None
        self.active_task=None

    def shutdown(self):
        self.stop()
        self.executor.shutdown()

    def solve(
            self,
            datastore: DataStore,
            config: dict,
            progress_callback: Callable
    ):
        """Solve rota
        data: initial duty data as dict of (name,date):duties
        config: configuration for constraints
        callback:feed results back to main thread
        """
        print('Setting up...')
        model = cp_model.CpModel()
        solver = cp_model.CpSolver()
        def do_solve():
            with self.condition:
                self.active_model=model
                self.condition.notify_all()
            data=datastore.data
            ctx=ConstraintContext(model=model)
            ctx=cast(CoreContext,ctx)
            ctx.core = CoreConfig(
                days=sorted({d[1] for d in data}),
                minimize_targets=[],
                constraint_atoms=[],
                shifts=('am', 'pm', 'oncall'),
                staff={n[0] for n in data},
                locations=set(('ICU', 'Theatre')),
            )

            @ctx.signals.after_apply.connect
            def minimize_targets():
                model.Minimize(sum(ctx.core.minimize_targets))

            signal('apply_constraint').send(ctx)
            if self.active_model!=model:
                return
            ctx.signals.after_apply.emit()

            
            def process_result(solver):
                outputdict = {}
                assert ctx.core.days is not None
                for day in ctx.core.days: 
                    for staff in ctx.core.staff:
                        for shift in ctx.core.shifts:
                            sd=SessionDuty()
                            ctx.signals.result.emit(
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
            if self.active_model!=model:
                return
            printer = SolutionPrinter(post_result)
            solver.Solve(model, printer)
            status = solver.StatusName()
            if self.active_model!=model:
                print(f'solver {model} aborted')
                return
            if status in ['FEASIBLE', 'OPTIMAL']:
                post_result(solver)
            with self.condition:
                self.active_model=None
                self.condition.notify_all()
            return status
        def stop_solver():
            with self.condition:
                self.condition.wait_for(lambda:self.active_model!=model)
                solver.StopSearch()
        self.executor.submit(stop_solver)
        return self.executor.submit(do_solve)
            
    def stop(self):
        with self.condition:
            self.active_model=None
            self.condition.notify_all()


solver_manager = SolverManager()


def solve(
        datastore: DataStore,
        config: dict,
        progress_callback: Callable
):

    return solver_manager.solve(datastore,config,progress_callback)


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
        ctx=ConstraintContext(model=model)
        ctx.core = CoreConfig(
            days=sorted({d[1] for d in data}),
            minimize_targets=[],
            constraint_atoms=[],
            shifts=('am', 'pm', 'oncall'),
            staff={n[0] for n in data},
            locations=set(('ICU', 'Theatre')),
        )

        @ctx.signals.after_apply.connect
        def minimize_targets():
            model.Minimize(sum(ctx.core.minimize_targets))
        await signal('apply_constraint').send_async(ctx=ctx,**config)
        await ctx.signals.after_apply.emit_async()

        def process_result(solver):
            outputdict = {}
            assert ctx.core.days is not None
            for day in ctx.core.days: 
                for staff in ctx.core.staff:
                    for shift in ctx.core.shifts:
                        sd=SessionDuty()
                        ctx.signals.result.emit(
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
        except asyncio.CancelledError:
            print(f'solver {model} aborted')
            solver.StopSearch()
            raise
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
    await runner




