"""contains rules to constrain the model"""
from calendar import MONDAY, TUESDAY, WEDNESDAY, THURSDAY
from constraints.core_duties import icu_daytime as get_icu_daytime,icu_oncall as get_icu_oncall

from constants import Staff
from constraints.constraintmanager import BaseConstraint

def cotw_key(day:int,staff:Staff):
    """key deriving function"""
    return ('COTW',day//7,staff)

def isWeekday(day):
    return day % 7 in [MONDAY, TUESDAY, WEDNESDAY, THURSDAY]

class Constraint(BaseConstraint):
    """Daytime consultant should be COTW"""
    name = 'Consultant of the week'

    @classmethod
    def definition(cls):
        yield 'consultant of the week should do Mon-Thu and Thu oncall'

    def apply_constraint(self):     
        for day in self.days(isWeekday):
            enforced = self.get_constraint_atom(day=day)
            for staff in Staff:
                cotw = self.rota.get_or_create_duty_base(
                    cotw_key(day,staff)
                    )
                icu_daytime = self.get_duty(
                    get_icu_daytime(day,staff)
                    )
                icu_oncall = self.get_duty(get_icu_oncall(day,staff))
                self.model.Add(
                    icu_daytime == cotw
                    ).OnlyEnforceIf(enforced)
                if day % 7 == THURSDAY:
                    self.model.Add(
                        icu_oncall == cotw
                        ).OnlyEnforceIf(enforced)
                self.rota.model.Add(enforced == 1)
