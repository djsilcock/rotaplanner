"""contains rules to constrain the model"""

from constraints.core_duties import icu,clinical
from datetime import timedelta
from signals import signal

@signal('apply_constraint').connect
def no_night_before_clinical_day(ctx):
    """no night before clinical day (except Sunday and Thursday)"""
    
    for day in ctx.days:
        #enforced = self.get_constraint_atom(day=day)
        for staff in ctx.staff:
            ctx.model.Add(
                ctx.dutystore[clinical('am',day+timedelta(days=1),staff)]==0
            ).OnlyEnforceIf(
                ctx.dutystore[(icu('oncall', day, staff))])
            ctx.model.Add(
                ctx.dutystore[clinical('pm',day+timedelta(days=1),staff)]==0
            ).OnlyEnforceIf(
                ctx.dutystore[(icu('oncall', day, staff))])
