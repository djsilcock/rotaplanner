"""contains rules to constrain the model"""
from calendar import MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY




from constants import Shifts, Staff, Duties
from constraints.constraintmanager import BaseConstraint


class Constraint(BaseConstraint):
    """Maximum deviation from target number of shifts of any given type (excluding locums)"""
    name = "Minimise deviation from average"

    @classmethod
    def definition(cls):

        yield 'same consultant should not be more than'
        yield {
            'name': 'deviation',
            'component': 'number'}
        yield {
            'name': 'shift',
            'component': 'select',
            'options': [
                'Weekend oncall',
                'Weekend daytime',
                'Weekday oncall',
                'Weekday daytime',
                'Any weekend']}
        yield 'shifts above or below target'

    def apply_constraint(self):
        kwargs = dict(**self.kwargs)
        shift = kwargs.pop('shift').lower()
        deviation = kwargs.pop('deviation')
        enforced = self.get_constraint_atom()
        (days, shifts) = {
            'weekend oncall': ([FRIDAY, SATURDAY, SUNDAY], [Shifts.ONCALL]),
            'weekend daytime': ([FRIDAY, SATURDAY, SUNDAY], [Shifts.DAYTIME]),
            'weekday oncall': ([MONDAY, TUESDAY, WEDNESDAY, THURSDAY], [Shifts.ONCALL]),
            'weekday daytime': ([FRIDAY, SATURDAY, SUNDAY], [Shifts.DAYTIME]),
            'any weekend': ([FRIDAY, SATURDAY, SUNDAY], [Shifts.ONCALL, Shifts.DAYTIME])

        }[shift]
        self.weekdays = [SATURDAY]
        for staff in Staff:
            for day in self.days():
                for shift in Shifts:
                    duties = [self.rota.get_duty(Duties.ICU, dd, shift, staff) for dd in range(
                        0, day) if day in days and shift in shifts]
                    tally = self.rota.model.NewIntVar(
                        0,
                        self.rota.rota_cycles*7*self.rota.slots_on_rota,
                        f'tally{day}{shift}{staff}')
                    self.rota.model.AddAbsEquality(
                        tally,
                        sum(duties))
                    target = self.rota.model.NewIntVar(
                        0,
                        self.rota.rota_cycles*7*self.rota.slots_on_rota,
                        'target')
                    self.rota.model.Add(target == (
                        len(duties)//self.rota.people_on_rota)).OnlyEnforceIf(enforced)
                    delta = self.rota.model.NewIntVar(-deviation,
                                                      deviation,
                                                      f'delta{day}{shift}{staff}')
                    self.rota.model.Add(
                        delta == tally-target).OnlyEnforceIf(enforced)
