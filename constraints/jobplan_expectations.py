"""contains rules to constrain the model"""
from collections import namedtuple
import datetime
import inspect

from sanic_wtf import SanicForm
from wtforms import (
    Field,SelectField,SelectMultipleField,IntegerField,FieldList,
    FormField,DateField)
from wtforms.widgets import TextInput
from wtforms.validators import (StopValidation,InputRequired,ValidationError)

from config import Shifts, Staff
from constraints.utils import BaseConstraint
from constraints.core_duties import leave, nonclinical, theatre, icu
from database import get_names_from_db

def icu_timeshift(shift, day, staff):
    "ICU duty as a timeshifted session"
    return ('ICU_TS', shift, day, staff)

def icu_jobplanned(shift, day, staff):
    "ICU duty in jobplanned time"
    return ('ICU_JP', shift, day, staff)

def time_back(shift, day, staff):
    "Time back from timeshifted sessions"
    return ('TIMEBACK', shift, day, staff)

def jobplanned_nonclinical(shift, day, staff):
    "Jobplanned nonclinical session"
    return('JP_NONCLINICAL', shift, day, staff)

def jobplanned_dcc(shift, day, staff):
    "Jobplanned DCC"
    return ('JP_DCC', shift, day, staff)

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
            if valuelist:
                self.data = [int(x.strip()) for x in valuelist[0].split(',')]
            else:
                self.data = []
        except ValueError as exc:
            raise ValueError('All elements must be numeric') from exc

class IgnoreIfBase():
    def __init__(self,other_field,value):
        self.other_field=other_field
        self.value=value if hasattr(value,'__iter__') else [value]
    def test(self,other_value):
        raise NotImplementedError
    def __call__(self,form,field):
        other_field=form.data[self.other_field]
        if self.test(other_field):
            field.errors.clear()
            raise StopValidation()

class IgnoreIf():
    def __init__(self,fn):
        self.fn=fn
    def __call__(self,form,field):
        if self.fn(form):
            field.errors.clear()
            raise StopValidation

class IgnoreUnless():
    def __init__(self,fn):
        self.fn=fn
    def __call__(self,form,field):
        if not self.fn(form):
            field.errors.clear()
            raise StopValidation


class JobPlanForm(SanicForm):
    "form for job plan entry"
    staff=SelectField(
        label='staff member',
        validators=[InputRequired()],
        )
    sessions=SelectMultipleField(label="sessions",choices=[
        f'{day}-{sess}' for day in 'mon tue wed thu fri sat sun'.split() for sess in 'am pm oncall'.split()
    ])
    rule_type=SelectField(
        label='Availability category',
        choices=[
            ('dcc','Timetabled DCC'),
            ('flex','Available for contracted duties'),
            ('locum','Available for locum duties'),
            ('timeshift','Available via timeshift')],

        validators=[InputRequired()])

    acceptable=SelectMultipleField(
        label='acceptable duties',
        choices=[
            ('theatre','theatre'),
            ('icu','ICU')
            ],
        validators=(InputRequired()))

    rotation_type=SelectField(
        label='rotation type',
        choices=[
            ('ev','every week'),
            ('xiny','weeks x,y... in z'),
            ('xinmonth','weeks x,y... of month'),
        ],
        validators=[InputRequired()])

    weeks=NumberListField(
        'weeks',
        render_kw={'pattern':r'^(\d+,)*\d+$'},
        validators=[
            IgnoreUnless(lambda form: form.rotation_type.data in ('xiny','xinmonth')),
            InputRequired()])
    def validate_weeks(self,field):
        "check x<=y for all x/y pairs"
        for week_no in field.data:
            if week_no>self.cycle.data:
                raise ValidationError('all values must be less than number of weeks in cycle')

    flex_expectation=IntegerField('expected shifts',
        validators=[
            IgnoreUnless(lambda form:form.rule_type.data=='flex'),
            InputRequired()
        ])

    locum_min=IntegerField('Minimum extras',
        validators=[
            IgnoreUnless(lambda form:form.rule_type.data=='locum'),
            InputRequired()
        ])
    locum_max=IntegerField('Minimum extras',
        validators=[
            IgnoreUnless(lambda form:form.rule_type.data=='locum'),
            InputRequired()
        ])
    def validate_locum_max(self,field):
        "validator"
        if field.data<self.locum_min.data:
            raise ValidationError('Maximum cannot be less than minimum')

    cycle=IntegerField('cycle length',
        validators=[
            IgnoreIf (lambda form: form.rule_type.data=='dcc' and form.rotation_type.data in ('ev','xinmonth')),
            InputRequired()
        ]
    )
    startdate=DateField(label='Effective from')
    enddate=DateField(label='Effective until')


class Constraint(BaseConstraint):
    """Apply jobplan to staffmember"""
    name = "Apply jobplans"
    staff=None
    jobplan_entries=None
    def configure(self, config):
        self.staff=config['staff']
        self.jobplan_type=config['rule_type']
        self.jobplan_sessions=config['sessions']
        self.acceptable_duties=config['acceptable']
        self.rotation_type=config['rotation_type']
        self.weeks=config['weeks']
        self.flex_expectation=config['flex_expectation']
        self.locum_min=config['locum_min']
        self.locum_max=config['locum_max']
        self.cycle=config['cycle']
        self.startdate=config['startdate']
        self.enddate=config['enddate']
        return super().configure(config)

    def serialize(self):
        return {
            'staff':self.staff,
            'jobplan_entries':self.jobplan_entries,
            **super().serialize()
            }

    def setup_constraint(self,context):
        """apply jobplans"""
        assert self.staff is not None
        assert self.jobplan_entries is not None
        jp_dcc_store=context.setdefault('jobplanned_dcc',{})
        def is_x_of_y(startdate:datetime.date,numerator,denominator,testdate:datetime.date):
            if startdate>testdate:
                return False
            week_num=((testdate-startdate).days//7) #will be zero-indexed
            if isinstance(numerator,int):
                return (week_num%denominator)+1 == numerator
            elif isinstance(numerator,tuple):
                return (week_num%denominator)+1 in numerator
        def is_x_of_month(numerator,testdate:datetime.date):
            week_num=testdate.day//7
            if isinstance(numerator,int):
                return numerator==week_num+1
            elif isinstance(numerator,tuple):
                return (week_num+1) in numerator  

        for day in self.days():
            for shift in ('am','pm','oncall'):
                jp_dcc_store.setdefault((day,shift),False)

                shift_id=f"{'mon tue wed thu fri sat sun'.split()[day.weekday]}-{shift}"
                if shift_id not in self.jobplan['sessions']:
                    continue
                if entry['rotation_type']=='xiny':
                    if not is_x_of_y(entry['startdate'],entry['weeks'],entry['cycle'],day):
                        continue
                elif entry['rotation_type']=='xinmonth':
                    if not is_x_of_month(entry['weeks'],day):
                        continue
                jobplanned_dcc[(day,shift)]=True

                is_jobplanned = self.get_or_create_duty(
                    jobplanned_dcc(shift, day, self.staff))
                is_icu_timeshift = self.get_or_create_duty(
                    icu_timeshift(shift, day, self.staff))
                is_icu_jobplanned = self.get_or_create_duty(
                    icu_jobplanned(shift, day, self.staff))
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
                self.model.AddAllowedAssignments(
                    [is_on_leave,is_jobplanned,is_icu,is_theatre,is_icu_timeshift],
                    [(True,True,False,False,False),
                    (True,False,False,False,False),
                    (False,True,True,False,False),
                    (False,True,False,True,False),
                    (False,False,False,False,False),
                    (False,False,True,False,True)]
                )
                
                

        self.rota.model.Add(
            sum(self.get_duty(icu_timeshift(shift, day, staff))
                for day in self.days() for shift in (Shifts.AM, Shifts.PM)) >=
            sum(self.get_duty(time_back(shift, day, staff))
                for day in self.days() for shift in (Shifts.AM, Shifts.PM)))
