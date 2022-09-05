"""constraint manager"""

#from solver import RotaSolver


import re
import json
from importlib import import_module
import pkgutil

from abstracttypes import RotaSolver
import constraints

constraint_store = {}

reg = re.compile(r'(?:^[a-z]+)|(?:[A-Z]+[a-z]+)')


class ConstraintMeta(type):
    """Registering metaclass"""
    def __new__(cls, name, bases, members):
        result = type.__new__(cls, name, bases, members)
        sc_name = '_'.join([s.lower() for s in reg.findall(name)])
        print(f'Registering: {sc_name}')
        print(__name__)
        constraint_store[sc_name] = result
        return result


class BaseConstraint():
    """base class for constraints"""
    #pylint: disable=unused-argument

    dependencies = []
    name = ""

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
        self.model=rota.model
        self.variables={}
        self.startdate = daterange.get(
            'startdate') if daterange is not None else None
        self.enddate = daterange.get(
            'enddate') if daterange is not None else None
        self.weekdays = weekdays
        self.exclusions = daterange.get(
            'exclusions') if daterange is not None else None
        self.kwargs = kwargs
        
    @classmethod
    def definition(cls):
        """form definition for frontend"""
        yield from []

    def days(self,*filters):
        """return iterator of days"""
        def filterfunc(day):
                return all((f(day) for f in filters))
        return filter(filterfunc,self.rota.days(self.startdate, self.enddate, self.weekdays, self.exclusions))

    def get_duty(self,key):
        "Retrieve a duty"
        return self.rota.get_duty_base(key)
    def create_duty(self,key):
        "Create a new duty"
        return self.rota.create_duty_base(key)
    def get_or_create_duty(self,key):
        "Create a new duty if no matching duty exists"
        return self.rota.get_or_create_duty_base(key)
    def add_rule(self,rule):
        "Add rule to model"
        return self.rota.model.Add(rule)

    def apply_constraint(self):
        """apply constraint to model"""
        return

    def event_stream(self, solver, event_stream):
        """called after solver has completed"""
        yield from (event_stream if event_stream is not None else [])

    def process_output(self,solver,pairs):
        """process output"""
        return pairs

    def build_output(self,solver,outputdict):
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
    model.constraints[(constraint, constraintid)] = import_module(f'constraints.{constraint}').Constraint(
        model, **kwargs)


def get_constraint_config():
    """get form definition for settings page"""
    config={}
    for mod in pkgutil.iter_modules(constraints.__path__):
        constraint_module=import_module(f'constraints.{mod.name}')
        if hasattr(constraint_module,'Constraint'):
            config[mod.name]={
                'name':constraint_module.Constraint.name,
                'definition':list(constraint_module.Constraint.definition())}
    
    return config