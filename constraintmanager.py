"""constraint manager"""

#from solver import RotaSolver


import re
from abstracttypes import RotaSolver


constraint_store = {}

reg = re.compile(r'(?:^[a-z]+)|(?:[A-Z]+[a-z]+)')

class ConstraintMeta(type):
    """Registering metaclass"""
    def __new__(cls, name, bases, members):
        result = type.__new__(cls, name, bases, members)
        sc_name='_'.join([s.lower() for s in reg.findall(name)])
        print(f'Registering: {sc_name}')
        constraint_store[sc_name] = result
        return result


class Constraint(metaclass=ConstraintMeta):
    """base class for constraints"""
    #pylint: disable=unused-argument

    def __init__(
            self,
            rota: RotaSolver,
            *, startdate=None,
            enddate=None,
            weekdays=None,
            exclusions=None,
            **kwargs):
        self.rota: RotaSolver = rota
        self.startdate = startdate
        self.enddate = enddate
        self.weekdays = weekdays
        self.exclusions = exclusions
        self.kwargs = kwargs

    @classmethod
    def definition(cls):
        """form definition for frontend"""
        yield from []

    def days(self):
        """return iterator of days"""
        return self.rota.days(self.startdate, self.enddate, self.weekdays, self.exclusions)

    def apply_constraint(self):
        """apply constraint to model"""
        return self.define_constraint(**self.kwargs)

    def define_constraint(self, **kwargs):
        """actual constraint definition"""
        return

    def event_stream(self, solver, event_stream):
        """called after solver has completed"""
        yield from (event_stream if event_stream is not None else [])

    def remove(self):
        """remove constraint from model"""
        return


def register_constraint(constraintfunc):
    """Decorator to register constraint functions"""
    constraint_store[constraintfunc.__name__] = constraintfunc
    return constraintfunc


def apply_constraint(model, constraint, **kwargs):
    """Apply constraint spec. Use as apply_constraint(model,**constraintspec)"""
    print(f'applying:{constraint}')
    constraint = constraint.lower()
    if constraint not in constraint_store:
        raise KeyError(f'unknown constraint:{constraint}')
    constraintid = kwargs.pop('id')
    if constraintid in model.constraints:
        print(f'overwriting {constraintid}')
        del model.constraints[constraintid]
    model.constraints[constraintid] = constraint_store[constraint](
        model, **kwargs)

def get_constraint_config(name=None):
    """get form definition for settings page"""
    if name is None:
        return {k:get_constraint_config(k) for k in constraint_store}
    return list(constraint_store[name].definition())
