"""contains rules to constrain the model"""


from datetime import timedelta
from constants import Shifts, Staff
from constraints.constraintmanager import BaseConstraint
from constraints.core_duties import leave, icu
from constraints.some_shifts_are_locum import quota_icu, locum_icu


class Constraint(BaseConstraint):
    """Leavebook entry"""

    def __init__(self, rota, **kwargs):
        super().__init__(rota, **kwargs)
        self.leavebook = {}

    def apply_constraint(self):
        data = self.kwargs.get('current_rota')
        for day in data:
            for shift in data[day]:
                for staff in data[day][shift]:
                    self.leavebook[(Staff[staff], Shifts[shift],
                                    day)] = data[day][shift][staff]
        for staff in Staff:
            for shift in Shifts:
                for day in self.days():
                    text_day = (self.rota.startdate +
                                timedelta(days=day)).isoformat()
                    this_duty = self.leavebook.get(
                        (staff, shift, text_day), None)

                    is_on_leave = self.get_duty(leave(shift, day, staff))

                    self.model.Add(is_on_leave == (
                        this_duty in ('LEAVE', 'NOC')))

                    implications = [
                        (this_duty == 'ICU_MAYBE_LOCUM',
                         self.get_duty(icu(shift, day, staff))),
                        (this_duty == 'DEFINITE_ICU', self.get_duty(
                            quota_icu(shift, day, staff))),
                        (this_duty == 'DEFINITE_LOCUM_ICU',
                         self.get_duty(locum_icu(shift, day, staff)))
                    ]
                    for if_this, then_that in implications:
                        self.model.AddImplication(if_this, then_that)

                    if this_duty == 'ICU':
                        self.model.AddHint(self.get_duty(
                            icu(shift, day, staff)), 1)
                    elif this_duty == 'LOCUM_ICU':
                        self.model.AddHint(self.get_duty(
                            locum_icu(shift, day, staff)), 1)

    def process_output(self, solver, pairs):
        for ((staff, shift, day), value) in pairs:
            text_day = (self.rota.startdate+timedelta(days=day)).isoformat()
            leavebook_duty = self.leavebook.get((staff, shift, text_day))
            if leavebook_duty in ['DEFINITE_ICU', 'DEFINITE_LOCUM_ICU', 'NOC']:
                yield ((staff, shift, day), leavebook_duty)
            elif leavebook_duty == 'ICU_MAYBE_LOCUM':
                yield ((staff, shift, day), 'DEFINITE_ICU' if value == 'ICU' else 'DEFINITE_LOCUM_ICU')
            else:
                yield ((staff, shift, day), value)
