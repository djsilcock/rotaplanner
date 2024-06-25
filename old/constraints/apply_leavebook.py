"""contains rules to constrain the model"""


from enum import Flag, StrEnum
from old.constraint_ctx import BaseConstraintConfig
from constraints.core_duties import leave, icu
from constraints.some_shifts_are_locum import quota_icu, locum_icu
from solver import GenericConfig

LeavebookFlags=Flag('LeavebookFlags',
    'IS_LOCUM LOCUM_STATUS_CONFIRMED DUTY_CONFIRMED')

LeavebookDuties=StrEnum('LeavebookDuties',
    'LEAVE TS NOC ICU THEATRE')


class Constraint(BaseConstraintConfig):
    """Leavebook entry"""

    def setup(self, solver_context):
        super().__init__(solver_context)
        self.leavebook = {}

    async def apply_constraint(self):
        data = []  # TODO: get data from database
        config: GenericConfig = self.ctx[None]
        for item in data:
            self.leavebook[(Staff[item.name], Shifts[item.shift],
                            item.date)] = (item.duty, item.flags)
        for staff in Staff:
            for shift in Shifts:
                for day in self.days():
                    this_duty, duty_flags = self.leavebook.get(
                        (staff, shift, day), (None, LeavebookFlags(0)))

                    is_on_leave = config.dutystore[leave(shift, day, staff)]

                    if this_duty in (LeavebookDuties.LEAVE,LeavebookDuties.NOC):
                        config.model.Add(is_on_leave == 1)
                    else:
                        config.model.Add(is_on_leave == 0)

                    if this_duty == LeavebookDuties.ICU and LeavebookFlags.DUTY_CONFIRMED in duty_flags:
                        config.model.Add(
                            config.dutystore[icu(shift, day, staff)] == 1)
                        if LeavebookFlags.LOCUM_STATUS_CONFIRMED in duty_flags:
                            if LeavebookFlags.IS_LOCUM in duty_flags:
                                config.model.Add(
                                    config.dutystore[locum_icu(shift, day, staff)] == 1)
                            else:
                                config.model.Add(
                                    config.dutystore[quota_icu(shift, day, staff)] == 1)

                    if this_duty == LeavebookDuties.ICU:
                        config.model.AddHint(config.dutystore[
                            icu(shift, day, staff)], 1)
                        if LeavebookFlags.IS_LOCUM in duty_flags:
                            config.model.AddHint(config.dutystore[
                                locum_icu(shift, day, staff)], 1)

    async def enrich_output_cell(self, cell, solver):
        staff = cell['staff']
        shift = cell['shift']
        day = cell['day']
        leavebook_duty,leavebook_flags = self.leavebook.get((staff, shift, day),(None,LeavebookFlags(0)))
        if leavebook_duty in (LeavebookDuties.NOC,LeavebookDuties.LEAVE):
            cell['duty'] = leavebook_duty
        flags=LeavebookFlags.LOCUM_STATUS_CONFIRMED|LeavebookFlags.DUTY_CONFIRMED|LeavebookFlags.IS_LOCUM
        cell['flags']|=flags&leavebook_flags
