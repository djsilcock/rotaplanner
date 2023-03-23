"""contains rules to constrain the model"""
from calendar import SATURDAY
from datetime import timedelta

from constraints.core_duties import icu


def enforce_max_x_in_y(ctx,filterfunc,config):
        enforced = 1 #self.get_constraint_atom()
        for day in ctx.days[config['denominator']:]:
            enforced = 1 #self.get_constraint_atom(day=day)
            for staff in ctx.staff:
                ctx.model.Add(
                    sum(ctx.dutystore[icu('oncall',dd,staff)]
                        for dd in (day-timedelta(days=d) for d in range(config['denominator']))
                        for shift in ctx.shifts
                        if filterfunc(shift,dd,staff)) <= config['numerator']
                ).OnlyEnforceIf(enforced)
