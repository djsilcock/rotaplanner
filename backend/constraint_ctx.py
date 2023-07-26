"constraint context"
from inspect import isawaitable
from typing import TYPE_CHECKING,Self,Generic, Type,TypeVar
from ortools.sat.python import cp_model

from datatypes import SessionDuty

if TYPE_CHECKING:
    from solver import CoreConfig

DutyKey=TypeVar('DutyKey')

class DutyStore(Generic[DutyKey]):
    "creates cp_model.BoolVar instances"
    def __init__(self, model: 'cp_model.CpModel'):
        self.model = model
        self.store={}
    def __getitem__(self, key:DutyKey):
        if key not in self.store:
            self.store[key]=self.model.NewBoolVar(repr(key))
        return self.store[key]
    def __setitem__(self,key,value):
        raise TypeError('Dutystore is readonly')

_registered_constraints=dict()

class BaseConstraintConfig():
    "Base constraint class"
    constraint_name=None
    _ctx=None
    def __init__(self,ctx:'ConstraintContext'|None=None):
        if ctx:
            self._ctx=ctx
            if self.constraint_name is not None:
                if self.constraint_name in ctx.constraints:
                    raise TypeError(f'{self.constraint_name} already registered for this context')
                ctx.constraints[self.constraint_name]=self
                self.configure()
    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        if cls.constraint_name is not None:
            if cls.constraint_name in _registered_constraints:
                raise TypeError(f'constraint {cls.constraint_name} is already registered')
            _registered_constraints[cls.constraint_name]=cls
    def configure(self):
        "configuration options for constraint"
    
    @property
    def ctx(self) -> 'ConstraintContext':
        "constraint context"
        if self._ctx is None:
            raise ValueError('not registered to a constraint context')
        return self._ctx
    @property
    def model(self) -> cp_model.CpModel:
        "return currently used model"
        return self.ctx.model
    @property
    def core_config(self) -> 'CoreConfig':
        "return the core configuration"
        return self.ctx.config['core']
    @classmethod
    def from_context(cls,ctx)->Self:
        "return the constraint instance associated with this context"
        if cls.constraint_name is None:
            raise TypeError(f'Class {cls} does not register with constraint context')
        try:
            return ctx.constraints[cls.constraint_name]
        except KeyError:
            return cls(ctx)
    def apply_constraint(self):
        "apply constraint to model"
    def result(self,staff,day,shift,sessionduty,solution):
        "modify result sessionduty inplace"

    @classmethod
    def from_frontend_json(cls,json_config) -> Self:
        "process json config from frontend"
        raise NotImplementedError
    @classmethod
    def get_ui_config(cls,datastore):
        "get ui config for given request"
    def save_config(self,datastore):
        "save config to datastore"
    

class ConstraintContext:
    """Constraint context"""
    def __init__(self,/,config):
        super().__init__()
        self.model=cp_model.CpModel()
        self.constraints={}
        self.config=config
        self.__runonce_cache={}
    @property
    def core_config(self) ->'CoreConfig':
        "core configuration"
        return self.config['core']
    def runonce(self,func):
        "run wrapped function only once"
        try:
            return self.__runonce_cache[id(func)]
        except KeyError:
            retval=func(self)
            self.__runonce_cache[id(func)]=retval
            return retval
    async def apply_constraints(self):
        "apply all constraints"
        constraint_results=[
            cons.from_context(self).apply_constraint() 
            for cons in get_registered_constraints().values()]
        for r in constraint_results:
            if isawaitable(r):
                await r
    async def result(self,solution):
        "generate result from solution"
        outputdict = {}
        for day in self.core_config.days:
            for staff in self.core_config.staff:
                for shift in self.core_config.shifts:
                    sessionduty = SessionDuty()    
                    for cons in self.constraints.values():
                        r=cons.result(staff,day,shift,sessionduty,solution)
                        if isawaitable(r):
                            await r
                    outputdict[(day, staff, shift)] = sessionduty
        

def get_registered_constraints() ->dict[str,BaseConstraintConfig]:
    "return list of all registered constraints"
    return dict(_registered_constraints)
