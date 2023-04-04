"""contains rules to constrain the model"""
from calendar import SATURDAY


from constraints.enforce_max_x_in_y_base import enforce_max_x_in_y
from signals import signal

@signal('apply_constraint').connect
def max_weekends_per_period(ctx):
    """Maximum x weekends (day or night) in any y weekends"""

    def filterfunc(shift, day, staff):
        return (shift in ('am','oncall')) and (day.weekday()==SATURDAY)
    
    return enforce_max_x_in_y(ctx,filterfunc,{'numerator':2,'denominator':35})
    