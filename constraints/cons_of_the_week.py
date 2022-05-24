"""contains rules to constrain the model"""
from calendar import MONDAY, TUESDAY, WEDNESDAY, THURSDAY




from constants import Shifts, Staff, Duties
from constraints.constraintmanager import BaseConstraint


class Constraint(BaseConstraint):
    """Daytime consultant should be COTW"""
    name = 'Consultant of the week'

    @classmethod
    def definition(cls):
        yield 'consultant of the week should do Mon-Thu and Thu oncall'

    def apply_constraint(self):
        self.weekdays = [MONDAY, TUESDAY, WEDNESDAY, THURSDAY]

        for day in self.days():
            enforced = self.get_constraint_atom(day=day)
            for staff in Staff:
                cotw = self.rota.get_or_create_duty(
                    Duties.ICU_COTW,
                    day//7*7,
                    Shifts.DAYTIME,
                    staff)
                self.rota.model.Add(self.rota.get_duty(
                    Duties.ICU,
                    day,
                    Shifts.DAYTIME,
                    staff) == cotw).OnlyEnforceIf(enforced)
                if day % 7 == THURSDAY:
                    self.rota.model.Add(self.rota.get_duty(
                        Duties.ICU,
                        day, Shifts.ONCALL,
                        staff) == cotw).OnlyEnforceIf(enforced)
                self.rota.model.Add(enforced == 1)
