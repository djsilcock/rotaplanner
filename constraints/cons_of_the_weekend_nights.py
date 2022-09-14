"""contains rules to constrain the model"""

from calendar import FRIDAY,SATURDAY

from constants import Shifts
from constraints.cotw_base import COTWConstraint

class Constraint(COTWConstraint):
    """Daytime consultant should be COTW"""
    name = 'Consultant of the week'
    dutylist=[((FRIDAY,SATURDAY),Shifts.ONCALL)]
    cotw_key='COTWEN'

    @classmethod
    def get_config_interface(cls,config):
        yield 'consultant of the weekend nights  should do Fri and Sat oncall'

    

