"""contains rules to constrain the model"""
from calendar import MONDAY




from constants import Shifts, Staff
from constraints.constraintmanager import BaseConstraint
from constraints.core_duties import icu


class Constraint(BaseConstraint):
    """maximum number of daytime ICU weeks in any given period"""
    name = "Limit ICU week frequency"

    @classmethod
    def definition(cls):

        yield 'same consultant should not do more than'
        yield {
            'name': 'numerator',
            'component': 'number'}
        yield 'weeks of ICU in any'
        yield {
            'name': 'denominator',
            'component': 'number'}

    def apply_constraint(self):
        kwargs = dict(**self.kwargs)
        denominator = kwargs.pop('denominator')
        numerator = kwargs.pop('numerator')
        self.weekdays = [MONDAY]
        enforced = self.get_constraint_atom()
        for day in self.days():
            enforced = self.get_constraint_atom(day=day)
            if day < (7*denominator):
                continue
            for staff in Staff:
                self.rota.model.Add(sum(self.get_duty(icu(Shifts.AM,dd,staff))
                                        for dd in range(day-(7*denominator), day, 7)) <= numerator
                                    ).OnlyEnforceIf(enforced)
