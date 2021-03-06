"""contains rules to constrain the model"""
from calendar import SATURDAY




from constants import Shifts, Staff, Duties
from constraints.constraintmanager import BaseConstraint


class Constraint(BaseConstraint):
    """Maximum number of oncalls per given number of days"""
    name = "Limit oncall frequency"

    @classmethod
    def definition(cls):

        yield 'same consultant should not do more than'
        yield {
            'name': 'numerator',
            'component': 'number'}
        yield 'oncalls in any'
        yield {
            'name': 'denominator',
            'component': 'number'}
        yield 'consecutive days'

    def apply_constraint(self):
        kwargs = dict(**self.kwargs)
        denominator = kwargs.pop('denominator')
        numerator = kwargs.pop('numerator')
        enforced = self.get_constraint_atom()
        for day in self.days():
            enforced = self.get_constraint_atom(day=day)
            if day < denominator:
                continue
            for staff in Staff:
                self.rota.model.Add(
                    sum(self.rota.get_duty(Duties.ICU, dd,  Shifts.ONCALL, staff)
                        for dd in range(day-denominator, day)) +
                    sum(self.rota.get_duty(Duties.ICU, dd, Shifts.DAYTIME, staff)
                        for dd in range(day-denominator, day) if dd % 7 == SATURDAY) <= numerator
                ).OnlyEnforceIf(enforced)
