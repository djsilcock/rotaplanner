"Define core duties and that one person is on for ICU"

from dataclasses import dataclass, field
from datetime import date
from typing import TYPE_CHECKING
from datatypes import DutyCell

from signals import signal

if TYPE_CHECKING:
    from solver import GenericConfig


Locations=('NONCLINICAL','ICU','THEATRE','LEAVE')


clinical_duties = ('THEATRE', 'ICU')


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
    return allocated_for_duty(shift,day,staff,'CLINICAL')


@dataclass
class CoreDutiesContext:
    "Config class"
    clinical_duties: set[str] = field(default_factory=set)
    nonclinical_duties: set[str] = field(default_factory=set)
    days: set[date] = field(default_factory=set)


@signal('apply_constraint').connect
def core_duties(ctx: 'GenericConfig'):
    "One person for ICU, no multitasking"
    print ('core duties constraint')
    for day in ctx.days:
        for shift in ctx.shifts:
            # one person must be on for ICU per shift
            ctx.model.Add(sum(ctx.dutystore[icu(shift, day, staff)]
                    for staff in ctx.staff)==1)
            # one person can only be doing one thing at a time
            for staff in ctx.staff:
                ctx.model.AddBoolXOr(
                    *[ctx.dutystore[allocated_for_duty(shift, day, staff, duty_type)]
                    for duty_type in Locations])
                for duty in Locations:
                    this_duty = ctx.dutystore[allocated_for_duty(
                        shift, day, staff, duty)]
                    is_clinical = ctx.dutystore[clinical(
                        shift, day, staff)]
                    if duty in clinical_duties:
                        ctx.model.AddImplication(
                            this_duty, is_clinical)
                    else:
                        ctx.model.AddImplication(
                            this_duty, is_clinical.Not())

@signal('build_output').connect
def build_output(ctx, outputdict, solver):
    "core duties output"
    print('core_duties builder')
    for key,value in ctx.dutystore.items():
        match key:
            case ('ALLOCATED_DUTY',shift,day,staff,"THEATRE"|"ICU" as location):
                if solver.Value(value):
                    cell=outputdict[(staff,day)]
                    assert isinstance(cell,DutyCell)
                    cell.duties[shift].duty=location
                    