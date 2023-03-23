"""constraint manager"""


import json
import pathlib
from typing import TYPE_CHECKING
from collections import deque
import dataclasses


if TYPE_CHECKING:
    from solver import GenericConfig
    from ortools.sat.python import cp_model
    from sqlalchemy.orm import Session

@dataclasses.dataclass
class ContextClass:
    "dummy contextclass"


class BaseConstraint():
    """base class for constraints"""
    #pylint: disable=unused-argument
    is_configurable = True
    template_dir = pathlib.Path(__file__).with_name('templates')
    constraint_type: str
    ctx:'GenericConfig'

    def __init__(self,ctx):
        self.ctx=ctx

    def get_constraint_atom(self, **kwargs):
        """Boolean atom for enforcement"""
        generic_context = self.ctx
        name = ('constraint', json.dumps(
            dict(constraint=self.constraint_type, **kwargs)))
        enforce_this = generic_context.dutystore[name]
        generic_context.constraint_atoms.append(enforce_this)
        return enforce_this

    def days(self, *filters):
        """return iterator of days"""
        assert self.ctx.days is not None
        return (d for d in self.ctx.days if all(f(d) for f in filters))

    def sliding_date_range(self,length=1, pre_filters=None):
        "returns window of dates.Pre-filters are passed to underlying days iterator"
        if pre_filters is None:
            pre_filters = []
        date_deque = deque(maxlen=length)
        for day in self.days(*pre_filters):
            date_deque.append(day)
            if len(date_deque) == length:
                yield date_deque

    def apply_constraint(self):
        "Apply constraint"

    def build_output(self,outputdict,solver):
        "Generate output (in-place)"
