"""contains rules to constrain the model"""
from typing import TYPE_CHECKING
from calendar import MONDAY, TUESDAY, WEDNESDAY, THURSDAY,FRIDAY,SATURDAY,SUNDAY

from constraints.core_duties import icu as get_icu

from signals import signal

if TYPE_CHECKING:
    from solver import GenericConfig

def expandlist(dayshiftlist):
    "expand list of duties"
    for days,shifts in dayshiftlist:
        for day in (days if isinstance(days,(tuple,list)) else (days,)):
            for shift in (shifts if isinstance(shifts, (tuple, list)) else (shifts,)):
                yield (day,shift)

def apply_cotw(ctx,cotw_key,dutylist):
    assert ctx.days is not None
    for day in ctx.days:
        enforced = True
        for staff in ctx.staff:
            cotw = ctx.dutystore[
                (cotw_key,day.isocalendar().year,day.isocalendar().week,staff)]
            for weekday,shift in expandlist(dutylist):
                if day.weekday()==weekday:
                    rule=ctx.model.Add(
                        ctx.dutystore[get_icu(shift,day,staff)] == cotw
                        )
                    assert rule is not None
                    rule.OnlyEnforceIf(enforced)
        ctx.model.Add(enforced == 1)

@signal('apply_constraint').connect
def monday_to_thursday_icu(ctx):
    """Daytime consultant should be COTW"""
    dutylist=[
        ((MONDAY,TUESDAY,WEDNESDAY),('am','pm')),
        (THURSDAY,('am','pm','oncall'))]
    cotw_key='COTW'
    return apply_cotw(ctx,cotw_key,dutylist)

@signal('apply_constraint').connect
def friday_saturday_night(ctx):
    """Daytime consultant should be COTW"""
    dutylist=[((FRIDAY,SATURDAY),'oncall')]
    cotw_key='COTWEN'
    return apply_cotw(ctx,cotw_key,dutylist)

@signal('apply_constraint').connect
def weekend_days(ctx):
    """Daytime consultant should be COTW"""
    dutylist=[
        ((FRIDAY,SATURDAY),('am','pm')),
        (SUNDAY,('am','pm','oncall'))
    ]
    cotw_key='COTWED'
    return apply_cotw(ctx,cotw_key,dutylist)
