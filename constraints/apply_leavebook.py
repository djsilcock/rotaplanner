"""contains rules to constrain the model"""


from constants import Shifts, Staff, Duties
from constraints.constraintmanager import BaseConstraint


class Constraint(BaseConstraint):
    """Leavebook entry"""

    def apply_constraint(self):
        leavebook = self.kwargs.get('leavebook')
        for staff in Staff:
            for shift in Shifts:
                for day in self.days():
                    if leavebook.get((staff, shift, day), None) == Duties.LEAVE:
                        self.rota.model.Add(self.rota.get_duty(
                            Duties.LEAVE, day, shift, staff) == 1)
                    else:
                        self.rota.model.Add(self.rota.get_duty(
                            Duties.LEAVE, day, shift, staff) == 0)
                    if leavebook.get((staff, shift, day), None) == Duties.ICU:
                        self.rota.model.Add(self.rota.get_duty(
                            Duties.ICU, day, shift, staff) == 1)

    def event_stream(self, solver, event_stream):
        leavebook = self.kwargs.get('leavebook')
        for event in event_stream:
            if event['type'] == 'duty' and event['dutyType'] == 'ICU':
                staff = Staff[event['name']]
                shift = Shifts[event['shift']]
                day = event['day']
                newevent = event.copy()
                newevent.update(
                    {'dutyType': 'DEFINITE_ICU'
                        if leavebook.get((staff, shift, day), '') == Duties.ICU
                        else 'ICU'})
                yield newevent
            else:
                yield event

        for (staff, shift, day) in leavebook:
            if leavebook[(staff, shift, day)] == Duties.LEAVE:
                yield {
                    'type': 'leave',
                    'shift': shift.name,
                    'day': day,
                    'staff': staff.name
                }
