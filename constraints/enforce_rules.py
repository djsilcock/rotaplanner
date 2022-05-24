"""contains rules to constrain the model"""

from constraints.constraintmanager import BaseConstraint


class Constraint(BaseConstraint):
    """Enforce all rules"""
    name = "Enforce Rules"

    @classmethod
    def definition(cls):
        return ['rules', {
            'component': 'select',
            'name': 'enforcement',
            'options': ['must', 'should']}, 'be enforced']

    def apply_constraint(self):
        if self.kwargs.get('enforcement') == 'must':
            for constraint in self.rota.constraint_atoms:
                self.rota.model.Add(constraint == 1)
        else:
            self.rota.model.Maximize(sum(self.rota.constraint_atoms))

    def event_stream(self, solver, event_stream):
        yield from event_stream
        for atom in self.rota.constraint_atoms:
            if solver.Value(atom) == 0:
                print(f'{atom.Name()} failed')
                yield {'type': 'statistic',
                       'constraint_fail': atom.Name()}
