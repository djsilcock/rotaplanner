"""constraint manager"""

#from solver import RotaSolver


from collections import namedtuple
from datetime import date
import re
import json
from importlib import import_module
from typing import Literal, Optional, Union

from ortools.sat.python import cp_model
from abstracttypes import RotaSolver
import constraints

constraint_store = {}

reg = re.compile(r'(?:^[a-z]+)|(?:[A-Z]+[a-z]+)')

ValidationResult = Union[Literal[False], str]


class BaseConfig():
    "holds configuration values for constraint"

    def __init__(self, config: dict):
        self._values = self.get_defaults()
        updates = {k: v for k, v in config.items() if k in self._values}
        self._values.update(updates)
        self._validators={k:getattr(self,f"validate_{k}",lambda x:False) for k in self._values}

    def get_defaults(self) -> dict:
        "returns default values for object"
        return {
            'enabled': True,
            'startdate': None,
            'enddate': None,
            'exclusions': []
        }

    def errors(self) -> Optional[dict]:
        "return dict of errors, or None if validates"
        errors = {k: validator(v, self._values) for k, validator in self._validators.items()}
        return {f: errors[f] for f in errors if errors[f]} if any(errors.values()) else None

    def validate_startdate(self, value) -> ValidationResult:
        "Validates start and end dates"
        if value is None or value == "":
            return False
        try:
            date.fromisoformat(value)
        except ValueError:
            return 'Start date is not valid'
        if all(
                self.values['enddate'] is not None,
                self.values['startdate'] is not None,
                self.values['startdate'] < self.values['enddate']):
            return 'end date cannot be before start date'

    def validate_enddate(self, value) -> ValidationResult:
        "Validates start and end dates"
        if value is None or value == "":
            return False
        try:
            date.fromisoformat(value)
        except ValueError:
            return 'End date is not valid'

    def validate_exclusions(self, value) -> ValidationResult:
        "validate exclusions"
        Exclusion = namedtuple('Exclusion', 'start end', defaults=[None, None])
        if value is None:
            return False
        if isinstance(value, list):
            if len(value) == 0:
                return False
            exclusions = [Exclusion(**exc) for exc in value]
            for exc in exclusions:
                try:
                    if exc.start is not None:
                        date.fromisoformat(exc.start)
                    if exc.end is not None:
                        date.fromisoformat(exc.end)
                    if exc.start is not None and exc.end is not None:
                        raise ValueError()
                except ValueError:
                    return f'{exc.start} - {exc.end} is not a valid time period'

    def set(self, key, value):
        "set a value"
        self._values[key] = getattr(
            self, f'sanitize_{key}', lambda x: x)(value)

    def get(self, key, default=None):
        "retrieve a value"
        return self._values.get(key, default)

    def values(self):
        "return all values"
        return {**self._values}


class BaseConstraint():
    """base class for constraints"""
    #pylint: disable=unused-argument

    dependencies = []
    name = ""
    is_configurable = True
    config_class=BaseConfig

    def get_constraint_atom(self, **kwargs):
        """Boolean atom for enforcement"""
        name = json.dumps(
            dict(id=self.kwargs['id'], constraint=self.kwargs['constraint'], **kwargs))
        enforce_this = self.rota.model.NewBoolVar(
            name if name is not None else self.name)
        self.rota.constraint_atoms.append(enforce_this)
        return enforce_this

    def __init__(
            self,
            rota: RotaSolver,
            *, daterange=None,
            weekdays=None,
            **kwargs):
        self.rota: RotaSolver = rota
        self.model: cp_model.CpModel = rota.model
        config=self.config_class(kwargs).values()
        self.variables = {}
        self.startdate = config.pop('startdate')
        self.enddate = config.pop('enddate')
        self.exclusions=config.pop('exclusions')
        self.weekdays = weekdays
        self.kwargs = config

    
    def days(self, *filters):
        """return iterator of days"""
        def filterfunc(day):
            return all((f(day) for f in filters))
        return filter(
            filterfunc,
            self.rota.days(self.startdate, self.enddate, self.weekdays, self.exclusions))

    def get_duty(self, key):
        "Retrieve a duty"
        return self.rota.get_duty_base(key)

    def create_duty(self, key):
        "Create a new duty"
        return self.rota.create_duty_base(key)

    def get_or_create_duty(self, key):
        "Create a new duty if no matching duty exists"
        return self.rota.get_or_create_duty_base(key)

    def add_rule(self, rule):
        "Add rule to model"
        return self.rota.model.Add(rule)

    def apply_constraint(self):
        """apply constraint to model"""
        return

    def event_stream(self, solver, event_stream):
        """called after solver has completed"""
        yield from (event_stream if event_stream is not None else [])

    def process_output(self, solver, pairs):
        """process output"""
        return pairs

    def build_output(self, solver, outputdict):
        """build output dict in format outputdict[date][shift][name]=duty"""
        return outputdict

    def remove(self):
        """remove constraint from model"""
        return


def apply_constraint(model, **kwargs):
    """Apply constraint spec. Use as apply_constraint(model,**constraintspec)"""
    constraint = kwargs['constraint']
    constraintid = kwargs['id']
    print(f'applying:{constraint}')
    constraint = constraint.lower()
    if (constraint, constraintid) in model.constraints:
        print(f'overwriting {constraintid}')
        del model.constraints[(constraint, constraintid)]
    model.constraints[(constraint, constraintid)] = import_module(
        f'constraints.{constraint}').Constraint(
        model, **kwargs)


def get_constraint_config(constraintspec: dict):
    "get constraint configuration from spec file"
    def rule_mapper1(entry):
        constraint_type, rules = entry
        constraint_class = import_module(
            f'constraints.{constraint_type}').Constraint

        def rule_mapper2(entry):
            ruleid, rule_spec = entry
            return {
                "id": ruleid,
                "form": constraint_class.get_config_interface(rule_spec),
                "values": rule_spec
            }
        return {
            'id': constraint_type,
            'title': constraint_class.name,
            'addButton': constraint_class.is_configurable,
            'forms': list(map(rule_mapper2, rules))
        }
    return map(rule_mapper1, constraintspec.items())
