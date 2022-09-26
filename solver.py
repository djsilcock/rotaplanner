# pylint: disable=invalid-name
"""Rota solver"""
import asyncio
from calendar import MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY
import collections
from datetime import date, timedelta
from importlib import import_module
import queue
from threading import Thread
from typing import Union
import time

from ortools.sat.python import cp_model

from constants import Shifts, Staff, Duties

class VarArrayAndObjectiveSolutionPrinter(cp_model.CpSolverSolutionCallback):
    """Print intermediate solutions (objective, variable values, time)."""

    def __init__(self, output_queue):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.__solution_count = 0
        self.__start_time = time.time()
        self.output_queue = output_queue

    def on_solution_callback(self):
        """Called on each new solution."""
        current_time = time.time()
        obj = self.ObjectiveValue()
        time_taken = current_time - self.__start_time
        self.queue.put(
            {'type': 'progress', 'time': time_taken, 'objective': obj})

        self.__solution_count += 1

    def solution_count(self):
        """Returns the number of solutions found."""
        return self.__solution_count


class RotaSolver():
    """Main rotasolver class"""

    def get_duty_base(self, key):
        """retrieve duty atom"""
        return self.all_duties.get(key, 0)

    def get_duty(self, duty: Union[Duties, str], day: int, shift: Shifts, staff: Staff):
        """retrieve the duty atom"""
        return self.get_duty_base((duty, day, shift, staff))

    def create_duty_base(self, key):
        """create duty"""
        if key in self.all_duties:
            raise KeyError(
                f'{repr(key)} exists')
        newvar = self.model.NewBoolVar(repr(key))
        self.all_duties[key] = newvar
        return newvar

    def create_duty(self, duty: Union[Duties, str], day: int, shift: Shifts, staff: Staff):
        """create duty"""
        return self.create_duty_base((duty, day, shift, staff))

    def get_or_create_duty_base(self, key):
        """Retrieve duty or create new if not found"""
        try:
            return self.all_duties[key]
        except KeyError:
            return self.create_duty_base(key)

    def get_or_create_duty(self, duty: Union[Duties, str], day: int, shift: Shifts, staff: Staff):
        """Retrieve duty or create new if not found"""
        return self.get_or_create_duty_base((duty, day, shift, staff))

    def __init__(self,
                 slots_on_rota: int,
                 people_on_rota: int,
                 startdate: str,
                 enddate: str):
        # pylint: disable=super-init-not-called

        self.constraints = collections.OrderedDict()
        self.slots_on_rota = slots_on_rota
        self.people_on_rota = people_on_rota
        startdate = date.fromisoformat(startdate[0:10])
        enddate = date.fromisoformat(enddate[0:10])
        self.startdate = startdate-timedelta(days=startdate.weekday())
        # wind back to previous monday
        rota_length = (enddate-startdate).days
        self.rota_length = rota_length+6-rota_length % 7
        self.exclusions = None
        self.model = cp_model.CpModel()
        self.all_duties = {}
        self.constraint_atoms = []
        self.minimize_targets = []
        self.targets = None
        self.status = None

    def days(self, startdate=None, enddate=None, weekdays=None, exclusions=None):
        """returns iterator of days"""
        weekdays_to_include = weekdays if weekdays is not None else [
            MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY]
        days_to_exclude = []
        all_exclusions = []
        if exclusions is not None:
            all_exclusions.extend(exclusions)
        if self.exclusions is not None:
            all_exclusions.extend(self.exclusions)
        for exclusion_range in all_exclusions:
            exc_start = max(0, (date.fromisoformat(
                exclusion_range['start'])-self.startdate).days)
            exc_end = min(
                (date.fromisoformat(
                    exclusion_range['end'])-self.startdate).days+1,
                self.rota_length)
            days_to_exclude.extend(range(exc_start, exc_end))

        if startdate is None:
            startingday = 0
        else:
            startingday = max(
                0, (date.fromisoformat(startdate)-self.startdate).days)
        if enddate is None:
            endingday = self.rota_length
        else:
            endingday = min(
                (date.fromisoformat(enddate)-self.startdate).days,
                self.rota_length)

        return (r for r in range(startingday, endingday)
                if r % 7 in weekdays_to_include
                and r not in days_to_exclude)

    def apply_constraint(self, params):
        """Apply constraint spec. Use as rota.apply_constraint(constraintspec)"""
        constraint = params['type']
        constraintid = params['id']
        print(f'applying:{constraint}')
        constraint = constraint.lower()
        if (constraint, constraintid) in self.constraints:
            print(f'overwriting {constraintid}')
            del self.constraints[(constraint, constraintid)]
        self.constraints[(constraint, constraintid)] = import_module(
            f'constraints.{constraint}').Constraint(
            self, **params)

    # Create a solver and solve.

    def solve(self):
        """solve model"""
        for constraint in self.constraints.values():
            constraint.apply_constraint()
        # with open('model.proto', 'w', encoding='utf-8') as modelfile:
        #    print(self.model, file=modelfile)
        self.model.Minimize(sum(self.minimize_targets))
        solver = cp_model.CpSolver()
        solver_queue = queue.Queue()
        solver_queue.put({'type': 'progress', 'time': 0, 'objective': None})
        solution_printer = VarArrayAndObjectiveSolutionPrinter(solver_queue)

        def abort_solver():
            solver.StopSearch()

        def do_solve():
            self.status = None
            self.status = solver.Solve(self.model, solution_printer)

        async def results_iterator():
            solver_thread = Thread(target=do_solve)
            solver_thread.run()
            while solver_thread.is_alive():
                try:
                    yield solver_queue.get_nowait()
                except queue.Empty:
                    await asyncio.sleep(0.1)

            yield {'type': 'solveStatus', 'statusName': solver.StatusName()}
            event_generator = []
            pairs = []
            print(f'status:{solver.StatusName()}')
            if solver.StatusName() in ['FEASIBLE', 'OPTIMAL']:
                for cons in self.constraints.values():
                    event_generator = cons.event_stream(
                        solver, event_generator)
                    pairs = cons.process_output(solver, pairs)
                for ((staff, shift, day), value) in pairs:
                    text_day = (self.startdate +
                                timedelta(days=day)).isoformat()
                    yield {'type': 'result', 'name': staff.name,
                           'shift': shift.name, 'day': text_day, 'duty': value}
                for event in event_generator:
                    yield event
            yield {'type': 'eof'}
        return (abort_solver, results_iterator())

    # Enumerate all solutions.
    # solver.parameters.enumerate_all_solutions = True
    # Solve.
