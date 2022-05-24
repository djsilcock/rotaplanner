"""contains rules to constrain the model"""
from calendar import THURSDAY



from constants import Shifts, Staff, Duties
from constraints.constraintmanager import BaseConstraint


class Constraint(BaseConstraint):
    """week not followed by weekend"""
    name = "Weekend not following week"

    @classmethod
    def definition(cls):

        yield 'an ICU weekend should not follow an ICU week'

    def apply_constraint(self):
        self.weekdays = [THURSDAY]
        for day in self.days():
            enforced = self.get_constraint_atom(day=day)
            for staff in Staff:
                self.rota.model.Add(
                    self.rota.get_duty(Duties.ICU, day, Shifts.DAYTIME, staff) +
                    self.rota.get_duty(Duties.ICU, day+1,
                                       Shifts.DAYTIME, staff) < 2
                ).OnlyEnforceIf(enforced)
                self.rota.model.Add(
                    self.rota.get_duty(Duties.ICU, day, Shifts.DAYTIME, staff) +
                    self.rota.get_duty(Duties.ICU, day+1,
                                       Shifts.ONCALL,  staff) < 2
                ).OnlyEnforceIf(enforced)
