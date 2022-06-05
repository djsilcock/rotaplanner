"""contains rules to constrain the model"""


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

        for allocation in data:
            staff = Staff[allocation['name']]
            shift = Shifts[allocation['shift']]
            day = allocation['day']
            duty = allocation['duty']
            self.leavebook[(staff, shift, day)] = duty
        for staff in Staff:
            for shift in Shifts:
                for day in self.days():
                    this_duty = self.leavebook.get((staff, shift, day), None)
                    if this_duty not in ['LEAVE','NOC']:
                        self.rota.model.Add(self.rota.get_duty(
                            Duties.LEAVE, day, shift, staff) == 0)
                    if this_duty == 'DEFINITE_ICU':
                        self.rota.model.Add(self.rota.get_duty(
                            Duties.ICU, day, shift, staff) == 1)
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
            leavebook_duty = self.leavebook.get((staff, shift, day))
            if leavebook_duty in ['DEFINITE_ICU','DEFINITE_LOCUM_ICU','NOC']:
                yield ((staff,shift,day),leavebook_duty)
            else:
                yield ((staff,shift,day),value)
