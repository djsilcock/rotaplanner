"""contains rules to constrain the model"""
from calendar import SATURDAY




from constants import Shifts, Staff, Duties
from constraints.constraintmanager import BaseConstraint


class Constraint(BaseConstraint):
    """Maximum x weekends (day or night) in any y weekends"""
    name = "Limit Weekend Frequency"

    @classmethod
    def definition(cls):

        yield 'same consultant should not do more than'
        yield {
            'name': 'numerator',
            'component': 'number'}
        yield 'weekends in any'
        yield {
            'name': 'denominator',
            'component': 'number'}

    def apply_constraint(self):
        #print(f'Maximum {numerator} weekends in {denominator}...')

        kwargs = dict(**self.kwargs)
        denominator = kwargs.pop('denominator')
        numerator = kwargs.pop('numerator')
        self.weekdays = [SATURDAY]
        for day in self.days():
            enforced = self.get_constraint_atom(day=day)
            if day < (7*denominator):
                continue
            for staff in Staff:

                self.rota.model.Add(sum(self.rota.get_duty(Duties.ICU, dd, Shifts.DAYTIME, staff)
                                        for dd in range(day-(7*denominator), day, 7)) +
                                    sum(self.rota.get_duty(Duties.ICU, dd,  Shifts.ONCALL, staff)
                                        for dd in range(day-(7*denominator), day, 7)) <= numerator
                                    ).OnlyEnforceIf(enforced)
