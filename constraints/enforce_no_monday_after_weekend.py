"""contains rules to constrain the model"""
from calendar import MONDAY


from constants import Shifts, Staff
from constraints.core_duties import icu
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
                sat_daytime = self.get_duty(icu(Shifts.AM, day-2, staff))
                sat_oncall = self.get_duty(icu(Shifts.ONCALL, day-2, staff))
                mon_daytime = self.get_duty(icu(Shifts.AM, day, staff))
                mon_oncall = self.get_duty(icu(Shifts.ONCALL, day, staff))

                prohibited_combinations=[
                    (sat_daytime,mon_daytime),
                    (sat_daytime,mon_oncall),
                    (sat_oncall,mon_daytime),
                    (sat_oncall,mon_oncall)
                    ]
                for left,right in prohibited_combinations:
                    self.model.AddBoolOr([left.Not(),right.Not()]).OnlyEnforceIf(enforced)
