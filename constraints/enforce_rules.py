"""contains rules to constrain the model"""

from constraints.utils import BaseConstraint

class Config():
    def get_defaults(self) -> dict:
        return dict(**super().get_defaults(),enforcement=True)
    def get_config_interface(self):
        return ['rules', {
            'component': 'select',
            'name': 'enforcement',
            'options': ['must', 'should']}, 'be enforced']
from constraints.constraint_store import register_constraint

@register_constraint('enforce_rules')           
class Constraint(BaseConstraint):
    """Enforce all rules"""
    name = "Enforce Rules"
    config_class=Config

    def apply_constraint(self):
        if self.kwargs.get('enforcement') == 'mustm':
            for constraint in self.rota.constraint_atoms:
                self.model.Add(constraint == 1)
        else:
            self.rota.minimize_targets.extend(atom.Not() for atom in self.rota.constraint_atoms)

    def event_stream(self, solver, event_stream):
        yield from event_stream
        for atom in self.rota.constraint_atoms:
            if solver.Value(atom) == 0:
                print(f'{atom.Name()} failed')
                yield {'type': 'statistic',
                       'constraint_fail': atom.Name()}
