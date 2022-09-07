"""contains rules to constrain the model"""
from calendar import FRIDAY


from constants import Shifts, Staff
from constraints.constraintmanager import BaseConstraint
from constraints.some_shifts_are_locum import locum_icu


class Constraint(BaseConstraint):
    """limit locum shifts for which filter is true"""
    name = "Limit Locum shifts"

    @classmethod
    def definition(cls):
        names = [s.name.title() for s in Staff]
        return [ dict(component='multiselect', name='staff', options=names),
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
        if kwargs.pop('collectively',None) == 'individually':
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
                and d in [Shifts.AM,Shifts.PM]
            ),
            'WEEKEND_DAYTIME': lambda d, day: (
                day % 7 > FRIDAY
                and d in [Shifts.AM,Shifts.PM]
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
                (day % 7 > FRIDAY and d in [Shifts.AM,Shifts.PM])
                or d == Shifts.ONCALL),
            'ANY': lambda d, day: True
        }
        if maximum is not None and minimum is not None and maximum < minimum:
            raise ValueError(
                'max locum sessions must be more or equal to minimum')

        for stafflist in list_of_lists:
            if maximum is not None:
                self.rota.model.Add(
                    sum(self.get_duty(locum_icu(shift,day,staff))
                        for day in self.days()
                        for shift in Shifts
                        for staff in stafflist
                        if any(
                            acceptable_shifts[shifttype](shift, day) for shifttype in shift_types
                    )
                    ) <= maximum).OnlyEnforceIf(enforced)
            if minimum is not None:
                self.rota.model.Add(
                    sum(self.get_duty(locum_icu(shift,day,staff))
                        for day in self.days()
                        for shift in Shifts
                        for staff in stafflist
                        if any(
                            acceptable_shifts[shifttype](shift, day) for shifttype in shift_types)
                        ) >= minimum).OnlyEnforceIf(enforced)
