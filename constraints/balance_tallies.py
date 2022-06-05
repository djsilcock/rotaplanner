"""contains rules to constrain the model"""
from calendar import THURSDAY, FRIDAY

from enum import Enum, auto


from constants import Shifts, Staff, Duties
from constraints.constraintmanager import BaseConstraint


class Constraint(BaseConstraint):
    """calculate targets"""
    name = "Balance tallies"
    targets = None

    @classmethod
    def definition(cls):
        return ['balance tallies (increases calculation time)']

    def apply_constraint(self):
        class Targets(Enum):
            '''labels for targets'''
            ICU_WEEKDAY = auto()
            ICU_WEEKEND = auto()
            ICU_WD_ONCALL = auto()
            ICU_WE_ONCALL = auto()

        targetkeys = {
            Targets.ICU_WEEKDAY: (Shifts.DAYTIME, lambda d: d % 7 <= THURSDAY),
            Targets.ICU_WEEKEND: (Shifts.DAYTIME, lambda d: d % 7 >= FRIDAY),
            Targets.ICU_WD_ONCALL: (Shifts.ONCALL, lambda d: d % 7 <= THURSDAY),
            Targets.ICU_WE_ONCALL: (Shifts.ONCALL, lambda d: d % 7 >= FRIDAY)}
        num_days = len(list(self.days()))
        tallies = {f"{key}{staff}": self.rota.model.NewIntVar(
            0, num_days, f'tally{key}') for key in targetkeys for staff in Staff}
        deltas = {f"{key}{staff}": self.rota.model.NewIntVar(
            0, num_days, f'delta{key}') for key in targetkeys for staff in Staff}
        targets = {}
        totals = {}
        for key, (shift, dayfilter) in targetkeys.items():
            totals[key] = len(
                [day for day in self.days() if dayfilter(day)])
            targets[key] = totals[key]//self.rota.slots_on_rota
            for staff in Staff:
                self.rota.model.AddAbsEquality(
                    tallies[f"{key}{staff}"],
                    sum(self.rota.get_duty(Duties.QUOTA_ICU, day, shift, staff)
                        for day in self.days()
                        if dayfilter(day)))
                self.rota.model.AddAbsEquality(
                    deltas[f"{key}{staff}"],
                    sum(self.rota.get_duty(Duties.QUOTA_ICU, day, shift, staff)
                        for day in self.days()
                        if dayfilter(day))-targets[key])

        self.rota.minimize_targets.extend(deltas.values())
        self.targets = targets

    def event_stream(self, solver, event_stream):
        yield from event_stream
        yield(
            {'type': 'statistic',
             'objective': solver.BestObjectiveBound()})
        statskeys = {
            'ICU weekdays': (Duties.QUOTA_ICU, Shifts.DAYTIME, lambda d: d % 7 <= THURSDAY),
            'ICU weekend days': (Duties.QUOTA_ICU, Shifts.DAYTIME, lambda d: d % 7 >= FRIDAY),
            'ICU weekday oncall': (Duties.QUOTA_ICU, Shifts.ONCALL, lambda d: d % 7 <= THURSDAY),
            'ICU weekend oncall': (Duties.QUOTA_ICU, Shifts.ONCALL, lambda d: d % 7 >= FRIDAY),
            'Locum weekday oncall': (Duties.LOCUM_ICU, Shifts.ONCALL, lambda d: d % 7 <= THURSDAY),
            'Locum wkend days': (Duties.LOCUM_ICU, Shifts.DAYTIME, lambda d: d % 7 > FRIDAY),
            'Locum wkend oncall': (Duties.LOCUM_ICU, Shifts.ONCALL, lambda d: d % 7 >= FRIDAY)
        }
        for k, (duty, shift, dayfilter) in statskeys.items():
            for staff in Staff:
                yield({
                    'type': 'statistic',
                    'duty': k,

                    'staff': staff.name,
                    'tally': solver.Value(
                        sum(self.rota.get_duty(duty, day, shift, staff) for day in self.days()
                            if dayfilter(day)))})
