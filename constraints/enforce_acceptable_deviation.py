"""contains rules to constrain the model"""
from calendar import MONDAY,TUESDAY,WEDNESDAY,THURSDAY,FRIDAY, SATURDAY, SUNDAY

import dataclasses
from typing import TYPE_CHECKING, Optional
from datetime import date

from ortools.sat.python import cp_model

from constraints.some_shifts_are_locum import quota_icu
from signals import signal

if TYPE_CHECKING:
    from solver import GenericConfig

shift_types = [('weoc', 'Weekend oncall'),
               ('wedt', 'Weekend daytime'),
               ('wdoc', 'Weekday oncall'),
               ('wddt', 'Weekday daytime'),
               ('anywe', 'Any weekend')]


@dataclasses.dataclass
class AcceptableDeviationEntry:
    staff:Optional[set[str]]
    deviation:int
    share:int
    shift_defs:set[tuple[int,str]]
    startdate:Optional[date]=None
    enddate:Optional[date]=None


@dataclasses.dataclass
class AcceptableDeviationContext:
    entries:list[AcceptableDeviationEntry]

weekend_days={(SATURDAY,'am'),(SATURDAY,'pm'),(SUNDAY,'am'),(SUNDAY,'pm')}
weekend_nights={(FRIDAY,'oncall'),(SATURDAY,'oncall'),(SUNDAY,'oncall')}
weekday_nights={(MONDAY,'oncall'),(TUESDAY,'oncall'),(WEDNESDAY,'oncall'),(THURSDAY,'oncall')}

entries=[
    AcceptableDeviationEntry(None,30,7,weekend_days),
    AcceptableDeviationEntry(None,30,7,weekend_nights),
    AcceptableDeviationEntry(None,30,7,weekday_nights)
]

@signal('apply_constraint').connect
def enforce_quotas(ctx):
    for entry_id,entry in enumerate(entries):
        deviation_hard_limit = entry.deviation
        #enforced = self.get_constraint_atom()
        deviation_soft_limits = []
        period_duration = 9*7
        for end_day in ctx.days[period_duration:None:period_duration]+[ctx.days[-1]]:
            deviation_soft_limit = ctx.model.NewIntVar(
                0,
                deviation_hard_limit,
                f'soft-limit{entry_id}{end_day}')
            deviation_soft_limits.append(deviation_soft_limit)
            for staff in (entry.staff or ctx.staff):
                duties = [
                    ctx.dutystore[quota_icu(shift_id, dd, staff)]
                    for dd in ctx.days
                    for (weekday,shift_id) in entry.shift_defs
                    if dd <= end_day and dd.weekday()==weekday]
                #target = ctx.model.NewConstant(len(duties)//entry.share)
                target = len(duties)//entry.share

                delta_abs = ctx.model.NewIntVar(-deviation_hard_limit,
                                                    deviation_hard_limit,
                                                    f'delta{end_day}{entry.shift_defs}{staff}')
                ctx.model.AddAbsEquality(delta_abs,  cp_model.LinearExpr.Sum(duties)-target)
                ctx.model.Add(delta_abs <= deviation_soft_limit)
        ctx.minimize_targets.extend(deviation_soft_limits)

