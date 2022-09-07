"""contains rules to constrain the model"""
from calendar import MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY

from constants import Shifts, Staff, Duties
from constraints.constraintmanager import BaseConstraint
from constraints.core_duties import icu, typecheck


def locum_icu(shift: Shifts, day: int, staff: Staff):
    "Locum ICU shift"
    typecheck(shift, day, staff)
    return ('LOCUM_ICU', day, shift, staff)

def quota_icu(shift: Shifts, day: int, staff: Staff):
    "Quota ICU shift"
    typecheck(shift, day, staff)
    return ('LOCUM_ICU', day, shift, staff)

def locum(shift:Shifts,day:int):
    "Is shift a locum"
    assert isinstance(shift,Shifts)
    assert isinstance(day,int)
    weekday=day%7
    if weekday in [MONDAY,TUESDAY,WEDNESDAY,THURSDAY]:
        if shift in [Shifts.AM,Shifts.PM]:
            return ('COTW_LOCUM',day//7)
        return ('WEEKDAY_ONCALL_LOCUM',day)
    if weekday in [FRIDAY,SATURDAY,SUNDAY] and shift in [Shifts.AM,Shifts.PM]:
        return ('WEEKEND_LOCUM',day//7)
    if weekday == SUNDAY and shift==Shifts.ONCALL:
        return ('WEEKEND_LOCUM',day//7)
    if weekday in [FRIDAY,SATURDAY] and shift ==Shifts.ONCALL:
        return ('WEEKEND_ONCALL_LOCUM',day//7)
    
class Constraint(BaseConstraint):
    """Some shifts are marked as locum"""
    name = "Some shifts are Locum"

    @classmethod
    def definition(cls):
        yield 'some shifts will be locum'

    def apply_constraint(self):
        for day in self.days():            
            for shift in Shifts:
                for staff in Staff:
                    shift_is_locum = self.get_or_create_duty(locum(shift, day))
                    locum_session = self.get_or_create_duty(locum_icu(shift,day,staff))
                    quota_session = self.get_or_create_duty(quota_icu(shift,day,staff))
                    is_icu=self.get_duty(icu(shift,day,staff))

                    self.model.AddImplication(locum_session,shift_is_locum)
                    self.model.AddImplication(locum_session,is_icu)
                    self.model.AddImplication(quota_session,shift_is_locum.Not())
                    self.model.AddImplication(quota_session,is_icu)

                    self.model.AddBoolOr([locum_session,quota_session]).OnlyEnforceIf(is_icu)


    def process_output(self, solver, pairs):
        for ((staff,shift,day),value) in pairs:
            if solver.Value(self.rota.get_duty(Duties.LOCUM_ICU,day,shift,staff)):
                yield((staff,shift,day),'LOCUM_ICU')
            else:
                yield((staff,shift,day),value)

