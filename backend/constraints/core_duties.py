"Define core duties and that one person is on for ICU"

from dataclasses import dataclass, field
from datetime import date
import operator
from typing import TYPE_CHECKING
from calendar import MONDAY,TUESDAY,WEDNESDAY,THURSDAY,FRIDAY,SATURDAY,SUNDAY
from datatypes import DutyCell

from signals import signal
from constraint_ctx import ConstraintContext

if TYPE_CHECKING:
    from solver import GenericConfig


clinical_duty_types = ('THEATRE', 'ICU')
apply_constraint=signal('apply_constraint')
build_output=signal('build_output')
register_urls=signal('register_urls')

class CoreDuties:
    def __init__(self,ctx:ConstraintContext):
        self.ctx=ctx
        ctx.config['coreduties']=self
    @classmethod
    def from_context(cls,ctx:ConstraintContext):
        return ctx.config.setdefault('coreduties',cls(ctx))
    def allocated_for_duty(self,shift: str, day: date, staff: str, location: str):
        "is allocated for a given duty"
        if location not in locations and location not in groups:
            raise KeyError(f'{location} not recognised')
        return self.ctx.dutystore[('ALLOCATED_DUTY', shift, day, staff, location)]
    locations=('NC','ICU','THEATRE','LEAVE')
    groups={
        'CLINICAL':('THEATRE','ICU'),
        'NONCLINICAL':('LEAVE','NC'),
        'JOBPLANNED':('CLINICAL','LEAVE'),
        'NOTJOBPLANNED':('TS','NC','LEAVE')
    }
    cover_requirements=[
        *((day,shift,'ICU',"==",1) for day in range(7) for shift in ('am','pm','oncall')),
        *((day,'oncall','THEATRE',"==",1) for day in range(7)),
        *((day,shift,'THEATRE',"==",1) for day in (SATURDAY,SUNDAY) for shift in ('am','pm')),
        *((day,shift,'THEATRE',">=",1) for day in range(5) for shift in ('am','pm'))
    ]
    

@dataclass
class CoreDutiesContext:
    "Config class"
    clinical_duties: set[str] = field(default_factory=set)
    nonclinical_duties: set[str] = field(default_factory=set)
    days: set[date] = field(default_factory=set)


@apply_constraint.connect
def required_coverage(ctx:ConstraintContext):
    cdctx=CoreDuties.from_context(ctx)
    for day in ctx.days:
        for (weekday,shift,dutytype,op,requirement) in cdctx.cover_requirements:
            if day.weekday()==weekday:
                oper={
                    "==":operator.eq,
                    ">=":operator.ge,
                    "<=":operator.le,
                    ">":operator.gt,
                    "<":operator.lt
                }[op]
                ctx.model.Add(oper(sum(cdctx.dutystore[allocated_for_duty(shift, day, staff,dutytype)]
                    for staff in ctx.staff),requirement))
                
@apply_constraint.connect
def core_duties(ctx: ConstraintContext):
    "No multitasking"
    cdctx=CoreDuties.from_context(ctx)
    for day in ctx.core_config.days:
        for shift in ctx.core_config.shifts:
            # one person can only be doing one thing at a time
            for staff in ctx.core_config.staff:
                ctx.model.Add(
                    sum(cdctx.allocated_for_duty(shift, day, staff, duty_type)
                    for duty_type in cdctx.locations)==1)
                for group_name,grp in cdctx.groups.items():
                    in_group=set(grp)
                    not_in_group=set(locations)-set(grp)
                    for loc in in_group:
                        ctx.model.Add(sum(ctx.allocated_for_duty(shift,day,staff,loc) for loc in grp)>=1).OnlyEnforceIf(ctx.allocated_for_duty(shift,day,staff,group_name)==1)
                        ctx.model.Add(sum(ctx.allocated_for_duty(shift,day,staff,loc) for loc in grp)==0).OnlyEnforceIf(ctx.allocated_for_duty(shift,day,staff,group_name)==0)

    @ctx.signals.result.connect
    def builder(ctx, staff,day,shift,sessionduty, solver):
        "core duties output"
        for loc in cdctx.locations:
            if solver.Value(cdctx.allocated_for_duty(shift,day,staff,loc)):
                sessionduty.duty=loc
