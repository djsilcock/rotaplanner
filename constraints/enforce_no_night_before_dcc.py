"""contains rules to constrain the model"""
from calendar import MONDAY, TUESDAY, WEDNESDAY,FRIDAY, SATURDAY


from constants import Shifts, Staff, Duties
from constraints.constraintmanager import BaseConstraint


class Constraint(BaseConstraint):
    """no night before clinical day (except Sunday and Thursday)"""
    name = "No night before DCC"

    @classmethod
    def definition(cls):

        yield 'consultant should not be oncall before DCC day'

    def apply_constraint(self):
        #self.weekdays = [MONDAY, TUESDAY, WEDNESDAY, FRIDAY, SATURDAY] 
        for day in self.days():
            enforced = self.get_constraint_atom(day=day)
            for staff in Staff:
                self.rota.model.Add(
                    sum([
                        self.rota.get_duty(
                            Duties.ICU, day+1, Shifts.DAYTIME,  staff),
                        self.rota.get_duty(
                            Duties.ICU, day, Shifts.ONCALL, staff),
                        self.rota.get_duty(Duties.THEATRE, day+1, Shifts.DAYTIME, staff)]) < 2
                ).OnlyEnforceIf(enforced)
