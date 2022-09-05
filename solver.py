# pylint: disable=invalid-name
"""Rota solver"""
from calendar import MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY
import collections
from datetime import date, timedelta
from threading import Timer
from types import FunctionType
from typing import Union

import time


from ortools.sat.python import cp_model


from constants import Shifts, Staff, Duties
from constraints.constraintmanager import apply_constraint
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

    def stop_timeout(self):
        """stop timer"""
        if self._timer:
            self._timer.cancel()


class RotaSolver(RSAbstract):
    """Main rotasolver class"""

    def get_duty_base(self,key):
        """retrieve duty atom"""
        return self.all_duties.get(key,0)

    def get_duty(self, duty: Union[Duties,str], day: int, shift: Shifts, staff: Staff):
        """retrieve the duty atom"""
        return self.get_duty_base((duty, day, shift, staff))

    def create_duty_base(self,key):
        """create duty"""
        if key in self.all_duties:
            raise KeyError(
                f'{repr(key)} exists')
        newvar = self.model.NewBoolVar(repr(key))
        self.all_duties[key] = newvar
        return newvar

    def create_duty(self, duty: Union[Duties,str], day: int, shift: Shifts, staff: Staff):
        """create duty"""
        return self.create_duty_base((duty,day,shift,staff))

    def get_or_create_duty_base(self, key):
        """Retrieve duty or create new if not found"""
        try:
            return self.all_duties[key]
        except KeyError:
            return self.create_duty_base(key)

    
    def get_or_create_duty(self, duty: Union[Duties,str], day: int, shift: Shifts, staff: Staff):
        """Retrieve duty or create new if not found"""
        return self.get_or_create_duty_base((duty, day, shift, staff))

    def __init__(self,
                 slots_on_rota: int,
                 people_on_rota: int,
                 startdate:str,
                 enddate:str,
                 pipe):
        # pylint: disable=super-init-not-called
        self.pipe = pipe
        self.constraints = collections.OrderedDict()
        self.slots_on_rota = slots_on_rota
        self.people_on_rota = people_on_rota
        startdate = date.fromisoformat(startdate[0:10])
        enddate = date.fromisoformat(enddate[0:10])
        self.startdate = startdate-timedelta(days=startdate.weekday())
            #wind back to previous monday
        rota_length = (enddate-startdate).days
        self.rota_length = rota_length+6-rota_length%7
        self.exclusions = None
        self.model = cp_model.CpModel()
        self.all_duties = {}
        self.constraint_atoms = []
        self.minimize_targets = []
        self.targets = None
        
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
                (date.fromisoformat(exclusion_range['end'])-self.startdate).days+1, self.rota_length)
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

    def apply_constraint(self, constraintspec):
        """Convenience method for constraintmanager.apply_constraint(model,**constraintspec)"""
        apply_constraint(self, **constraintspec)

    # Create a solver and solve.
    def solve(self):
        """solve model"""
        for constraint in self.constraints.values():
            constraint.apply_constraint()
        with open('model.proto', 'w', encoding='utf-8') as modelfile:
            print(self.model, file=modelfile)
        self.model.Minimize(sum(self.minimize_targets))
        solver = cp_model.CpSolver()
        self.pipe.send({'type': 'progress', 'time': 0, 'objective': None})
        solution_printer = VarArrayAndObjectiveSolutionPrinter(self.pipe)
        status = solver.Solve(self.model, solution_printer)
        solution_printer.stop_timeout()
        self.pipe.send({'type': 'solveStatus', 'statusName': solver.StatusName(
            status), 'status': status})
        event_generator = []
        pairs = []
        print(f'status:{solver.StatusName(status)}')
        if solver.StatusName(status) in ['FEASIBLE', 'OPTIMAL']:
            for cons in self.constraints.values():
                event_generator = cons.event_stream(solver, event_generator)
                pairs = cons.process_output(solver, pairs)
            for ((staff, shift, day), value) in pairs:
                text_day = (self.startdate +
                            timedelta(days=day)).isoformat()
                self.pipe.send({'type': 'result', 'name': staff.name,
                               'shift': shift.name, 'day': text_day, 'duty': value})
            for event in event_generator:
                self.pipe.send(event)
        self.pipe.send({'type': 'eof'})
        print('done')

    # Enumerate all solutions.
    # solver.parameters.enumerate_all_solutions = True
    # Solve.
