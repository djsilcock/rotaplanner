"""contains rules to constrain the model"""
from constraints.constraintmanager import BaseConstraint
from constants import Staff
from calendar import FRIDAY,SATURDAY,SUNDAY
from constraints.core_duties import icu_daytime as get_icu_daytime, icu_oncall as get_icu_oncall

def cotw_key(day: int, staff: Staff):
    """key deriving function"""
    return ('COTWED', day//7, staff)


def isWeekend(day):
    return day % 7 in [FRIDAY,SATURDAY,SUNDAY]


class Constraint(BaseConstraint):
    """Daytime consultant should be COTW at weekend"""

    name = "Consultant of the weekend"

    @classmethod
    def definition(cls):
        yield 'consultant of the week should do Fri-Sun and Sun oncall'

    def apply_constraint(self):
        for day in self.days(isWeekend):
            enforced = self.get_constraint_atom(day=day)
            for staff in Staff:
                cotw = self.rota.get_or_create_duty_base(
                    cotw_key(day, staff)
                )
                icu_daytime = self.get_duty(
                    get_icu_daytime(day, staff)
                )
                icu_oncall = self.get_duty(get_icu_oncall(day, staff))
                self.model.Add(
                    icu_daytime == cotw
                ).OnlyEnforceIf(enforced)
                if day % 7 == SUNDAY:
                    self.model.Add(
                        icu_oncall == cotw
                    ).OnlyEnforceIf(enforced)
                self.rota.model.Add(enforced == 1)