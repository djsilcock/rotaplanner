"""contains rules to constrain the model"""

from constants import Shifts, Staff
from constraints.constraintmanager import BaseConstraint
from constraints.core_duties import icu, nonclinical


class Constraint(BaseConstraint):
    """no night before clinical day (except Sunday and Thursday)"""
    name = "No night before DCC"

    @classmethod
    def definition(cls):

        yield 'consultant should not be oncall before DCC day'

    def apply_constraint(self):
        for day in self.days():
            enforced = self.get_constraint_atom(day=day)
            for staff in Staff:
                self.model.Add(
                    self.get_duty(nonclinical(Shifts.AM,day+1,staff))
                ).OnlyEnforceIf(
                    self.get_duty(icu(Shifts.ONCALL, day, staff))
                ).OnlyEnforceIf(enforced)
