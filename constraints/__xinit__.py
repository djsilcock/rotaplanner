"""contains rules to constrain the model"""
from calendar import MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY

from enum import Enum, auto


from constants import Shifts, Staff, Duties
from constraints.constraintmanager import BaseConstraint


class CoreDuties(BaseConstraint):
    """Defines core duty set and requirement that one person is on for ICU"""
    name = 'Core duties'

    def apply_constraint(self):
        for day in self.days():
            for shift in Shifts:
                for staff in Staff:
                    self.rota.create_duty(Duties.ICU, day, shift, staff)
                self.rota.model.Add(
                    sum(self.rota.get_duty(Duties.ICU, day, shift, staff)
                        for staff in Staff) == 1
                )

    def event_stream(self, solver, event_stream):
        yield from event_stream
        for day in self.days():
            for staff_member in Staff:
                for shift in Shifts:
                    for duty in [Duties.ICU, Duties.THEATRE]:
                        if solver.Value(self.rota.get_duty(duty, day, shift, staff_member)):
                            yield (
                                {'type': 'duty',
                                 'dutyType': duty.name,
                                 'day': day,
                                 'shift': shift.name,
                                 'name': staff_member.name})


class ConsOfTheWeek(BaseConstraint):
    """Daytime consultant should be COTW"""
    name = 'Consultant of the week'

    @classmethod
    def definition(cls):
        yield 'consultant of the week should do Mon-Thu and Thu oncall'

    def apply_constraint(self):
        self.weekdays = [MONDAY, TUESDAY, WEDNESDAY, THURSDAY]

        for day in self.days():
            enforced = self.get_constraint_atom(day=day)
            for staff in Staff:
                cotw = self.rota.get_or_create_duty(
                    Duties.ICU_COTW,
                    day//7*7,
                    Shifts.DAYTIME,
                    staff)
                self.rota.model.Add(self.rota.get_duty(
                    Duties.ICU,
                    day,
                    Shifts.DAYTIME,
                    staff) == cotw).OnlyEnforceIf(enforced)
                if day % 7 == THURSDAY:
                    self.rota.model.Add(self.rota.get_duty(
                        Duties.ICU,
                        day, Shifts.ONCALL,
                        staff) == cotw).OnlyEnforceIf(enforced)
                self.rota.model.Add(enforced == 1)


class ConsOfTheWeekEnd(BaseConstraint):
    """Daytime consultant should be COTW at weekend"""

    name = "Consultant of the weekend"

    @classmethod
    def definition(cls):
        yield 'consultant of the week should do Fri-Sun and Sun oncall'

    def apply_constraint(self):
        self.weekdays = [FRIDAY, SATURDAY, SUNDAY]

        for day in self.days():
            for staff in Staff:
                enforced = self.get_constraint_atom(day=day)
                cotw = self.rota.get_or_create_duty(
                    Duties.ICU_COTW,
                    day//7*7+4,
                    Shifts.DAYTIME,
                    staff)
                self.rota.model.Add(self.rota.get_duty(
                    Duties.ICU,
                    day,
                    Shifts.DAYTIME,
                    staff) == cotw).OnlyEnforceIf(enforced)
                if day % 7 == SUNDAY:
                    self.rota.model.Add(self.rota.get_duty(
                        Duties.ICU,
                        day,
                        Shifts.ONCALL,
                        staff) == cotw).OnlyEnforceIf(enforced)


class ConsOfTheWeekendNights(BaseConstraint):
    """Evening consultant should be same for Friday and Saturday"""
    name = "Consultant of the weekend (nights)"

    @classmethod
    def definition(cls):
        yield 'same consultant should do Fri and Sat oncalls'

    def apply_constraint(self):
        self.weekdays = [FRIDAY, SATURDAY]
        for day in self.days():
            enforced = self.get_constraint_atom(day=day)
            for staff in Staff:
                cotw = self.rota.get_or_create_duty(
                    Duties.ICU_COTW, day//7*7+4, Shifts.ONCALL, staff)
                self.rota.model.Add(self.rota.get_duty(
                    Duties.ICU, day, Shifts.ONCALL, staff) == cotw).OnlyEnforceIf(enforced)


class SomeShiftsAreLocum(BaseConstraint):
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
                    day//7,
                    Shifts.DAYTIME,
                    0)
            if day % 7 in [FRIDAY, SATURDAY, SUNDAY]:
                cotwl = self.rota.get_or_create_duty(
                    Duties.ICU_LOCUM_COTW,
                    day//7+4,
                    Shifts.DAYTIME,
                    0)
            self.rota.model.Add(cotwl == day_is_locum)
            if day % 7 in [FRIDAY, SATURDAY]:
                cotwen = self.rota.get_or_create_duty(
                    Duties.ICU_LOCUM_COTW, day//7+4, Shifts.ONCALL, 0)
                self.rota.model.Add(cotwen == oncall_is_locum)

            if day % 7 == SUNDAY:
                self.rota.model.Add(cotwl == oncall_is_locum)
            if day % 7 == FRIDAY:
                self.rota.model.Add(oncall_is_locum == self.rota.get_duty(
                    Duties.IS_LOCUM, day, Shifts.ONCALL, 0))
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

    def event_stream(self, solver, event_stream):
        for event in event_stream:
            if event['type'] == 'duty':
                shift = event['shift']
                shift = Shifts[shift]
                day = event['day']
                if day not in self.days():
                    continue
                islocum = solver.Value(self.rota.get_duty(
                    Duties.IS_LOCUM, day, shift, 0))
                yield dict(**event, locum=islocum)
                continue
            yield event


class ApplyLeavebook(BaseConstraint):
    """Leavebook entry"""

    def apply_constraint(self):
        leavebook = self.kwargs.get('leavebook')
        for staff in Staff:
            for shift in Shifts:
                for day in self.days():
                    if leavebook.get((staff, shift, day), None) == Duties.LEAVE:
                        self.rota.model.Add(self.rota.get_duty(
                            Duties.LEAVE, day, shift, staff) == 1)
                    else:
                        self.rota.model.Add(self.rota.get_duty(
                            Duties.LEAVE, day, shift, staff) == 0)
                    if leavebook.get((staff, shift, day), None) == Duties.ICU:
                        self.rota.model.Add(self.rota.get_duty(
                            Duties.ICU, day, shift, staff) == 1)

    def event_stream(self, solver, event_stream):
        leavebook = self.kwargs.get('leavebook')
        for event in event_stream:
            if event['type'] == 'duty' and event['dutyType'] == 'ICU':
                staff = Staff[event['name']]
                shift = Shifts[event['shift']]
                day = event['day']
                newevent = event.copy()
                newevent.update(
                    {'dutyType': 'DEFINITE_ICU'
                        if leavebook.get((staff, shift, day), '') == Duties.ICU
                        else 'ICU'})
                yield newevent
            else:
                yield event

        for (staff, shift, day) in leavebook:
            if leavebook[(staff, shift, day)] == Duties.LEAVE:
                yield {
                    'type': 'leave',
                    'shift': shift.name,
                    'day': day,
                    'staff': staff.name
                }


class NoMultiTasking(BaseConstraint):
    """Block duties which cannot exist simultaneously"""
    name = "No multi-tasking"

    def apply_constraint(self):
        for day in self.days():
            for staff in Staff:
                for shift in Shifts:
                    dutyset = {Duties.ICU, Duties.THEATRE,
                               Duties.OFF, Duties.LEAVE}
                    self.rota.model.Add(sum(self.rota.get_or_create_duty(duty, day, shift, staff)
                                            for duty in dutyset) == 1)


class ApplyJobPlan(BaseConstraint):
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
            with open('logfile.txt', 'a', encoding='utf-8') as logfile:
                if day % 7 < 5:
                    # is a weekday
                    if day % 7 in working_days:
                        self.rota.model.Add(self.rota.get_duty(
                            Duties.OFF, day, Shifts.DAYTIME, staff) == 0)
                        print(
                            (f'jobplan {staff} on day {day%7} - working\n'), file=logfile)
                    else:
                        self.rota.model.Add(self.rota.get_duty(
                            Duties.THEATRE, day, Shifts.DAYTIME, staff) == 0)
                        print(
                            f'jobplan {staff} on day {day%7} - not working', file=logfile)


class EnforceWeekendNotFollowingWeek(BaseConstraint):
    """week not followed by weekend"""
    name = "Weekend not following week"

    @classmethod
    def definition(cls):

        yield 'an ICU weekend should not follow an ICU week'

    def apply_constraint(self):
        self.weekdays = [THURSDAY]
        for day in self.days():
            enforced = self.get_constraint_atom(day=day)
            for staff in Staff:
                self.rota.model.Add(
                    self.rota.get_duty(Duties.ICU, day, Shifts.DAYTIME, staff) +
                    self.rota.get_duty(Duties.ICU, day+1,
                                       Shifts.DAYTIME, staff) < 2
                ).OnlyEnforceIf(enforced)
                self.rota.model.Add(
                    self.rota.get_duty(Duties.ICU, day, Shifts.DAYTIME, staff) +
                    self.rota.get_duty(Duties.ICU, day+1,
                                       Shifts.ONCALL,  staff) < 2
                ).OnlyEnforceIf(enforced)


class EnforceNoMultipleWeekdayCalls(BaseConstraint):
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


class EnforceNoNightBeforeDcc(BaseConstraint):
    """no night before clinical day (except Sunday and Thursday)"""
    name = "No night before DCC"

    @classmethod
    def definition(cls):

        yield 'consultant should not be oncall before DCC day'

    def apply_constraint(self):
        self.weekdays = [MONDAY, TUESDAY, WEDNESDAY, FRIDAY, SATURDAY]

        with open('logfile.txt', 'a', encoding='utf-8') as logfile:
            print(f'{self.startdate} {self.enddate} {self.exclusions}', file=logfile)
            for day in self.days():
                enforced = self.get_constraint_atom(day=day)
                print(f'applying for {day}', file=logfile)
                for staff in Staff:
                    self.rota.model.Add(
                        sum([
                            self.rota.get_duty(
                                Duties.ICU, day+1, Shifts.DAYTIME,  staff),
                            self.rota.get_duty(
                                Duties.ICU, day, Shifts.ONCALL, staff),
                            self.rota.get_duty(Duties.THEATRE, day+1, Shifts.DAYTIME, staff)]) < 2
                    ).OnlyEnforceIf(enforced)


class EnforceNoMondayAfterWeekend(BaseConstraint):
    """no monday after weekend"""
    name = "No Monday after weekend"

    @classmethod
    def definition(cls):

        yield 'same consultant should not do weekend and Monday oncall'

    def apply_constraint(self):
        self.weekdays = [MONDAY]
        for day in self.days():
            enforced = self.get_constraint_atom(day=day)
            if day < 7:
                continue
            for staff in Staff:
                self.rota.model.Add(self.rota.get_duty(
                    Duties.ICU, day-2, Shifts.DAYTIME, staff) +
                    self.rota.get_duty(
                        Duties.ICU, day, Shifts.ONCALL, staff) < 2
                ).OnlyEnforceIf(enforced)
                self.rota.model.Add(self.rota.get_duty(
                    Duties.ICU, day-2, Shifts.ONCALL,  staff) +
                    self.rota.get_duty(
                        Duties.ICU, day, Shifts.ONCALL,  staff) < 2
                ).OnlyEnforceIf(enforced)
                self.rota.model.Add(self.rota.get_duty(
                    Duties.ICU, day-2, Shifts.DAYTIME, staff) +
                    self.rota.get_duty(
                        Duties.ICU, day, Shifts.DAYTIME, staff) < 2
                ).OnlyEnforceIf(enforced)
                self.rota.model.Add(self.rota.get_duty(
                    Duties.ICU, day-2,  Shifts.ONCALL, staff) +
                    self.rota.get_duty(
                        Duties.ICU, day, Shifts.DAYTIME,  staff) < 2
                ).OnlyEnforceIf(enforced)


class EnforceMaxWeekendsPerPeriod(BaseConstraint):
    """Maximum x weekends (day or night) in any y weekends"""
    name = "Limit Weekend Frequency"

    @classmethod
    def definition(cls):

        yield 'same consultant should not do more than'
        yield {
            'name': 'numerator',
            'component': 'number'}
        yield 'weekends in any'
        yield {
            'name': 'denominator',
            'component': 'number'}

    def apply_constraint(self):
        #print(f'Maximum {numerator} weekends in {denominator}...')

        kwargs = dict(**self.kwargs)
        denominator = kwargs.pop('denominator')
        numerator = kwargs.pop('numerator')
        self.weekdays = [SATURDAY]
        for day in self.days():
            enforced = self.get_constraint_atom(day=day)
            if day < (7*denominator):
                continue
            for staff in Staff:

                self.rota.model.Add(sum(self.rota.get_duty(Duties.ICU, dd, Shifts.DAYTIME, staff)
                                        for dd in range(day-(7*denominator), day, 7)) +
                                    sum(self.rota.get_duty(Duties.ICU, dd,  Shifts.ONCALL, staff)
                                        for dd in range(day-(7*denominator), day, 7)) <= numerator
                                    ).OnlyEnforceIf(enforced)


class EnforceMaxWeeksPerPeriod(BaseConstraint):
    """maximum number of daytime ICU weeks in any given period"""
    name = "Limit ICU week frequency"

    @classmethod
    def definition(cls):

        yield 'same consultant should not do more than'
        yield {
            'name': 'numerator',
            'component': 'number'}
        yield 'weeks of ICU in any'
        yield {
            'name': 'denominator',
            'component': 'number'}

    def apply_constraint(self):
        kwargs = dict(**self.kwargs)
        denominator = kwargs.pop('denominator')
        numerator = kwargs.pop('numerator')
        self.weekdays = [MONDAY]
        enforced = self.get_constraint_atom()
        for day in self.days():
            enforced = self.get_constraint_atom(day=day)
            if day < (7*denominator):
                continue
            for staff in Staff:
                self.rota.model.Add(sum(self.rota.get_duty(Duties.ICU, dd, Shifts.DAYTIME, staff)
                                        for dd in range(day-(7*denominator), day, 7)) <= numerator
                                    ).OnlyEnforceIf(enforced)


class EnforceMaxOncallsPerPeriod(BaseConstraint):
    """Maximum number of oncalls per given number of days"""
    name = "Limit oncall frequency"

    @classmethod
    def definition(cls):

        yield 'same consultant should not do more than'
        yield {
            'name': 'numerator',
            'component': 'number'}
        yield 'oncalls in any'
        yield {
            'name': 'denominator',
            'component': 'number'}
        yield 'consecutive days'

    def apply_constraint(self):
        kwargs = dict(**self.kwargs)
        denominator = kwargs.pop('denominator')
        numerator = kwargs.pop('numerator')
        enforced = self.get_constraint_atom()
        for day in self.days():
            enforced = self.get_constraint_atom(day=day)
            if day < denominator:
                continue
            for staff in Staff:
                self.rota.model.Add(
                    sum(self.rota.get_duty(Duties.ICU, dd,  Shifts.ONCALL, staff)
                        for dd in range(day-denominator, day)) +
                    sum(self.rota.get_duty(Duties.ICU, dd, Shifts.DAYTIME, staff)
                        for dd in range(day-denominator, day) if dd % 7 == SATURDAY) <= numerator
                ).OnlyEnforceIf(enforced)


class EnforceAcceptableDeviation(BaseConstraint):
    """Maximum deviation from target number of shifts of any given type (excluding locums)"""
    name = "Minimise deviation from average"

    @classmethod
    def definition(cls):

        yield 'same consultant should not be more than'
        yield {
            'name': 'deviation',
            'component': 'number'}
        yield {
            'name': 'shift',
            'component': 'select',
            'options': [
                'Weekend oncall',
                'Weekend daytime',
                'Weekday oncall',
                'Weekday daytime',
                'Any weekend']}
        yield 'shifts above or below target'

    def apply_constraint(self):
        kwargs = dict(**self.kwargs)
        shift = kwargs.pop('shift').lower()
        deviation = kwargs.pop('deviation')
        enforced = self.get_constraint_atom()
        (days, shifts) = {
            'weekend oncall': ([FRIDAY, SATURDAY, SUNDAY], [Shifts.ONCALL]),
            'weekend daytime': ([FRIDAY, SATURDAY, SUNDAY], [Shifts.DAYTIME]),
            'weekday oncall': ([MONDAY, TUESDAY, WEDNESDAY, THURSDAY], [Shifts.ONCALL]),
            'weekday daytime': ([FRIDAY, SATURDAY, SUNDAY], [Shifts.DAYTIME]),
            'any weekend': ([FRIDAY, SATURDAY, SUNDAY], [Shifts.ONCALL, Shifts.DAYTIME])

        }[shift]
        self.weekdays = [SATURDAY]
        for staff in Staff:
            for day in self.days():
                for shift in Shifts:
                    duties = [self.rota.get_duty(Duties.ICU, dd, shift, staff) for dd in range(
                        0, day) if day in days and shift in shifts]
                    tally = self.rota.model.NewIntVar(
                        0,
                        self.rota.rota_cycles*7*self.rota.slots_on_rota,
                        f'tally{day}{shift}{staff}')
                    self.rota.model.AddAbsEquality(
                        tally,
                        sum(duties))
                    target = self.rota.model.NewIntVar(
                        0,
                        self.rota.rota_cycles*7*self.rota.slots_on_rota,
                        'target')
                    self.rota.model.Add(target == (
                        len(duties)//self.rota.people_on_rota)).OnlyEnforceIf(enforced)
                    delta = self.rota.model.NewIntVar(-deviation,
                                                      deviation,
                                                      f'delta{day}{shift}{staff}')
                    self.rota.model.Add(
                        delta == tally-target).OnlyEnforceIf(enforced)


class LimitLocumShifts(BaseConstraint):
    """limit locum shifts for which filter is true"""
    name = "Limit Locum shifts"

    @classmethod
    def definition(cls):
        names = [s.name.title() for s in Staff]
        return ['Between',
                dict(component='date', name='startDate'),
                'and',
                dict(component='date', name='endDate'),
                dict(component='multiselect', name='staff', options=names),
                'should',
                dict(
                    component='select',
                    name='collectively',
                    options=['individually', 'collectively'],
                    displayif='values.staff.length>1'),
                'do',
                dict(
                    component='select',
                    name='moreless',
                    options=['at least', 'at most', 'between']),
                dict(
                    component='number',
                    name='minimum',
                    displayif='(values.moreless=="at least")||(values.moreless=="between")'),
                dict(
                    component='text',
                    content='and',
                    displayif='(values.moreless=="between")'),
                dict(
                    component='number',
                    name='maximum',
                    displayif='(values.moreless=="at most")||(values.moreless=="between")'),
                dict(
                    component='multiselect',
                    name='shift_type',
                    options=[
                        'weekday daytime',
                        'weekend daytime',
                        'weekend oncall',
                        'weekday oncall']),
                'locum shifts']

    def apply_constraint(self):
        kwargs = dict(**self.kwargs)
        enforced = self.get_constraint_atom()
        shift_types = ['_'.join(shifttype.upper().split())
                       for shifttype in kwargs.pop('shift_type', [])]
        if kwargs.pop('collectively') == 'individually':
            list_of_lists = [[Staff[s.upper()]]
                             for s in kwargs.pop('staff', [])]
        else:
            list_of_lists = [[Staff[s.upper()]
                              for s in kwargs.pop('staff', [])]]
        maximum = kwargs.pop('maximum', None)
        minimum = kwargs.pop('minimum', None)

        acceptable_shifts = {
            'WEEKDAY_DAYTIME': lambda d, day: (
                day % 7 <= FRIDAY
                and d == Shifts.DAYTIME
            ),
            'WEEKEND_DAYTIME': lambda d, day: (
                day % 7 > FRIDAY
                and d == Shifts.DAYTIME
            ),
            'WEEKDAY_ONCALL': lambda d, day: (
                day % 7 < FRIDAY
                and d == Shifts.ONCALL
            ),
            'WEEKEND_ONCALL': lambda d, day: (
                day % 7 >= FRIDAY
                and d == Shifts.ONCALL
            ),
            'ANY_OOH': lambda d, day: (
                (day % 7 > FRIDAY and d == Shifts.DAYTIME)
                or d == Shifts.ONCALL),
            'ANY': lambda d, day: True
        }
        if maximum is not None and minimum is not None and maximum < minimum:
            raise ValueError(
                'max locum sessions must be more or equal to minimum')

        for stafflist in list_of_lists:
            if maximum is not None:
                self.rota.model.Add(
                    sum(self.rota.get_duty(Duties.LOCUM_ICU, day, shift, staff)
                        for day in self.days()
                        for shift in Shifts
                        for staff in stafflist
                        if any(
                            acceptable_shifts[shifttype](shift, day) for shifttype in shift_types
                    )
                    ) <= maximum).OnlyEnforceIf(enforced)
            if minimum is not None:
                self.rota.model.Add(
                    sum(self.rota.get_duty(Duties.LOCUM_ICU, day, shift, staff)
                        for day in self.days()
                        for shift in Shifts
                        for staff in stafflist
                        if any(
                            acceptable_shifts[shifttype](shift, day) for shifttype in shift_types)
                        ) >= minimum).OnlyEnforceIf(enforced)


class EnforceRules(BaseConstraint):
    """Enforce all rules"""
    name = "Enforce Rules"

    @classmethod
    def definition(cls):
        return ['rules', {
            'component': 'select',
            'name': 'enforcement',
            'options': ['must', 'should']}, 'be enforced']

    def apply_constraint(self):
        if self.kwargs.get('enforcement') == 'must':
            for constraint in self.rota.constraint_atoms:
                self.rota.model.Add(constraint == 1)
        else:
            self.rota.model.Maximize(sum(self.rota.constraint_atoms))

    def event_stream(self, solver, event_stream):
        yield from event_stream
        for atom in self.rota.constraint_atoms:
            if solver.Value(atom) == 0:
                print(f'{atom.Name()} failed')
                yield {'type': 'statistic',
                       'constraint_fail': atom.Name()}


class BalanceTallies(BaseConstraint):
    """calculate targets"""
    name = "Balance tallies"
    targets = None

    @classmethod
    def definition(cls):
        return ['balance tallies (increases calculation time)']

    def apply_constraint(self):
        class Targets(Enum):
            '''labels for targets'''
            ICU_WEEKDAY = auto()
            ICU_WEEKEND = auto()
            ICU_WD_ONCALL = auto()
            ICU_WE_ONCALL = auto()

        targetkeys = {
            Targets.ICU_WEEKDAY: (Shifts.DAYTIME, lambda d: d % 7 <= THURSDAY),
            Targets.ICU_WEEKEND: (Shifts.DAYTIME, lambda d: d % 7 >= FRIDAY),
            Targets.ICU_WD_ONCALL: (Shifts.ONCALL, lambda d: d % 7 <= THURSDAY),
            Targets.ICU_WE_ONCALL: (Shifts.ONCALL, lambda d: d % 7 >= FRIDAY)}
        num_days = len(list(self.days()))
        tallies = {f"{key}{staff}": self.rota.model.NewIntVar(
            0, num_days, f'tally{key}') for key in targetkeys for staff in Staff}
        deltas = {f"{key}{staff}": self.rota.model.NewIntVar(
            0, num_days, f'delta{key}') for key in targetkeys for staff in Staff}
        targets = {}
        totals = {}
        for key, (shift, dayfilter) in targetkeys.items():
            totals[key] = len(
                [day for day in self.days() if dayfilter(day)])
            targets[key] = totals[key]//self.rota.slots_on_rota
            for staff in Staff:
                self.rota.model.AddAbsEquality(
                    tallies[f"{key}{staff}"],
                    sum(self.rota.get_duty(Duties.QUOTA_ICU, day, shift, staff)
                        for day in self.days()
                        if dayfilter(day)))
                self.rota.model.AddAbsEquality(
                    deltas[f"{key}{staff}"],
                    sum(self.rota.get_duty(Duties.QUOTA_ICU, day, shift, staff)
                        for day in self.days()
                        if dayfilter(day))-targets[key])

        self.rota.model.Minimize(sum(deltas.values()))
        self.targets = targets

    def event_stream(self, solver, event_stream):
        yield from event_stream
        yield(
            {'type': 'statistic',
             'objective': solver.BestObjectiveBound()})
        statskeys = {
            'ICU weekdays': (Duties.QUOTA_ICU, Shifts.DAYTIME, lambda d: d % 7 <= THURSDAY),
            'ICU weekend days': (Duties.QUOTA_ICU, Shifts.DAYTIME, lambda d: d % 7 >= FRIDAY),
            'ICU weekday oncall': (Duties.QUOTA_ICU, Shifts.ONCALL, lambda d: d % 7 <= THURSDAY),
            'ICU weekend oncall': (Duties.QUOTA_ICU, Shifts.ONCALL, lambda d: d % 7 >= FRIDAY),
            'Locum weekday oncall': (Duties.LOCUM_ICU, Shifts.ONCALL, lambda d: d % 7 <= THURSDAY),
            'Locum wkend days': (Duties.LOCUM_ICU, Shifts.DAYTIME, lambda d: d % 7 > FRIDAY),
            'Locum wkend oncall': (Duties.LOCUM_ICU, Shifts.ONCALL, lambda d: d % 7 >= FRIDAY)
        }
        for k, (duty, shift, dayfilter) in statskeys.items():
            for staff in Staff:
                yield({
                    'type': 'statistic',
                    'duty': k,

                    'staff': staff.name,
                    'tally': solver.Value(
                        sum(self.rota.get_duty(duty, day, shift, staff) for day in self.days()
                            if dayfilter(day)))})
""""""