"""contains rules to constrain the model"""
from calendar import MONDAY
from datetime import timedelta
from typing import TYPE_CHECKING


from constraints.core_duties import clinical, icu
from signals import signal

if TYPE_CHECKING:
    from solver import GenericConfig


@signal('apply_constraint').connect
def no_monday_after_weekend(ctx: 'GenericConfig'):
    for day in ctx.days:
        enforced = True
        if day.weekday() != MONDAY:
            continue
        monday = day
        saturday = day-timedelta(days=2)
        sunday = day-timedelta(days=1)
        if saturday not in ctx.days:
            continue

        for staff in ctx.staff:
            sat_shifts = [ctx.dutystore[clinical(
                shift, saturday, staff)] for shift in ctx.shifts]
            sun_shifts = [ctx.dutystore[clinical(
                shift, sunday, staff)] for shift in ctx.shifts]
            mon_shifts = [ctx.dutystore[clinical(
                shift, monday, staff)] for shift in ctx.shifts]
            wkend_shifts = sat_shifts+sun_shifts
            for mon in mon_shifts:
                for wkend in wkend_shifts:
                    ctx.model.AddBoolOr(
                        [mon.Not(), wkend.Not()]).OnlyEnforceIf(enforced)
