"""contains rules to constrain the model"""
from calendar import MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY

from constants import Shifts, Staff, Duties
from constraints.constraintmanager import BaseConstraint


class Constraint(BaseConstraint):
    """Some shifts are marked as locum"""
    name = "Some shifts are Locum"

    @classmethod
    def definition(cls):
        yield 'some shifts will be locum'

    def apply_constraint(self):
        for day in self.days():
            day_is_locum = self.rota.create_duty(
                Duties.IS_LOCUM, day, Shifts.DAYTIME, 0)
            oncall_is_locum = self.rota.create_duty(
                Duties.IS_LOCUM, day, Shifts.ONCALL, 0)
            if day % 7 in [MONDAY, TUESDAY, WEDNESDAY, THURSDAY]:
                cotwl = self.rota.get_or_create_duty(
                    Duties.ICU_LOCUM_COTW,
                    day-day%7,
                    Shifts.DAYTIME,
                    0)
            if day % 7 in [FRIDAY, SATURDAY, SUNDAY]:
                cotwl = self.rota.get_or_create_duty(
                    Duties.ICU_LOCUM_COTW,
                    day-day%7+4,
                    Shifts.DAYTIME,
                    0)
            self.rota.model.Add(cotwl == day_is_locum)
            if day % 7 in [FRIDAY, SATURDAY]:
                cotwen = self.rota.get_or_create_duty(
                    Duties.ICU_LOCUM_COTW, day-day%7+4, Shifts.ONCALL, 0)
                self.rota.model.Add(cotwen == oncall_is_locum)

            if day % 7 == SUNDAY:
                self.rota.model.Add(cotwl == oncall_is_locum)
            
            for shift in Shifts:
                for staff in Staff:
                    locum_session = self.rota.create_duty(
                        Duties.LOCUM_ICU, day, shift, staff)
                    quota_session = self.rota.create_duty(
                        Duties.QUOTA_ICU, day, shift, staff)
                    any_session = self.rota.get_duty(
                        Duties.ICU, day, shift, staff)
                    self.rota.model.Add(
                        locum_session+quota_session == any_session)
            self.rota.model.AddAbsEquality(
                day_is_locum,
                sum(self.rota.get_duty(
                    Duties.LOCUM_ICU,
                    day,
                    Shifts.DAYTIME, staff)
                    for staff in Staff))
            self.rota.model.AddAbsEquality(
                oncall_is_locum,
                sum(self.rota.get_duty(
                    Duties.LOCUM_ICU,
                    day,
                    Shifts.ONCALL, staff)
                    for staff in Staff))

    def process_output(self, solver, pairs):
        for ((staff,shift,day),value) in pairs:
            if solver.Value(self.rota.get_duty(Duties.LOCUM_ICU,day,shift,staff)):
                yield((staff,shift,day),'LOCUM_ICU')
            else:
                yield((staff,shift,day),value)

