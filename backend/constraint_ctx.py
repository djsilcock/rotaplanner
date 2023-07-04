from inspect import signature
from typing import TYPE_CHECKING, Any, Callable
import asyncio

from signals import Signal
if TYPE_CHECKING:
    from ortools.sat.python import cp_model

    
            
    
class DutyStore(dict):
    "creates cp_model.BoolVar instances"
    def __init__(self, model: 'cp_model.CpModel'):
        super().__init__()
        self.model = model
    def __missing__(self, key):
        self[key] = self.model.NewBoolVar(repr(key))
        return self[key]

class SignalSet:
    def __init__(self):
        self.result=Signal()
        self.before_apply=Signal()
        self.after_apply=Signal()

class ConstraintContext:
    __protected_names=()
    def __init__(self,/,model):
        super().__init__()
        self.model=model
        self.dutystore=DutyStore(model)
        self.__runonce_cache={}
        self.signals=SignalSet()
        self.__protected_names=('model','dutystore','signals','runonce')
    def __setattr__(self, __name: str, __value: Any) -> None:
        if __name in self.__protected_names:
            raise TypeError(f'cannot assign to {__name} after initialisation')
        return super().__setattr__(__name,__value)
    def runonce(self,func):
        try:
            return self.__runonce_cache[id(func)]
        except KeyError:
            retval=func(self)
            self.__runonce_cache[id(func)]=retval
            return retval
    



