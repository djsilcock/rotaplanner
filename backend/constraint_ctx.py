from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ortools.sat.python import cp_model

class Signal:
    def __init__(self):
        self.handlers=[]
    def connect(self,func):
        if func not in self.handlers:
            self.handlers.append(func)
        return func
    def emit(self,__sender=None,**kwargs):
        return [handler(__sender,**kwargs) for handler in self.handlers]
    
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
    core:Any
    def __init__(self,/,model):
        super().__init__()
        self.model=model
        self.dutystore=DutyStore(model)
        self.__runonce_cache={}
        self.signals=SignalSet()
    def runonce(self,func):
        try:
            return self.__runonce_cache[id(func)]
        except KeyError:
            retval=func(self)
            self.__runonce_cache[id(func)]=retval
            return retval
    



