# pylint: disable=invalid-name
"""Rota solver"""

from datetime import date
from threading import Lock
import threading
from typing import TYPE_CHECKING
import dataclasses
import asyncio
import queue

from ortools.sat.python import cp_model
from datatypes import DutyCell, SessionDuty

from signals import signal

# from constraints import get_all_constraint_classes

if TYPE_CHECKING:
    from constraints.base import BaseConstraint
    from ui import View

solvers_queue=queue.Queue()
solver_lock=Lock()

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


def solve(
        data: dict,
        config: dict,
        result_queue:asyncio.Queue,
        loop,
):
    """Solve rota
    data: initial duty data as dict of (name,date):duties
    config: configuration for constraints
    result_queue:feed results back to main thread
    """
    print ('Setting up...')
    model = cp_model.CpModel()
    ctx = GenericConfig(
        initial_data=data,
        context=config,
        days=sorted({d[1] for d in data}),
        minimize_targets=[],
        dutystore=DutyStore(model),
        model=model,
        constraint_atoms=[],
        shifts=('am','pm','oncall'),
        staff={n[0] for n in data},
        locations=set(('ICU','Theatre')),
        condition=asyncio.Condition()
    )

    print ('Applying constraints...')
    signal('apply_constraint').send(ctx)

    model.Minimize(sum(ctx.minimize_targets))
    
    def process_result(solver):
        outputdict = {}
        assert ctx.days is not None
        for day in ctx.days:
            for staff in ctx.staff:
                outputdict[(staff,day)] = DutyCell(duties={shift:SessionDuty() for shift in ctx.shifts})
        signal('build_output').send(ctx,outputdict=outputdict, solver=solver)
        return outputdict
    
    def post_result(solver:cp_model.CpSolver):
        print('callback')
        result = process_result(solver)
        print(solver.ObjectiveValue())
        asyncio.run_coroutine_threadsafe(result_queue.put(result),loop)

    class SolutionPrinter(cp_model.CpSolverSolutionCallback):
        """Print intermediate solutions (objective, variable values, time)."""

        def on_solution_callback(self):
            "solution callback"
            post_result(self)
            #kill previous solvers
    try:
        while True:
            prev_solver:cp_model.CpSolver=solvers_queue.get_nowait()
            print('removing solvers')
            prev_solver.StopSearch()
    except queue.Empty:
        pass
    
    print('waiting for solver lock...')
    with solver_lock:
        print('obtained lock')
        solver=cp_model.CpSolver()
        solvers_queue.put(solver)
        
        print ('Solving...')
        solver.Solve(model, SolutionPrinter())
        print('Solver finished')
        if solver.StatusName() in ['FEASIBLE', 'OPTIMAL']:
            post_result(solver)
        print (f'Solver status: {solver.StatusName()}')
        return solver.StatusName()
