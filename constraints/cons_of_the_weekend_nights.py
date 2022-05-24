"""contains rules to constrain the model"""
from calendar import FRIDAY, SATURDAY




from constants import Shifts, Staff, Duties
from constraints.constraintmanager import BaseConstraint


class Constraint(BaseConstraint):
    """Evening consultant should be same for Friday and Saturday"""
    name = "Consultant of the weekend (nights)"

    @classmethod
    def definition(cls):
        yield 'same consultant should do Fri and Sat oncalls'

    def apply_constraint(self):
        self.weekdays = [FRIDAY, SATURDAY]
        for day in self.days():
            enforced = self.get_constraint_atom(day=day)
            for staff in Staff:
                cotw = self.rota.get_or_create_duty(
                    Duties.ICU_COTW, day//7*7+4, Shifts.ONCALL, staff)
                self.rota.model.Add(self.rota.get_duty(
                    Duties.ICU, day, Shifts.ONCALL, staff) == cotw).OnlyEnforceIf(enforced)
