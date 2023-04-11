"Define core duties and that one person is on for ICU"

from dataclasses import dataclass, field
from datetime import date
import operator
from typing import TYPE_CHECKING
from calendar import MONDAY,TUESDAY,WEDNESDAY,THURSDAY,FRIDAY,SATURDAY,SUNDAY
from datatypes import DutyCell

from signals import signal

if TYPE_CHECKING:
    from solver import GenericConfig


Locations=('NONCLINICAL','ICU','THEATRE','LEAVE')


clinical_duty_types = ('THEATRE', 'ICU')


def allocated_for_duty(shift: str, day: date, staff: str, location: str):
    "is allocated for a given duty"
    return ('ALLOCATED_DUTY', shift, day, staff, location)


def icu(shift: str, day: date, staff: str):
    "An ICU daytime shift"
    return allocated_for_duty(shift, day, staff, 'ICU')


def theatre(shift: str, day: date, staff: str):
    "Theatre shift"
    return allocated_for_duty(shift, day, staff, 'THEATRE')


def leave(shift: str, day: date, staff):
    "is on leave"
    return allocated_for_duty(shift, day, staff, 'LEAVE')

def clinical(shift,day,staff):
    "is clinical"
    return ('CLINICAL',shift,day,staff)


@dataclass
class CoreDutiesContext:
    "Config class"
    clinical_duties: set[str] = field(default_factory=set)
    nonclinical_duties: set[str] = field(default_factory=set)
    days: set[date] = field(default_factory=set)

cover_requirements=[
    *((day,shift,icu,"==",1) for day in range(7) for shift in ('am','pm','oncall')),
    *((day,'oncall',theatre,"==",1) for day in range(7)),
    *((day,shift,theatre,"==",1) for day in (SATURDAY,SUNDAY) for shift in ('am','pm')),
    *((day,shift,theatre,">=",1) for day in range(5) for shift in ('am','pm'))
]

@signal('apply_constraint').connect
def required_coverage(ctx:'GenericConfig'):
    for day in ctx.days:
        for (weekday,shift,dutytype,op,requirement) in cover_requirements:
            if day.weekday()==weekday:
                oper={
                    "==":operator.eq,
                    ">=":operator.ge,
                    "<=":operator.le,
                    ">":operator.gt,
                    "<":operator.lt
                }[op]
                ctx.model.Add(oper(sum(ctx.dutystore[dutytype(shift, day, staff)]
                    for staff in ctx.staff),requirement))
@signal('apply_constraint').connect
def core_duties(ctx: 'GenericConfig'):
    "One person for ICU, no multitasking"
    for day in ctx.days:
        for shift in ctx.shifts:
            # one person must be on for ICU per shift
            
            # one person can only be doing one thing at a time
            for staff in ctx.staff:
                ctx.model.Add(
                    sum(ctx.dutystore[allocated_for_duty(shift, day, staff, duty_type)]
                    for duty_type in Locations)==1)
                clinical_duties=[ctx.dutystore[allocated_for_duty(
                        shift, day, staff, duty)] for duty in clinical_duty_types]
                is_clinical = ctx.dutystore[clinical(
                        shift, day, staff)]
                ctx.model.Add(sum(clinical_duties)+is_clinical.Not()==1)

@signal('build_output').connect
def build_output(ctx, outputdict, solver):
    "core duties output"
    print('core_duties builder')
    for key,value in ctx.dutystore.items():
        match key:
            case ('ALLOCATED_DUTY',shift,day,staff,location):
                if solver.Value(value):
                    cell=outputdict[(staff,day)]
                    assert isinstance(cell,DutyCell)
                    if location == 'NONCLINICAL':
                        cell.duties[shift].duty=None
                    else:
                        cell.duties[shift].duty=location
                    