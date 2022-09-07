"""contains rules to constrain the model"""
from calendar import MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY


from constants import Shifts, Staff
from constraints.constraintmanager import BaseConstraint
from constraints.some_shifts_are_locum import quota_icu


class Constraint(BaseConstraint):
    """Maximum deviation from target number of shifts of any given type (excluding locums)"""
    name = "Minimise deviation from average"

    @classmethod
    def definition(cls):

        yield 'same consultant should not be more than'
        yield {
            'name': 'deviation',
            'component': 'number'}
        yield {
            'name': 'shift',
            'component': 'select',
            'options': [
                'Weekend oncall',
                'Weekend daytime',
                'Weekday oncall',
                'Weekday daytime',
                'Any weekend']}
        yield 'shifts above or below target'

    def apply_constraint(self):
        kwargs = dict(**self.kwargs)
        shift_to_check = kwargs.pop('shift').lower()
        self.variables['shift_to_check'] = shift_to_check
        deviation_hard_limit = kwargs.pop('deviation')
        enforced = self.get_constraint_atom()
        (days, shifts) = {
            'weekend oncall': ([FRIDAY, SATURDAY, SUNDAY], [Shifts.ONCALL]),
            'weekend daytime': ([FRIDAY, SATURDAY, SUNDAY], [Shifts.AM,Shifts.PM]),
            'weekday oncall': ([MONDAY, TUESDAY, WEDNESDAY, THURSDAY], [Shifts.ONCALL]),
            'weekday daytime': ([MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY], [Shifts.AM,Shifts.PM]),
            'any weekend': ([FRIDAY, SATURDAY, SUNDAY], [Shifts.ONCALL, Shifts.AM,Shifts.PM])
        }[shift_to_check]
        deviation_soft_limits={}
        self.variables['dsl'] = deviation_soft_limits
        period_duration=9*7
        for day in self.days():
            if day//period_duration not in deviation_soft_limits:
                deviation_soft_limits[day//period_duration] = self.rota.model.NewIntVar(
                    0,
                    deviation_hard_limit,
                    f'soft-limit{shift_to_check}{day//period_duration}')
            deviation_soft_limit=deviation_soft_limits[day//period_duration]
            for staff in Staff:
                duties = [self.get_duty(quota_icu(shift,dd,staff)) for dd in range(
                    0, day) for shift in Shifts if dd % 7 in days and shift in shifts]
                tally = self.rota.model.NewIntVar(
                    0,
                    self.rota.rota_length,
                    f'tally{day}{shift_to_check}{staff}')
                self.rota.model.AddAbsEquality(
                    tally,
                    sum(duties))
                target = self.rota.model.NewConstant(
                    len(duties)//self.rota.slots_on_rota,
                )

                delta = self.rota.model.NewIntVar(-deviation_hard_limit,
                                                  deviation_hard_limit,
                                                  f'delta{day}{shift_to_check}{staff}')
                delta_abs = self.rota.model.NewIntVar(-deviation_hard_limit,
                                                      deviation_hard_limit,
                                                      f'delta{day}{shift_to_check}{staff}')
                self.rota.model.Add(
                    delta == tally-target).OnlyEnforceIf(enforced)
                self.rota.model.AddAbsEquality(delta_abs, delta)
                self.rota.model.Add(delta_abs <= deviation_soft_limit)
        self.rota.minimize_targets.extend(deviation_soft_limits.values())

    def event_stream(self, solver, event_stream):
        yield from event_stream
        yield {'type':'report',
                'message':"\n\n".join([
                    f"deviation soft limit {self.variables['shift_to_check']} for period {period}: {solver.Value(softlimit)}"
                    for period, softlimit in self.variables['dsl'].items()])
            }
