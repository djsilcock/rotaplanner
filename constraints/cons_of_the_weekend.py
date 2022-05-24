"""contains rules to constrain the model"""
from calendar import FRIDAY, SATURDAY, SUNDAY


from constants import Shifts, Staff, Duties
from constraints.constraintmanager import BaseConstraint


class Constraint(BaseConstraint):
    """Daytime consultant should be COTW at weekend"""

    name = "Consultant of the weekend"

    @classmethod
    def definition(cls):
        yield 'consultant of the week should do Fri-Sun and Sun oncall'

    def apply_constraint(self):
        self.weekdays = [FRIDAY, SATURDAY, SUNDAY]

        for day in self.days():
            for staff in Staff:
                enforced = self.get_constraint_atom(day=day)
                cotw = self.rota.get_or_create_duty(
                    Duties.ICU_COTW,
                    day//7*7+4,
                    Shifts.DAYTIME,
                    staff)
                self.rota.model.Add(self.rota.get_duty(
                    Duties.ICU,
                    day,
                    Shifts.DAYTIME,
                    staff) == cotw).OnlyEnforceIf(enforced)
                if day % 7 == SUNDAY:
                    self.rota.model.Add(self.rota.get_duty(
                        Duties.ICU,
                        day,
                        Shifts.ONCALL,
                        staff) == cotw).OnlyEnforceIf(enforced)
