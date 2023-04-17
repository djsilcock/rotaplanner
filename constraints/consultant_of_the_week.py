"""contains rules to constrain the model"""
from collections import deque
from datetime import timedelta
from typing import TYPE_CHECKING
from calendar import MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY

from constraints.core_duties import clinical, icu, leave, theatre, nonclinical
from config.jobplans import jobplans

from signals import signal

if TYPE_CHECKING:
    from solver import GenericConfig


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


class Getters:
    @staticmethod
    def icu(ctx, shift, day, staff):
        return ctx.dutystore[icu(shift, day, staff)]
    @staticmethod
    def theatre(ctx, shift, day, staff):
        return ctx.dutystore[theatre(shift, day, staff)]
    @staticmethod
    def get_clinical(ctx: 'GenericConfig', shift, day, staff):
        return ctx.dutystore[clinical(shift, day, staff)]
    @staticmethod
    def nonclinical(ctx: 'GenericConfig', shift, day, staff):
        return ctx.dutystore[nonclinical(shift, day, staff)]
    @staticmethod
    def timeback(ctx: 'GenericConfig', shift, day, staff):
        return ctx.dutystore[leave(shift, day, staff)]





def template_var(ctx, template, day, staff):
    return ctx.dutystore[('TEMPLATE', repr(template), day.isocalendar().year, day.isocalendar().week, staff)]


@signal('apply_constraint').connect
def apply_templates(ctx: 'GenericConfig'):
    assert ctx.days is not None
    for day in ctx.days:
        enforced = True
        for staff in ctx.staff:
            for shift in ctx.shifts:
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
