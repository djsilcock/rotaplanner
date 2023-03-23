"""contains rules to constrain the model"""
from calendar import MONDAY


from config import Shifts, Staff
from constraints.core_duties import icu
from constraints.base import BaseConstraint

class Config():
    def get_config_interface(self):
        yield 'same consultant should not do weekend and Monday oncall'

from constraints.constraint_store import register_constraint

@register_constraint('enforce_no_monday_after_weekend')
class Constraint(BaseConstraint):
    """no monday after weekend"""
    name = "No Monday after weekend"

    config_class=Config

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
