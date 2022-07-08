"""contains rules to constrain the model"""


from datetime import timedelta
from enum import Enum
from constants import Shifts, Staff, Duties
from constraints.constraintmanager import BaseConstraint


ConfirmedDuties=Enum('ConfirmedDuties','DEFINITE_ICU DEFINITE_LOCUM_ICU')

class Constraint(BaseConstraint):
    """Leavebook entry"""
    def __init__(self, rota, **kwargs):
        super().__init__(rota, **kwargs)
        self.leavebook={}

    def apply_constraint(self):
        data = self.kwargs.get('current_rota')
        for day in data:
            for shift in data[day]:
                for staff in data[day][shift]:
                    self.leavebook[(Staff[staff],Shifts[shift],day)]=data[day][shift][staff]
        for staff in Staff:
            for shift in Shifts:
                for day in self.days():
                    text_day=(self.rota.startdate+timedelta(days=day)).isoformat()
                    this_duty = self.leavebook.get((staff, shift, text_day), None)
                    if this_duty not in ['LEAVE','NOC']:
                        self.rota.model.Add(self.rota.get_duty(
                            Duties.LEAVE, day, shift, staff) == 0)
                    if this_duty == 'ICU_MAYBE_LOCUM':
                        self.rota.model.Add(self.rota.get_duty(
                            Duties.ICU, day, shift, staff) == 1)
                    elif this_duty == 'DEFINITE_ICU':
                        self.rota.model.Add(self.rota.get_duty(
                            Duties.QUOTA_ICU, day, shift, staff) == 1)
                    elif this_duty=='DEFINITE_LOCUM_ICU':
                        self.rota.model.Add(self.rota.get_duty(
                            Duties.LOCUM_ICU, day, shift, staff) == 1)
                    elif this_duty in ['NOC','LEAVE']:
                        self.rota.model.Add(self.rota.get_duty(
                            Duties.LEAVE, day, shift, staff) == 1)
                    elif this_duty=='ICU':
                        self.rota.model.AddHint(self.rota.get_duty(
                            Duties.ICU, day, shift, staff),1)
                    elif this_duty=='LOCUM_ICU':
                        self.rota.model.AddHint(self.rota.get_duty(
                            Duties.LOCUM_ICU, day, shift, staff), 1)

    def process_output(self,solver, pairs):
        for ((staff,shift,day),value) in pairs:
            text_day = (self.rota.startdate+timedelta(days=day)).isoformat()
            leavebook_duty = self.leavebook.get((staff, shift, text_day))
            if leavebook_duty in ['DEFINITE_ICU','DEFINITE_LOCUM_ICU','NOC']:
                yield ((staff,shift,day),leavebook_duty)
            elif leavebook_duty=='ICU_MAYBE_LOCUM':
                yield ((staff,shift,day),'DEFINITE_ICU' if value=='ICU' else 'DEFINITE_LOCUM_ICU')
            else:
                yield ((staff,shift,day),value)
    
