"""contains rules to constrain the model"""
from calendar import MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY
from datetime import date

from constraints.core_duties import icu
from datatypes import DutyCell
from signals import signal


def locum_icu(shift: str, day: date, staff: str):
    "Locum ICU shift"
    return ('LOCUM_ICU', day, shift, staff)

def quota_icu(shift: str, day, staff:str):
    "Quota ICU shift"
    return ('QUOTA_ICU', day, shift, staff)

def locum(shift:str,day:date):
    "Is shift a locum"
    assert isinstance(shift,str)
    assert isinstance(day,date)
    weekday=day.weekday()
    isoweek=day.isocalendar()[0:2]
    if weekday in [MONDAY,TUESDAY,WEDNESDAY,THURSDAY]:
        if shift in ['am','pm']:
            return ('COTW_LOCUM',isoweek)
        return ('WEEKDAY_ONCALL_LOCUM',day)
    if weekday in [FRIDAY,SATURDAY,SUNDAY] and shift in ['am','pm']:
        return ('WEEKEND_LOCUM',isoweek)
    if weekday == SUNDAY and shift=='oncall':
        return ('WEEKEND_LOCUM',isoweek)
    if weekday in [FRIDAY,SATURDAY] and shift =='oncall':
        return ('WEEKEND_ONCALL_LOCUM',isoweek)
    raise ValueError('should not be here')

@signal('apply_constraint').connect
def some_shifts_are_locum(ctx):
    for day in ctx.days:
        for shift in ctx.shifts:
            for staff in ctx.staff:
                shift_is_locum = ctx.dutystore[locum(shift, day)]
                locum_session = ctx.dutystore[locum_icu(shift,day,staff)]
                quota_session = ctx.dutystore[quota_icu(shift,day,staff)]
                is_icu=ctx.dutystore[icu(shift,day,staff)]
                #self.model.AddImplication(locum_session,shift_is_locum)
                #self.model.AddImplication(locum_session,is_icu)
                #self.model.AddImplication(quota_session,shift_is_locum.Not())
                #self.model.AddImplication(quota_session,is_icu)
                #self.model.AddImplication(locum_session,quota_session.Not())
                #self.model.AddImplication(quota_session,locum_session.Not())
                ctx.model.AddAllowedAssignments([is_icu,locum_session,quota_session],[
                    (True,True,False),(True,False,True),(False,False,False)
                ])
                ctx.model.AddAllowedAssignments(
                    [shift_is_locum,locum_session,quota_session],
                    [(True,True,False),
                    (True,False,False),
                    (False,False,True),
                    (False,False,False),
                    ]
                )
                #self.model.AddBoolOr(locum_session,quota_session).OnlyEnforceIf(is_icu)
                #self.model.Add((locum_session+quota_session)==is_icu)
                #self.model.Add(sum([locum_session,quota_session])==1).OnlyEnforceIf(is_icu)

@signal('build_output').connect
def build_output(ctx, outputdict, solver):
    "locum duties output"
    print('some_are_locum builder')
    for key,value in ctx.dutystore.items():
        match key:
            case ('LOCUM_ICU',day,shift,staff):
                if solver.Value(value):
                    cell=outputdict[(staff,day)]
                    assert isinstance(cell,DutyCell)
                    cell.duties[shift].locum=True
            case ('QUOTA_ICU',day,shift,staff):
                if solver.Value(value):
                    cell=outputdict[(staff,day)]
                    assert isinstance(cell,DutyCell)
                    cell.duties[shift].locum=False
            

def process_output(self, solver, pairs):
    locum_shifts=0
    quota_shifts=0
    icu_shifts=0
    for ((staff,shift,day),value) in pairs:
        if solver.Value(self.get_duty(icu(shift,day,staff))):
            icu_shifts+=1
        if solver.Value(self.get_duty(locum_icu(shift,day,staff))):
            locum_shifts+=1
            yield((staff,shift,day),'LOCUM_ICU')
        else:
            yield((staff,shift,day),value)
            quota_shifts+=1
    print (f'locum shifts:{locum_shifts}, quota shifts:{quota_shifts}, total:{icu_shifts}')

