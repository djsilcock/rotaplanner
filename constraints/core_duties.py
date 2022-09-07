

from typing import Literal
from constants import Shifts, Staff, Duties
from constraints.constraintmanager import BaseConstraint

def typecheck(shift,day,staff):
    assert isinstance(shift,Shifts)
    assert isinstance(day,int)
    assert isinstance(staff,Staff)

def icu(shift: Shifts,day: int, staff: Staff):
    "An ICU daytime shift"
    typecheck(shift,day,staff)
    return ('ICU',day,shift,staff)

def theatre(shift:Shifts,day:int, staff:Staff):
    "Theatre shift"
    typecheck(shift, day, staff)
    return ('THEATRE',day,shift,staff)

def nonclinical(shift,day,staff):
    "Not in theatre or ICU"
    typecheck(shift, day, staff)
    return ('NONCLINICAL',day,shift,staff)

def leave(shift,day,staff):
    "On Leave"
    typecheck(shift,day,staff)
    return ('LEAVE',day,shift,staff)


class Constraint(BaseConstraint):
    """Defines core duty set and requirement that one person is on for ICU"""
    name = 'Core duties'

    def apply_constraint(self):
        for day in self.days():
            for shift in ['am','pm','oncall']:
                for staff in Staff:
                    self.create_duty(icu(shift,day,staff))
                self.model.AddBoolXOr(
                    [self.get_duty(icu(shift,day,staff))
                        for staff in Staff]
                )

    def process_output(self, solver, pairs):
        for day in self.days():
            for duty in [icu,theatre,nonclinical]:
                for shift in Shifts:
                    for staff in Staff:
                        if solver.Value(self.get_duty(duty(shift, day, staff))):
                            yield ((staff,shift,day),duty.__name__.upper())

    def build_output(self, solver, outputdict):
        for day in self.days():
            for duty in [Duties.ICU, Duties.THEATRE, Duties.LEAVE, Duties.OFF, Duties.TIMEBACK]:
                for shift in Shifts:
                    for staff in Staff:
                        if solver.Value(self.rota.get_duty(duty, day, shift, staff)):
                            outputdict.setdefault(duty.name,{}).setdefault(shift.name,{})[staff.name]=duty.name
        return outputdict


