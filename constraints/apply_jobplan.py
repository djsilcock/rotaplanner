"""contains rules to constrain the model"""

from constants import Shifts, Staff, Duties
from constraints.constraintmanager import BaseConstraint


class Constraint(BaseConstraint):
    """Apply jobplan to staffmember"""
    name = "Apply jobplans"

    @classmethod
    def definition(cls):
        yield {
            'component': 'select',
            'name': 'staff',
            'options': [s.name for s in Staff]}
        yield 'has jobplanned DCC on'
        yield {
            'component': 'multiselect',
            'name': 'working_days',
            'options': 'Monday Tuesday Wednesday Thursday Friday'.split()}

    def apply_constraint(self):
        """apply jobplans"""
        def convert_working_days(day):
            try:
                if isinstance(day, int):
                    if day > 6:
                        raise ValueError
                    return day
                elif isinstance(day, str):
                    day = day.lower()[0:2]
                    day = 'mo tu we th fr sa su'.split().index(day)
                    return day
                else:
                    raise ValueError
            except ValueError as exc:
                raise ValueError(
                    f'Did not recognise {day} in working days list') from exc
        working_days = list(
            map(convert_working_days, self.kwargs.get('working_days')))
        staff = Staff[self.kwargs.get('staff').upper()]
        for day in self.days():
            self.rota.model.Add(self.rota.get_duty(
                                Duties.THEATRE, day, Shifts.ONCALL, staff) == 0)
            for duty in [Duties.ICU_TS,Duties.ICU_JP,Duties.TIMEBACK]:
                self.rota.get_or_create_duty(
                    duty, day, Shifts.DAYTIME, staff)
            if day % 7 in working_days:
                self.rota.model.Add(self.rota.get_duty(
                    Duties.OFF, day, Shifts.DAYTIME, staff) == 0)
                self.rota.model.Add(self.rota.get_duty(
                    Duties.ICU_TS,day,Shifts.DAYTIME,staff)==0)
                #self.rota.model.Add(self.rota.get_duty(
                #    Duties.LEAVE,day,Shifts.DAYTIME,staff)==
                #    self.rota.get_duty(
                #    Duties.DROPPED_SESSION, day, Shifts.DAYTIME, staff)
                #)
            else:
                self.rota.model.Add(self.rota.get_duty(
                    Duties.THEATRE, day, Shifts.DAYTIME, staff) == 0)
                self.rota.model.Add(self.rota.get_duty(
                    Duties.ICU_JP, day, Shifts.DAYTIME, staff) == 0)
                self.rota.model.Add(self.rota.get_duty(
                    Duties.TIMEBACK, day, Shifts.DAYTIME, staff)==0)
                #self.rota.model.Add(self.rota.get_duty(
                #    Duties.DROPPED_SESSION, day, Shifts.DAYTIME, staff) == 0)

            self.rota.model.Add(self.rota.get_duty(
                Duties.ICU_TS, day, Shifts.DAYTIME, staff)+
                self.rota.get_duty(
                Duties.ICU_JP, day, Shifts.DAYTIME, staff) == self.rota.get_duty(
                Duties.ICU, day, Shifts.DAYTIME, staff))
        self.rota.model.Add(
            sum(self.rota.get_duty(
            Duties.ICU_TS, day, Shifts.DAYTIME, staff) for day in self.days()) >=
            sum(self.rota.get_duty(
                Duties.TIMEBACK, day, Shifts.DAYTIME, staff) for day in self.days()))
