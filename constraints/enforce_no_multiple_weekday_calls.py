"""contains rules to constrain the model"""
from calendar import MONDAY, TUESDAY, WEDNESDAY




from constants import Shifts, Staff, Duties
from constraints.constraintmanager import BaseConstraint


class Constraint(BaseConstraint):
    """no more than 1 weekday oncall"""
    #print('No multiple weekday oncalls')
    name = "No multiple weekday oncalls"

    @classmethod
    def definition(cls):

        yield 'same consultant should not do more than one Mon-Wed oncall'

    def apply_constraint(self):
        self.weekdays = [MONDAY, TUESDAY, WEDNESDAY]
        days_to_check = list(self.days())
        for day in days_to_check:
            enforced = self.get_constraint_atom(day=day)
            start_of_week = (day // 7)*7
            for staff in Staff:
                sum_of_duties = sum(
                    self.rota.get_duty(Duties.ICU,
                                       start_of_week+dd, Shifts.ONCALL, staff)
                    for dd in [0, 1, 2]
                    if dd+start_of_week in days_to_check)
                self.rota.model.Add(sum_of_duties < 2).OnlyEnforceIf(enforced)
