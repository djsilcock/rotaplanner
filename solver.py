# pylint: disable=invalid-name
"""Rota solver"""

from concurrent.futures import ThreadPoolExecutor
from datetime import date
from threading import Lock, Event
from typing import TYPE_CHECKING, Callable
import dataclasses
import asyncio
import queue

from ortools.sat.python import cp_model
from datatypes import DutyCell, SessionDuty

from signals import signal

# from constraints import get_all_constraint_classes

if TYPE_CHECKING:
    from ui import View

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


class SolutionPrinter(cp_model.CpSolverSolutionCallback):
    """Print intermediate solutions (objective, variable values, time)."""

    def __init__(self, callback, event: Event):
        super().__init__()
        self.callback = callback
        self.event = event

    def on_solution_callback(self):
        "solution callback"
        if self.event.is_set():
            self.StopSearch()
            return
        self.callback(self)


class SolverManager:
    def __init__(self):
        self.solver_lock = Lock()
        self.solver_events = []
        self._shutdown = False
        self.executor=ThreadPoolExecutor()

    def shutdown(self):
        self.stop()
        self.executor.shutdown()

    def solve(self, model, callback):
        print('starting solver')
        self.stop()
        stop_event = Event()
        self.solver_events.append(stop_event)
        print('waiting for solver lock') 
        with self.solver_lock:
            print('lock obtained')
            printer = SolutionPrinter(callback, stop_event)
            solver = cp_model.CpSolver()
            def do_solve():
                if stop_event.is_set():
                    return
                print(f'solving with {id(solver)}')
                solver.Solve(model, printer)
                status = solver.StatusName()
                if stop_event.is_set():
                    print(f'solver {id(solver)} aborted')
                    return
                if status in ['FEASIBLE', 'OPTIMAL']:
                    callback(solver)
                stop_event.set()
                self.solver_events.remove(stop_event)
                return status
            def stop_solver():
                stop_event.wait()
                solver.StopSearch()
            self.executor.submit(stop_solver)
            return self.executor.submit(do_solve)
            
            
    def stop(self):
        for e in self.solver_events:
            e.set()


solver_manager = SolverManager()


def solve(
        data: dict,
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
    ctx = GenericConfig(
        initial_data=data,
        context=config,
        days=sorted({d[1] for d in data}),
        minimize_targets=[],
        dutystore=DutyStore(model),
        model=model,
        constraint_atoms=[],
        shifts=('am', 'pm', 'oncall'),
        staff={n[0] for n in data},
        locations=set(('ICU', 'Theatre')),
        condition=asyncio.Condition()
    )

    print('Applying constraints...')
    signal('apply_constraint').send(ctx)

    model.Minimize(sum(ctx.minimize_targets))

    def process_result(solver):
        outputdict = {}
        assert ctx.days is not None
        for day in ctx.days:
            for staff in ctx.staff:
                outputdict[(staff, day)] = DutyCell(
                    duties={shift: SessionDuty() for shift in ctx.shifts})
        signal('build_output').send(ctx, outputdict=outputdict, solver=solver)
        return outputdict

    def post_result(solver: cp_model.CpSolver):
        print('callback')
        result = process_result(solver)
        print(solver.ObjectiveValue())
        progress_callback(result)

    return solver_manager.solve(model, post_result)
