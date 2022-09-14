"""contains rules to constrain the model"""
from calendar import SATURDAY
from collections import namedtuple

from constants import Shifts, Staff
from constraints.constraintmanager import BaseConstraint
from constraints.core_duties import icu

Config=namedtuple('Config','numerator denominator')
class Constraint(BaseConstraint):
    """Maximum number of oncalls per given number of days"""
    name = "Limit oncall frequency"

    @classmethod
    def validate_config(cls, config):
        config=Config(**config)
        if config.denominator<config.numerator:
            raise ValueError(f'Cannot do {config.numerator} in only {config.denominator} days')
        return config

    @classmethod
    def get_config_interface(cls,config):
        yield 'same consultant should not do more than'
        yield {
            'name': 'numerator',
            'component': 'number',
            'value':config}
        yield 'oncalls in any'
        yield {
            'name': 'denominator',
            'component': 'number'}
        yield 'consecutive days'

    def apply_constraint(self):
        kwargs = dict(**self.kwargs)
        denominator = kwargs.pop('denominator')
        numerator = kwargs.pop('numerator')
        enforced = self.get_constraint_atom()
        for day in self.days():
            enforced = self.get_constraint_atom(day=day)
            if day < denominator:
                continue
            for staff in Staff:
                self.rota.model.Add(
                    sum(self.get_duty(icu(Shifts.ONCALL,dd,staff))
                        for dd in range(day-denominator, day)) +
                    sum(self.get_duty(icu(Shifts.AM,dd, staff))
                        for dd in range(day-denominator, day) if dd % 7 == SATURDAY) <= numerator
                ).OnlyEnforceIf(enforced)
