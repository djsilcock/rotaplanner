"""contains rules to constrain the model"""
from calendar import THURSDAY



from config import Shifts, Staff
from constraints.utils import BaseConstraint
from constraints.core_duties import icu

class Constraint(BaseConstraint):
    """week not followed by weekend"""
    name = "Weekend not following week"

    @classmethod
    def definition(cls):

        yield 'an ICU weekend should not follow an ICU week'

    def apply_constraint(self):
        self.weekdays = [THURSDAY]
        for day in self.days():
            enforced = self.get_constraint_atom(day=day)
            for staff in Staff:
                thursday_am = self.get_duty(icu(Shifts.AM, day, staff))
                friday_am = self.get_duty(icu(Shifts.AM, day+1, staff))
                thursday_oc = self.get_duty(icu(Shifts.ONCALL, day, staff))
                friday_oc = self.get_duty(icu(Shifts.ONCALL, day+1, staff))

                prohibited=[
                    (thursday_am,friday_am),
                    (thursday_oc,friday_am),
                    (thursday_am,friday_oc),
                    (thursday_oc,friday_oc)
                ]
                for left,right in prohibited:
                    self.model.AddBoolOr([left.Not(),right.Not()])
                