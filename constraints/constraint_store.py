"Repository for constraint classes"
from typing import TYPE_CHECKING,Type

_constraint_store={}
_templates=set()

if TYPE_CHECKING:
    from constraints.base import BaseConstraint

def register_constraint(name,constraint_class=None):
    """Register constraint

    Usage:

    register_constraint(name:str,constraint_class:BaseConstraint)

    @register_constraint(name)

    class Constraint(BaseConstraint)
      ..."""
    def _decorator(class_to_decorate):
        _constraint_store[name]=class_to_decorate
        class_to_decorate.constraint_type=name
        if class_to_decorate.template_dir is not None:
            if isinstance(class_to_decorate.template_dir,(tuple,list)):
                _templates.update(str(x) for x in class_to_decorate.template_dir)
            else:
                _templates.add(str(class_to_decorate.template_dir))
        return class_to_decorate
    if constraint_class is None:
        return _decorator
    return _decorator(constraint_class)

def get_constraint_class(name:str) -> 'Type[BaseConstraint]':
    return _constraint_store[name]

def get_all_constraint_classes() ->dict[str,'Type[BaseConstraint]']:
    return dict(_constraint_store)

def get_all_template_folders():
    return list(_templates)
    