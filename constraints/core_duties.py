

from constants import Shifts, Staff, Duties
from constraints.constraintmanager import BaseConstraint


class Constraint(BaseConstraint):
    """Defines core duty set and requirement that one person is on for ICU"""
    name = 'Core duties'

    def apply_constraint(self):
        for day in self.days():
            for shift in Shifts:
                for staff in Staff:
                    self.rota.create_duty(Duties.ICU, day, shift, staff)
                self.rota.model.Add(
                    sum(self.rota.get_duty(Duties.ICU, day, shift, staff)
                        for staff in Staff) == 1
                )

    def event_stream(self, solver, event_stream):
        yield from event_stream
        for day in self.days():
            for staff_member in Staff:
                for shift in Shifts:
                    for duty in [Duties.ICU, Duties.THEATRE]:
                        if solver.Value(self.rota.get_duty(duty, day, shift, staff_member)):
                            yield (
                                {'type': 'duty',
                                 'dutyType': duty.name,
                                 'day': day,
                                 'shift': shift.name,
                                 'name': staff_member.name})
