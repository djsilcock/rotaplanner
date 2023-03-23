"""contains rules to constrain the model"""
from calendar import SATURDAY


from constraints.enforce_max_x_in_y_base import enforce_max_x_in_y
from signals import signal

@signal('apply_constraint').connect
def max_oncalls_per_period(ctx):
    """Maximum number of oncalls per given number of days"""
    def filterfunc(shift, day, staff):
        return any([
            (shift=='oncall'),
            ((shift=='am') and (day.weekday()==SATURDAY))
            ])
    return enforce_max_x_in_y(ctx,filterfunc,{'numerator':3,'denominator':7})
