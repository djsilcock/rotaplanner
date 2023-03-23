"""contains rules to constrain the model"""
from calendar import MONDAY, TUESDAY, WEDNESDAY
from datetime import timedelta




from constraints.core_duties import icu
from signals import signal

@signal('apply_constraint').connect
def no_multiple_weekday_oncalls(ctx):
        """no more than 1 weekday oncall"""
        weekdays = [MONDAY, TUESDAY, WEDNESDAY]
        days_to_check = list(ctx.days)
        for day in days_to_check:
            enforced = 1 #self.get_constraint_atom(day=day)
            start_of_week = day-timedelta(days=day.weekday())
            for staff in ctx.staff:
                sum_of_duties = sum(
                    ctx.dutystore[icu('oncall',start_of_week+timedelta(days=dd),staff)]
                        for dd in [0, 1, 2]
                        if start_of_week+timedelta(days=dd) in days_to_check)
                ctx.model.Add(sum_of_duties < 2).OnlyEnforceIf(enforced)
