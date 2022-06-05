# pylint: disable=invalid-name
"""Rota solver"""
from calendar import MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY
import collections
from datetime import date, timedelta
from threading import Timer

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
        self.exclusions = None
        if self.startdate.weekday() != 0:
            raise ValueError('Starting date must be a Monday')

        self.model = cp_model.CpModel()
        self.all_duties = {}
        self.constraint_atoms=[]
        self.minimize_targets=[]
        self.targets = None

    def set_enforcement_period(self, startdate, enddate, exclusions=None):
        """sets period for enforcement of rules
        startdate:str enddate:str ,exclusions [str] - ISO format date strings"""
        self.startingday = (date.fromisoformat(startdate)-self.startdate).days
        self.endingday = (date.fromisoformat(enddate)-self.startdate).days
        self.exclusions = exclusions if exclusions is not None else []

    def clear_enforcement_period(self):
        """clear previously set enforcement period"""
        self.startingday = None
        self.endingday = None
        self.exclusions = None

    def days(self, startdate=None, enddate=None, weekdays=None, exclusions=None):
        """returns iterator of days"""
        weekdays_to_include = weekdays if weekdays is not None else [
            MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY]
        days_to_exclude = []
        all_exclusions=[]
        if exclusions is not None:
            with open('logfile.txt','a') as logfile:
                print(f'exclusions:{exclusions}',file=logfile)
            all_exclusions.extend(exclusions)
        if self.exclusions is not None:
            all_exclusions.extend(self.exclusions)
        for exclusion_range in all_exclusions:
            exc_start=(date.fromisoformat(exclusion_range['start'])-self.startdate).days
            exc_end=(date.fromisoformat(exclusion_range['end'])-self.startdate).days+1
            days_to_exclude.extend(range(exc_start,exc_end))
            with open('logfile.txt', 'a',encoding='utf-8') as logfile:
                print(f'all exclusions:{days_to_exclude}', file=logfile)
                
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
            constraint.apply_constraint()
        with open('model.proto','w') as modelfile:
            print(self.model,file=modelfile)
        self.model.Minimize(sum(self.minimize_targets))
        solver = cp_model.CpSolver()
        self.pipe.send(
            {'type': 'info', 'message': f'number of variables: {len(self.all_duties)}'})

        self.pipe.send({'type': 'progress', 'time': 0, 'objective': None})
        status = solver.Solve(
            self.model, VarArrayAndObjectiveSolutionPrinter(self.pipe))
        self.pipe.send({'type': 'solveStatus', 'statusName': solver.StatusName(
            status), 'status': status})
        event_generator = []
        pairs=[]
        if solver.StatusName(status) in ['FEASIBLE', 'OPTIMAL']:
            for cons in self.constraints.values():
                event_generator = cons.event_stream(solver, event_generator)
                pairs=cons.process_output(solver,pairs)
            for ((staff,shift,day),value) in pairs:
                self.pipe.send({'type':'result','name':staff.name,'shift':shift.name,'day':day.name,'duty':value})
            for event in event_generator:
                self.pipe.send(event)          
        self.pipe.send({'type': 'eof'})

    # Enumerate all solutions.
    # solver.parameters.enumerate_all_solutions = True
    # Solve.
