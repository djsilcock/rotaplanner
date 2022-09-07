"""contains rules to constrain the model"""

from calendar import FRIDAY,SATURDAY,SUNDAY

from constants import Shifts
from constraints.cotw_base import COTWConstraint

class Constraint(COTWConstraint):
    """Daytime consultant should be COTW"""
    name = 'Consultant of the week'
    dutylist=[
        ((FRIDAY,SATURDAY),(Shifts.AM,Shifts.PM)),
        (SUNDAY,(Shifts.AM,Shifts.PM,Shifts.ONCALL))
    ]
    cotw_key='COTWED'

    @classmethod
    def definition(cls):
        yield 'consultant of the week should do Fri-Sun and Sun oncall'

    

