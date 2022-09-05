

from constants import Shifts, Staff, Duties
from constraints.constraintmanager import BaseConstraint

def icu_daytime(day:int,staff:Staff):
    "An ICU daytime shift"
    return (Duties.ICU,day,Shifts.DAYTIME,staff)

def icu_oncall(day:int,staff:Staff):
    "An ICU oncall shift"
    return (Duties.ICU,day,Shifts.ONCALL,staff)

class Constraint(BaseConstraint):
    """Defines core duty set and requirement that one person is on for ICU"""
    name = 'Core duties'

    def apply_constraint(self):
        for day in self.days():
            for shift in [icu_daytime,icu_oncall]:
                for staff in Staff:
                    self.create_duty(shift(day,staff))
                self.model.AddBoolXOr(
                    [self.get_duty(shift(day,staff))
                        for staff in Staff]
                )

    def process_output(self, solver, pairs):
        for day in self.days():
            for duty in [Duties.ICU, Duties.THEATRE,Duties.LEAVE,Duties.OFF,Duties.TIMEBACK]:
                for shift in Shifts:
                    for staff in Staff:
                        if solver.Value(self.rota.get_duty(duty, day, shift, staff)):
                            yield ((staff,shift,day),duty.name)

    def build_output(self, solver, outputdict):
        for day in self.days():
            for duty in [Duties.ICU, Duties.THEATRE, Duties.LEAVE, Duties.OFF, Duties.TIMEBACK]:
                for shift in Shifts:
                    for staff in Staff:
                        if solver.Value(self.rota.get_duty(duty, day, shift, staff)):
                            outputdict.setdefault(duty.name,{}).setdefault(shift.name,{})[staff.name]=duty.name
        return outputdict


