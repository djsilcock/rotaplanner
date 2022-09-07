"""contains rules to constrain the model"""

from constants import Shifts, Staff, Duties
from constraints.constraintmanager import BaseConstraint
from constraints.core_duties import leave, nonclinical, theatre, typecheck, icu


def icu_timeshift(shift, day, staff):
    "ICU duty as a timeshifted session"
    typecheck(shift, day, staff)
    return ('ICU_TS', shift, day, staff)


def icu_jobplanned(shift, day, staff):
    "ICU duty in jobplanned time"
    typecheck(shift, day, staff)
    return ('ICU_JP', shift, day, staff)


def time_back(shift, day, staff):
    "Time back from timeshifted sessions"
    typecheck(shift, day, staff)
    return ('TIMEBACK', shift, day, staff)


def jobplanned_nonclinical(shift, day, staff):
    "Jobplanned nonclinical session"
    typecheck(shift, day, staff)
    return('JP_NONCLINICAL', shift, day, staff)


def jobplanned_dcc(shift, day, staff):
    "Jobplanned DCC"
    typecheck(shift, day, staff)
    return ('JP_DCC', shift, day, staff)


def convert_working_days(day_shift_str):
    "Convert eg 'Monday AM' to (0,Shifts.AM)"
    try:
        if isinstance(day_shift_str, str):
            daystr, shiftstr = day_shift_str.split()
            day = 'mo tu we th fr sa su'.split().index(
                daystr.lower()[0:2])
            shift = Shifts[shiftstr]
            return (day, shift)
        else:
            raise ValueError
    except (ValueError, KeyError) as exc:
        raise ValueError(
            f'Did not recognise {day} in working days list') from exc


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
            'options': [f'{day} {shift}'
                for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
                for shift in ('AM', 'PM')]

        }

    def apply_constraint(self):
        """apply jobplans"""

        working_days = list(
            map(convert_working_days, self.kwargs.get('working_days')))
        staff = Staff[self.kwargs.get('staff').upper()]
        for day in self.days():
            self.rota.model.Add(self.rota.get_duty(
                                Duties.THEATRE, day, Shifts.ONCALL, staff) == 0)
            for shift in (Shifts.AM, Shifts.PM):
                is_jobplanned = self.get_or_create_duty(
                    jobplanned_dcc(shift, day, staff))
                is_icu_timeshift = self.get_or_create_duty(
                    icu_timeshift(shift, day, staff))
                is_icu_jobplanned = self.get_or_create_duty(
                    icu_jobplanned(shift, day, staff))
                is_time_back = self.get_or_create_duty(
                    time_back(shift, day, staff))
                is_icu = self.get_or_create_duty(
                    icu(shift, day, staff))
                is_nonclinical = self.get_or_create_duty(
                    nonclinical(shift, day, staff))
                is_theatre = self.get_or_create_duty(
                    theatre(shift, day, staff))
                is_on_leave = self.get_or_create_duty(
                    leave(shift, day, staff))

                self.model.Add(is_jobplanned == (
                    (day % 7, shift) in working_days))

                implications = [
                    (is_icu_timeshift, is_jobplanned.Not()),
                    (is_icu_jobplanned, is_jobplanned),
                    (is_icu_timeshift, is_icu),
                    (is_icu_jobplanned, is_icu),
                    (is_time_back, is_jobplanned),
                    (is_time_back, is_nonclinical)
                ]

                for if_this, then_that in implications:
                    self.model.AddImplication(if_this, then_that)

                self.model.AddBoolOr(
                    [is_icu, is_theatre, is_time_back, is_on_leave]).OnlyEnforceIf(is_jobplanned)
                self.model.AddBoolOr([is_icu_timeshift, is_on_leave]).OnlyEnforceIf(
                    is_jobplanned.Not())

        self.rota.model.Add(
            sum(self.get_duty(is_icu_timeshift(shift, day, staff))
                for day in self.days() for shift in (Shifts.AM, Shifts.PM)) >=
            sum(self.get_duty(is_time_back(shift, day, staff))
                for day in self.days() for shift in (Shifts.AM, Shifts.PM)))
