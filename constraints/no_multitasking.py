"""contains rules to constrain the model"""



from constants import Shifts, Staff, Duties
from constraints.constraintmanager import BaseConstraint


class Constraint(BaseConstraint):
    """Block duties which cannot exist simultaneously"""
    name = "No multi-tasking"

    def apply_constraint(self):
        for day in self.days():
            for staff in Staff:
                for shift in Shifts:
                    dutyset = {Duties.ICU, Duties.THEATRE,
                               Duties.OFF, Duties.LEAVE}
                    self.rota.model.Add(sum(self.rota.get_or_create_duty(duty, day, shift, staff)
                                            for duty in dutyset) == 1)
