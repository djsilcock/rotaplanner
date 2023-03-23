"""contains rules to constrain the model"""
from calendar import WEDNESDAY

from constraints.enforce_max_x_in_y_base import enforce_max_x_in_y
from signals import signal

@signal('apply_constraint').connect
def max_weeks_per_period(ctx):
    """maximum number of daytime ICU weeks in any given period"""

    def filterfunc(shift, day, _):
        return (shift=='am') and (day.weekday()==WEDNESDAY)
    
    return enforce_max_x_in_y(ctx,filterfunc,{'numerator':2,'denominator':5})
    