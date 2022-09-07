"""contains rules to constrain the model"""

from calendar import MONDAY, TUESDAY, WEDNESDAY, THURSDAY

from constants import Shifts
from constraints.cotw_base import COTWConstraint

class Constraint(COTWConstraint):
    """Daytime consultant should be COTW"""
    name = 'Consultant of the week'
    dutylist=[
        ((MONDAY,TUESDAY,WEDNESDAY),(Shifts.AM,Shifts.PM)),
        THURSDAY,(Shifts.AM,Shifts.PM,Shifts.ONCALL)]
    cotw_key='COTW'

    @classmethod
    def definition(cls):
        yield 'consultant of the week should do Mon-Thu and Thu oncall'

    

