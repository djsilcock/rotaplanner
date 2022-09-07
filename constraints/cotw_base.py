"""contains rules to constrain the model"""
from constraints.core_duties import icu as get_icu
from constraints.constraintmanager import BaseConstraint

from constants import Staff


def expandlist(dayshiftlist):
    "expand list of duties"
    for days,shifts in dayshiftlist:
        for d in (days if isinstance(days,(tuple,list)) else (days,)):
            for s in (shifts if isinstance(shifts, (tuple, list)) else (shifts,)):
                yield (d,s)


class COTWConstraint(BaseConstraint):
    """Base COTW constraint"""
    name = 'Consultant of the week'
    dutylist=[]
    cotw_key=None
    def apply_constraint(self):     
        for day in self.days():
            enforced = self.get_constraint_atom(day=day)
            for staff in Staff:
                cotw = self.rota.get_or_create_duty_base(
                    (self.cotw_key,day//7,staff)
                    )
                for weekday,shift in expandlist(self.dutylist):
                    if day%7==weekday:                        
                        self.model.Add(
                            self.get_duty(get_icu(shift,day,staff)) == cotw
                            ).OnlyEnforceIf(enforced)               
            self.rota.model.Add(enforced == 1)

