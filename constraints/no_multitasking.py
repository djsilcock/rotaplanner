"""contains rules to constrain the model"""



from constants import Shifts, Staff
from constraints.constraintmanager import BaseConstraint
from constraints.core_duties import icu, nonclinical, theatre


class Constraint(BaseConstraint):
    """Block duties which cannot exist simultaneously"""
    name = "No multi-tasking"

    def apply_constraint(self):
        for day in self.days():
            for staff in Staff:
                for shift in Shifts:
                    duties=(icu,theatre,nonclinical)
                    self.model.AddBoolXOr(
                        [self.get_duty(duty(shift,day,staff)) for duty in duties]
                    )
