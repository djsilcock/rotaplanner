# pylint: disable=invalid-name
"""Rota solver"""
import asyncio
from calendar import MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY
import collections
from datetime import date, timedelta
import json
import multiprocessing
import sys
from threading import Timer

import os
import time


from ortools.sat.python import cp_model
import sanic
import sanic.response


from constants import Shifts, Staff, Duties
from constraintmanager import apply_constraint, get_constraint_config
from abstracttypes import RotaSolver as RSAbstract
# pylint: disable=unused-import
import constraints  # only used for side-effects


class VarArrayAndObjectiveSolutionPrinter(cp_model.CpSolverSolutionCallback):
    """Print intermediate solutions (objective, variable values, time)."""

    def __init__(self, pipe, time_limit=15):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.__solution_count = 0
        self.__start_time = time.time()
        self.pipe = pipe
        self._time_limit = time_limit
        self._timer = None

    def on_solution_callback(self):
        """Called on each new solution."""
        current_time = time.time()
        obj = self.ObjectiveValue()
        time_taken = current_time - self.__start_time
        self.pipe.send(
            {'type': 'progress', 'time': time_taken, 'objective': obj})

        self.__solution_count += 1
        if not self._timer:
            self._timer = Timer(self._time_limit, self.stop)
            self._timer.start()
        else:
            self._timer.cancel()
            self._timer = Timer(self._time_limit, self.stop)
            self._timer.start()

    def solution_count(self):
        """Returns the number of solutions found."""
        return self.__solution_count

    def stop(self):
        """Stop after timeout"""
        print(
            f'Objective {int(self.ObjectiveValue())} not changed '
            f'in {self._time_limit} seconds, stopping solver...'
        )
        self.StopSearch()


class RotaSolver(RSAbstract):
    """Main rotasolver class"""

    def get_duty(self, duty: Duties, day: int, shift: Shifts, staff: Staff):
        """retrieve the duty atom"""
        return self.all_duties[(duty, day, shift, staff)]

    def create_duty(self, duty: Duties, day: int, shift: Shifts, staff: Staff):
        """create duty"""
        if (duty, day, staff) in self.all_duties:
            raise KeyError(
                f'{duty.name} {day} {shift.name} {staff.name} exists')
        newvar = self.model.NewBoolVar(f'{duty}{day}{shift}{staff}')
        self.all_duties[(duty, day, shift, staff)] = newvar
        #print(f'created: {duty} {day} {shift} {staff}')
        return newvar

    def get_or_create_duty(self, duty: Duties, day: int, shift: Shifts, staff: Staff):
        """Retrieve duty or create new if not found"""
        try:
            return self.get_duty(duty, day, shift, staff)
        except KeyError:
            return self.create_duty(duty, day, shift, staff)

    def __init__(self,
                 
                 rota_cycles: int,
                 slots_on_rota: int,
                 people_on_rota: int,
                 startdate: str,
                 pipe):
        # pylint: disable=super-init-not-called
        self.pipe = pipe
        self.constraints = collections.OrderedDict()
        self.rota_cycles = rota_cycles
        self.slots_on_rota = slots_on_rota
        self.people_on_rota = people_on_rota
        self.startdate = date.fromisoformat(startdate[0:10])
        self.startingday = None
        self.endingday = None
        self.exclusiondays = None
        if self.startdate.weekday() != 0:
            raise ValueError('Starting date must be a Monday')
        
        self.model = cp_model.CpModel()
        self.all_duties = {}

        self.targets = None

    def set_enforcement_period(self, startdate, enddate, exclusions=None):
        """sets period for enforcement of rules
        startdate:str enddate:str ,exclusions [str] - ISO format date strings"""
        self.startingday = (date.fromisoformat(startdate)-self.startdate).days
        self.endingday = (date.fromisoformat(enddate)-self.startdate).days
        self.exclusiondays = exclusions if exclusions is not None else []

    def clear_enforcement_period(self):
        """clear previously set enforcement period"""
        self.startingday = None
        self.endingday = None
        self.exclusiondays = None

    def days(self, startdate=None, enddate=None, weekdays=None, exclusions=None):
        """returns iterator of days"""
        weekdays_to_include = weekdays if weekdays is not None else [
            MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY]
        days_to_exclude = (map(lambda d: (date.fromisoformat(
            d)-self.startdate).days, exclusions)
            if exclusions is not None
            else self.exclusiondays if self.exclusiondays is not None
            else [])
        if startdate is None:
            if self.startingday is not None:
                startingday = self.startingday
            else:
                startingday = 0
        elif date.fromisoformat(startdate) < self.startdate:
            raise ValueError(
                'starting date must not be before beginning of rota')
        else:
            startingday = (date.fromisoformat(startdate)-self.startdate).days
        if enddate is None:
            if self.endingday is not None:
                endingday = self.endingday
            else:
                endingday = self.rota_cycles*self.slots_on_rota*7
        elif date.fromisoformat(enddate) > self.startdate+timedelta(
                days=self.rota_cycles*self.slots_on_rota*7):
            raise ValueError(
                'ending date must not be after end of rota')
        else:
            endingday = (date.fromisoformat(enddate)-self.startdate).days

        return (r for r in range(startingday, endingday)
                if r % 7 in weekdays_to_include
                and r not in days_to_exclude)

    def apply_constraint(self, constraintspec):
        """Convenience method for constraintmanager.apply_constraint(model,**constraintspec)"""
        apply_constraint(self, **constraintspec)

    # Create a solver and solve.
    def solve(self):
        """solve model"""

        for constraint in self.constraints.values():
            self.pipe.send(
                {'type': 'info',
                 'message': f'applying constraint:{type(constraint).__name__}'})
            constraint.apply_constraint()
        solver = cp_model.CpSolver()
        self.pipe.send(
            {'type': 'info', 'message': f'number of variables: {len(self.all_duties)}'})

        self.pipe.send({'type': 'progress', 'time': 0, 'objective': None})
        status = solver.Solve(
            self.model, VarArrayAndObjectiveSolutionPrinter(self.pipe))
        self.pipe.send({'type': 'solveStatus', 'statusName': solver.StatusName(
            status), 'status': status})
        generator = []
        if solver.StatusName(status) in ['FEASIBLE', 'OPTIMAL']:
            for cons in self.constraints.values():
                generator = cons.event_stream(solver, generator)
            for event in generator:
                self.pipe.send(event)
        self.pipe.send({'type': 'eof'})

    # Enumerate all solutions.
    # solver.parameters.enumerate_all_solutions = True
    # Solve.



