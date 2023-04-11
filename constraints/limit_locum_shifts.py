"""contains rules to constrain the model"""
from calendar import FRIDAY
from collections import namedtuple


from config import Shifts, Staff
from constraints.utils import BaseConstraint
from constraints.some_shifts_are_locum import locum_icu

class Config():
    def get_config_interface(self):
        names = [s.name.title() for s in Staff]
        staff=self.get('staff')
        moreless=self.get('moreless')
        return [
            dict(component='multiselect', name='staff', options=names),
            'should',
            dict(
                component='select',
                name='collectively',
                options=['individually', 'collectively']) if len(staff)>1 else None,
            'do',
            dict(
                component='select',
                name='moreless',
                options=['at least', 'at most', 'between']),
            dict(
                component='number',
                name='minimum') if moreless in ['at least','between'] else None,
            'and' if moreless=='between' else None,
            dict(
                component='number',
                name='maximum') if moreless in ["at most","between"] else None,
            dict(
                component='multiselect',
                name='shift_type',
                options=[
                    'weekday daytime',
                    'weekend daytime',
                    'weekend oncall',
                    'weekday oncall']),
            'locum shifts']

class Constraint(BaseConstraint):
    """limit locum shifts for which filter is true"""
    name = "Limit Locum shifts"

    @classmethod
    def validate_config(cls, config):
        config=namedtuple(
            'Config',
            'staff collectively moreless maximum minimum shift_type'
            )(**config)
        return config

    

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
