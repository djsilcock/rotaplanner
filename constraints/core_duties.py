

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

    def process_output(self, solver, pairs):
        for day in self.days():
            for duty in [Duties.ICU, Duties.THEATRE,Duties.LEAVE,Duties.OFF]:
                for shift in Shifts:
                    for staff in Staff:
                        if solver.Value(self.rota.get_duty(duty, day, shift, staff)):
                            yield ((staff,shift,day),duty.name)


