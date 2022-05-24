"""contains rules to constrain the model"""
from calendar import MONDAY


from constants import Shifts, Staff, Duties
from constraints.constraintmanager import BaseConstraint


class Constraint(BaseConstraint):
    """no monday after weekend"""
    name = "No Monday after weekend"

    @classmethod
    def definition(cls):

        yield 'same consultant should not do weekend and Monday oncall'

    def apply_constraint(self):
        self.weekdays = [MONDAY]
        for day in self.days():
            enforced = self.get_constraint_atom(day=day)
            if day < 7:
                continue
            for staff in Staff:
                self.rota.model.Add(self.rota.get_duty(
                    Duties.ICU, day-2, Shifts.DAYTIME, staff) +
                    self.rota.get_duty(
                        Duties.ICU, day, Shifts.ONCALL, staff) < 2
                ).OnlyEnforceIf(enforced)
                self.rota.model.Add(self.rota.get_duty(
                    Duties.ICU, day-2, Shifts.ONCALL,  staff) +
                    self.rota.get_duty(
                        Duties.ICU, day, Shifts.ONCALL,  staff) < 2
                ).OnlyEnforceIf(enforced)
                self.rota.model.Add(self.rota.get_duty(
                    Duties.ICU, day-2, Shifts.DAYTIME, staff) +
                    self.rota.get_duty(
                        Duties.ICU, day, Shifts.DAYTIME, staff) < 2
                ).OnlyEnforceIf(enforced)
                self.rota.model.Add(self.rota.get_duty(
                    Duties.ICU, day-2,  Shifts.ONCALL, staff) +
                    self.rota.get_duty(
                        Duties.ICU, day, Shifts.DAYTIME,  staff) < 2
                ).OnlyEnforceIf(enforced)
