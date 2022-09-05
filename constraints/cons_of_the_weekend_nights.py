"""contains rules to constrain the model"""
from constraints.core_duties import icu_daytime as get_icu_daytime, icu_oncall as get_icu_oncall
from constants import Staff
from calendar import FRIDAY, SATURDAY,SUNDAY


from constraints.constraintmanager import BaseConstraint


def cotw_key(day: int, staff: Staff):
    """key deriving function"""
    return ('COTWEN', day//7, staff)


def is_fri_or_sat(day):
    return day % 7 in [FRIDAY,SATURDAY]

class Constraint(BaseConstraint):
    """Evening consultant should be same for Friday and Saturday"""
    name = "Consultant of the weekend (nights)"

    @classmethod
    def definition(cls):
        yield 'same consultant should do Fri and Sat oncalls'

    
    def apply_constraint(self):
        for day in self.days(is_fri_or_sat):
            enforced = self.get_constraint_atom(day=day)
            for staff in Staff:
                cotw = self.get_or_create_duty(
                    cotw_key(day, staff)
                )
                icu_oncall = self.get_duty(get_icu_oncall(day, staff))
                self.model.Add(
                    icu_oncall == cotw
                ).OnlyEnforceIf(enforced)
                self.rota.model.Add(enforced == 1)
