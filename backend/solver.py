# pylint: disable=invalid-name
"""Rota solver"""

from concurrent.futures import ThreadPoolExecutor
from datetime import date
from threading import Condition, Lock, Event
from typing import TYPE_CHECKING, Callable
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


class SolverManager:
    def __init__(self):
        self.executor=ThreadPoolExecutor()
        self.condition=Condition()
        self.active_model=None

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



