"""contains rules to constrain the model"""
from collections import deque, namedtuple
from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum, StrEnum
from typing import TYPE_CHECKING, Any, Literal, NamedTuple,Self
from calendar import MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY
from backend.constraint_ctx import DutyStore
from constraint_ctx import ConstraintContext,BaseConstraintConfig
from constraints import acceptable_duties
from constraints.core_duties import CoreDuties
from config.jobplans import jobplans,trainee_default

from signals import signal


def expand(template, head=None):
    if head is None:
        head = []
    tmp = deque(template)
    while tmp:
        a, b, c = tmp.popleft()
        if isinstance(a, tuple):
            for x in a:
                yield from expand([(x, b, c), *tmp], head[:])
            return
        else:
            head.append((a, b, c))
    yield head


AnchorType=Literal['MONTH']|Literal['WEEK']

class TemplateEntry:
    week:int
    day:int
    acceptable_duties:set

class BoundTemplateEntry(NamedTuple):
    date:date
    session:str
    duty:str


class BoundTemplate(NamedTuple):
    staff_member:str
    template_entries:tuple[BoundTemplateEntry,...]


class Template:
    template_id:Any
    anchor_date:date
    start_date:date
    end_date:date
    anchor_type:AnchorType
    repeat_period:int
    staff_members:set
    template_entries:list[TemplateEntry]
    def __init__(self,anchor_date:date,anchor_type:AnchorType,template_entries:list[TemplateEntry|dict],repeat_period:int|None=None):
        self._bindings={}
    def bind(self,day,staff) ->BoundTemplate|None:
        if day in self._bindings:
            return self._bindings[day,staff]
        if day<self.start_date:
            return None
        if day>self.end_date:
            return None
        if day==self.anchor_date:
            if self.anchor_type=='MONTH':
                nth_of_month=self.anchor_date.day//7
                day_of_

                MTWTFSSMTW    MTWTFSSMTW
                123456789A    3456789ABC
        



def template_var(ctx, template, day, staff):
    return ctx.dutystore[('TEMPLATE', repr(template), day.isocalendar().year, day.isocalendar().week, staff)]


class TemplateConstraint(BaseConstraintConfig):
    dutystore:DutyStore[BoundTemplate]
    def apply_constraint(self):
        core_duties=CoreDuties.from_context(self.ctx)
        core=self.ctx.core_config
        bound_templates:dict[tuple[str,date,str],set]={}
        templates:list[Template]=[]
        for day in core.days:
            for template in templates:
                for staff in template.staff_members:
                    if (bound:=template.bind(day,staff)):
                        for entry in bound.template_entries:
                            bound_templates.setdefault((staff,entry.date,entry.session),set()).add(bound)
        for day in core.days:
            for staff in core.staff:
                for shift in core.shifts:
                    if (staff,day,shift) in bound_templates:
                    




        enforced = True
        for staff in core.staff:
            for shift in core.shifts:
                valid_templates = []
                jp = jobplans.get(staff, trainee_default)
                for template_or_templates in jp:
                    for template in expand(template_or_templates):
                        for template_entry in template:
                            duty, weekday, dutyshift = template_entry
                            weekoffset = weekday//7
                            weekday = weekday-7*weekoffset
                            cotw = template_var(
                                ctx, template, day-timedelta(days=weekoffset*-7), staff)
                            if day.weekday() == weekday and shift == dutyshift:
                                if template not in valid_templates:
                                    valid_templates.append(template)
                                rule = ctx.model.Add(getattr(Getters, duty)(
                                    ctx, shift, day, staff) == 1)
                                rule.OnlyEnforceIf(cotw)
                assert len(valid_templates) > 0
                ctx.model.Add(sum(template_var(ctx, cotw_key, day, staff)
                              for cotw_key in valid_templates) >= 1)
