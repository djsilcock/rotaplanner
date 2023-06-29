
from sanic_wtf import SanicForm
from wtforms import (Field, SelectField,
                     SelectMultipleField, IntegerField, DateField)
from wtforms.widgets import TextInput
from wtforms.validators import (StopValidation, InputRequired, ValidationError)
from .enums import DutyBasis,RotationType
from typing import Callable, TYPE_CHECKING

from constraints.core_duties import Clinical

if TYPE_CHECKING:
    from solver import GenericConfig

class NumberListField(Field):
    "custom wtf field"
    widget = TextInput()

    def _value(self):
        if self.data:
            return ', '.join(str(d) for d in self.data)
        else:
            return ''

    def process_formdata(self, valuelist):
        try:
            # pylint: disable=attribute-defined-outside-init
            if valuelist:
                self.data = [int(x.strip()) for x in valuelist[0].split(',')]
            else:
                self.data = []
        except ValueError as exc:
            raise ValueError('All elements must be numeric') from exc



class JobPlanForm(SanicForm):
    "form for job plan entry"
    staff = SelectField(
        label='staff member',
        validators=[InputRequired()],
    )
    sessions = SelectMultipleField(label="sessions", choices=[
        f'{day}-{sess}' for day in 'mon tue wed thu fri sat sun'.split()
        for sess in 'am pm oncall'.split()
    ])
    availability_basis = SelectField(
        label='Availability category',
        choices=[
            (DutyBasis.DCC, 'Timetabled DCC'),
            (DutyBasis.FLEX, 'Contracted flexible availability'),
            (DutyBasis.LOCUM, 'Locum availability'),
            (DutyBasis.TIMESHIFT, 'Available via timeshift/dutychange')],

        validators=[InputRequired()])

    acceptable = SelectMultipleField(
        label='acceptable duties',
        choices=[
            (Clinical.THEATRE, 'theatre'),
            (Clinical.ICU, 'ICU')
        ],
        validators=(InputRequired()))

    rotation_type = SelectField(
        label='rotation type',
        choices=[
            (RotationType.EV, 'every week'),
            (RotationType.XINY, 'weeks x,y... in z'),
            (RotationType.XINMONTH, 'weeks x,y... of month'),
        ],
        validators=[InputRequired()])

    weeks = NumberListField(
        'weeks',
        render_kw={'pattern': r'^(\d+,)*\d+$'},
        validators=[
            InputRequired()])

    def validate_weeks(self, field):
        "check x<=y for all x/y pairs"
        for week_no in field.data:
            if week_no > self.cycle.data:
                raise ValidationError(
                    'all values must be less than number of weeks in cycle')

    cycle = IntegerField('cycle length',
                         validators=[InputRequired()
                         ]
                         )
    startdate = DateField(label='Effective from')
    enddate = DateField(label='Effective until')

    def validate(self, extra_validators=None):
        match self.rotation_type.data:
            case RotationType.EV:
                del self._fields['cycle']
                del self._fields['weeks']
            case RotationType.XINMONTH:
                del self._fields['cycle']
            case RotationType.XINY:
                pass
            case _:
                raise ValueError
        return super().validate(extra_validators)
