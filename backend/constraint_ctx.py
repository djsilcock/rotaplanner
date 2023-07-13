"constraint context"
from inspect import isawaitable
from typing import TYPE_CHECKING, Any,Type,Self


from signals import Signal
if TYPE_CHECKING:
    from ortools.sat.python import cp_model
    from solver import CoreConfig


class DutyStore(dict):
    "creates cp_model.BoolVar instances"
    def __init__(self, model: 'cp_model.CpModel'):
        super().__init__()
        self.model = model
    def __missing__(self, key):
        self[key] = self.model.NewBoolVar(repr(key))
        return self[key]

class SignalSet:
    """attributes:

    result signal(staff,day,shift,sessionduty,solver)

    before_apply (ctx)

    after_apply (ctx)
    """
    def __init__(self):
        self.result=Signal()
        self.before_apply=Signal()
        self.after_apply=Signal()

registered_constraints=dict()

class BaseConstraintConfig:
    constraint_name=None
    def __init__(self,ctx:'ConstraintContext'):
        self.ctx=ctx
        self.dutystore=DutyStore(ctx.model)
        if self.constraint_name is not None:
            if self.constraint_name in ctx.config:
                raise TypeError(f'{self.constraint_name} already registered for this context')
            ctx.config[self.constraint_name]=self
    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        if cls.constraint_name is not None:
            if cls.constraint_name in registered_constraints:
                raise TypeError(f'constraint {cls.constraint_name} is already registered')
            registered_constraints[cls.constraint_name]=cls
    @property
    def model(self):
        return self.ctx.model
    @property
    def core_config(self):
        return self.ctx.core_config
    @classmethod
    def from_context(cls,ctx)->Self:
        if cls.constraint_name is None:
            raise TypeError(f'Class {cls} does not register with constraint context')
        try:
            return ctx.config[cls.constraint_name]            
        except KeyError:
            return cls(ctx)
    def apply_constraint(self):
        pass
    def result(self,staff,day,shift,sessionduty,solution):
        pass
    

class ConstraintContext:
    """Constraint context"""
    __protected_names=()
    def __init__(self,/,model,core_config:'CoreConfig'):
        super().__init__()
        self.model=model
        self.core_config=core_config
        self.dutystore=DutyStore(model)
        self.config={}
        self.__runonce_cache={}
        self.signals=SignalSet()
        self.__protected_names=('model','dutystore','signals','runonce','config','core_config')
    def __setattr__(self, __name: str, __value: Any) -> None:
        if __name in self.__protected_names:
            raise TypeError(f'cannot assign to {__name} after initialisation')
        return super().__setattr__(__name,__value)
    def runonce(self,func):
        "run wrapped function only once"
        try:
            return self.__runonce_cache[id(func)]
        except KeyError:
            retval=func(self)
            self.__runonce_cache[id(func)]=retval
            return retval
    async def apply_constraints(self):
        constraint_results=[cons.apply_constraint() for cons in self.config.values()]
        for r in constraint_results:
            if isawaitable(r):
                await r
    async def result(self,staff,day,shift,sessionduty,solution):
        constraint_results=[cons.result(staff,day,shift,sessionduty,solution) for cons in self.config.values()]
        for r in constraint_results:
            if isawaitable(r):
                await r

