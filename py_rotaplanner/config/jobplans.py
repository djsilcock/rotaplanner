from calendar import MONDAY,TUESDAY,WEDNESDAY,THURSDAY,FRIDAY,SATURDAY,SUNDAY

def oncall(day,duty):
    return {(day,'ONCALL'):duty,
            (day+1,'am'):'NONCLINICAL',
            (day+2,'pm'):'NONCLINICAL'}
def allday(day,duty):
    return {(day,'am'):duty,(day,'pm'):duty}
def duty24h(day,duty):
    return{**allday(day,duty),**oncall(day,duty)}

class templates:    
    ICUweek={
        **allday(MONDAY,'ICU'),
        **allday(TUESDAY,'ICU'),
        **allday(WEDNESDAY,'ICU'),
        **duty24h(THURSDAY,'ICU')
        }    
    ICUocwkend = {
        **oncall(FRIDAY,'ICU'),
        **oncall(SATURDAY,'ICU'),
    }
    ICUwkend = {
        **allday(FRIDAY,'ICU'),
        **allday(SATURDAY,'ICU'),
        **duty24h(SUNDAY,'ICU'),
    }
    ThSun = duty24h(SUNDAY,'THEATRE')
    ThSat = duty24h(SATURDAY,'THEATRE')
    ICUocMon = oncall(MONDAY,'ICU')
    ICUocTue = oncall(TUESDAY,'ICU')
    ICUocWed = oncall(WEDNESDAY,'ICU')
    ThocMon =  oncall(MONDAY,'THEATRE')
    ThocTue = oncall(TUESDAY,'THEATRE')
    ThocWed = oncall(WEDNESDAY,'THEATRE')
    ThocThu = oncall(THURSDAY,'THEATRE')
    ThocFri = oncall(FRIDAY,'THEATRE')
    JPamMon = {(MONDAY, 'am'):'JOBPLANNED'}
    JPamTue = {(TUESDAY, 'am'):'JOBPLANNED'}
    JPamWed = {(WEDNESDAY, 'am'):'JOBPLANNED'}
    JPamThu = {(THURSDAY, 'am'):'JOBPLANNED'}
    JPamFri = {(FRIDAY, 'am'):'JOBPLANNED'}
    JPpmMon = {(MONDAY, 'pm'):'JOBPLANNED'}
    JPpmTue = {(TUESDAY, 'pm'):'JOBPLANNED'}
    JPpmWed = {(WEDNESDAY, 'pm'):'JOBPLANNED'}
    JPpmThu = {(THURSDAY, 'pm'):'JOBPLANNED'}
    JPpmFri = {(FRIDAY, 'pm'):'JOBPLANNED'}

    Ooh = {(MONDAY, 'oncall'):'OOH',
    (TUESDAY, 'oncall'):'OOH',
    (WEDNESDAY, 'oncall'):'OOH',
    (THURSDAY, 'oncall'):'OOH',
    (FRIDAY, 'oncall'):'OOH',
    (SATURDAY,'am'):'OOH',
    (SATURDAY,'pm'):'OOH',
    (SATURDAY, 'oncall'):'OOH',
    (SUNDAY,'am'):'OOH',
    (SUNDAY,'pm'):'OOH',
    (SUNDAY, 'oncall'):'OOH'}

    NJPamMon = {(MONDAY, 'am'):'NOTJOBPLANNED'}
    NJPamTue = {(TUESDAY, 'am'):'NOTJOBPLANNED'}
    NJPamWed = {(WEDNESDAY, 'am'):'NOTJOBPLANNED'}
    NJPamThu = {(THURSDAY, 'am'):'NOTJOBPLANNED'}
    NJPamFri = {(FRIDAY, 'am'):'NOTJOBPLANNED'}
    NJPpmMon = {(MONDAY, 'pm'):'NOTJOBPLANNED'}
    NJPpmTue = {(TUESDAY, 'pm'):'NOTJOBPLANNED'}
    NJPpmWed = {(WEDNESDAY, 'pm'):'NOTJOBPLANNED'}
    NJPpmThu = {(THURSDAY, 'pm'):'NOTJOBPLANNED'}
    NJPpmFri = {(FRIDAY, 'pm'):'NOTJOBPLANNED'}
    

    all_th_daytime = {(day,sess):'JOBPLANNED' for sess in ('am','pm') for day in (MONDAY,TUESDAY,WEDNESDAY,THURSDAY,FRIDAY)}
trainee_default=[templates.Ooh,templates.all_th_daytime]
jobplans = {
    'Chohan S': [templates.Ooh,
        templates.ICUocMon, templates.ICUocWed,
        templates.ICUweek, templates.ICUwkend, templates.ICUocwkend,
        templates.JPamMon, templates.JPpmMon,
        templates.NJPamTue, templates.NJPpmTue,
        templates.JPamWed, templates.JPpmWed,
        templates.NJPamThu, templates.NJPpmThu,
        templates.NJPamFri, templates.NJPpmFri],
    'Ley S': [templates.Ooh,
        templates.ICUocWed,
        templates.ICUweek, templates.ICUwkend, templates.ICUocwkend,
        templates.NJPamMon, templates.NJPpmMon,
        templates.JPamTue, templates.NJPpmTue,
        templates.JPamWed, templates.JPpmWed,
        templates.NJPamThu, templates.NJPpmThu,
        templates.NJPamFri, templates.NJPpmFri],
    'Marshall S': [templates.Ooh,
        templates.ICUocMon, templates.ICUocTue,
        templates.ICUweek, templates.ICUwkend, templates.ICUocwkend,
        templates.NJPamMon, templates.NJPpmMon,
        templates.NJPamTue, templates.NJPpmTue,
        templates.NJPamWed, templates.NJPpmWed,
        templates.JPamThu, templates.JPpmThu,
        templates.JPamFri, templates.JPpmFri],
    'Mackenzie R': [templates.Ooh,
        templates.ICUocMon, templates.ICUocWed,
        templates.ICUweek, templates.ICUwkend, templates.ICUocwkend,
        templates.NJPamMon, templates.NJPpmMon,
        templates.NJPamTue, templates.NJPpmTue,
        templates.NJPamWed, templates.NJPpmWed,
        templates.NJPamThu, templates.NJPpmThu,
        templates.NJPamFri, templates.NJPpmFri],
    'Ruddy J': [templates.Ooh,
        templates.ICUocMon, templates.ICUocTue,
        templates.ICUweek, templates.ICUwkend, templates.ICUocwkend,
        templates.JPamMon, templates.JPpmMon,
        templates.NJPamTue, templates.NJPpmTue,
        templates.JPamWed, templates.JPpmWed,
        templates.NJPamThu, templates.NJPpmThu,
        templates.NJPamFri, templates.NJPpmFri],
    'Silcock D': [templates.Ooh,
        templates.ICUocTue,
        templates.ICUweek, templates.ICUwkend, templates.ICUocwkend,
        templates.NJPamMon, templates.NJPpmMon,
        templates.JPamTue, templates.NJPpmTue,
        templates.NJPamWed, templates.NJPpmWed,
        templates.JPamThu, templates.JPpmThu,
        templates.JPamFri, templates.JPpmFri],
    'Stieblich B': [templates.Ooh,
        templates.ICUocMon, templates.ICUocWed,
        templates.ICUweek, templates.ICUwkend, templates.ICUocwkend,
        templates.JPamMon, templates.JPpmMon,
        templates.JPamTue, templates.NJPpmTue,
        templates.JPamWed, templates.JPpmWed,
        templates.NJPamThu, templates.NJPpmThu,
        templates.JPamFri, templates.JPpmFri],
    'Bell J': [templates.Ooh,
        templates.ThocMon, templates.ThocTue, templates.ThocWed, templates.ThocThu,
        templates.ThocFri, templates.ThSat, templates.ThSun,
        templates.JPamMon, templates.JPpmMon,
        templates.NJPamMon, templates.NJPpmMon,
        templates.JPamTue, templates.JPpmTue,
        templates.NJPamTue, templates.NJPpmTue,
        templates.JPamWed, templates.JPpmWed,
        templates.NJPamWed, templates.NJPpmWed,
        templates.JPamThu, templates.JPpmThu,
        templates.NJPamThu, templates.NJPpmThu,
        templates.JPamFri, templates.JPpmFri,
        templates.NJPamFri, templates.NJPpmFri],
    'Cowan G': [templates.Ooh,
        templates.ThocMon, templates.ThocTue, templates.ThocWed, templates.ThocThu,
        templates.ThocFri, templates.ThSat, templates.ThSun,
        templates.JPamMon, templates.JPpmMon,
        templates.NJPamMon, templates.NJPpmMon,
        templates.JPamTue, templates.JPpmTue,
        templates.NJPamTue, templates.NJPpmTue,
        templates.JPamWed, templates.JPpmWed,
        templates.NJPamWed, templates.NJPpmWed,
        templates.JPamThu, templates.JPpmThu,
        templates.NJPamThu, templates.NJPpmThu,
        templates.JPamFri, templates.JPpmFri,
        templates.NJPamFri, templates.NJPpmFri],
    'Currie C': [templates.Ooh,
        templates.ThocMon, templates.ThocTue, templates.ThocWed, templates.ThocThu,
        templates.ThocFri, templates.ThSat, templates.ThSun,
        templates.JPamMon, templates.JPpmMon,
        templates.NJPamMon, templates.NJPpmMon,
        templates.JPamTue, templates.JPpmTue,
        templates.NJPamTue, templates.NJPpmTue,
        templates.JPamWed, templates.JPpmWed,
        templates.NJPamWed, templates.NJPpmWed,
        templates.JPamThu, templates.JPpmThu,
        templates.NJPamThu, templates.NJPpmThu,
        templates.JPamFri, templates.JPpmFri,
        templates.NJPamFri, templates.NJPpmFri],
    'Dunn T': [templates.Ooh,
        templates.ThocMon, templates.ThocTue, templates.ThocWed, templates.ThocThu,
        templates.ThocFri, templates.ThSat, templates.ThSun,
        templates.JPamMon, templates.JPpmMon,
        templates.NJPamMon, templates.NJPpmMon,
        templates.JPamTue, templates.JPpmTue,
        templates.NJPamTue, templates.NJPpmTue,
        templates.JPamWed, templates.JPpmWed,
        templates.NJPamWed, templates.NJPpmWed,
        templates.JPamThu, templates.JPpmThu,
        templates.NJPamThu, templates.NJPpmThu,
        templates.JPamFri, templates.JPpmFri,
        templates.NJPamFri, templates.NJPpmFri],
    'Jamil S': [templates.Ooh,
        templates.ThocMon, templates.ThocTue, templates.ThocWed, templates.ThocThu,
        templates.ThocFri, templates.ThSat, templates.ThSun,
        templates.JPamMon, templates.JPpmMon,
        templates.NJPamMon, templates.NJPpmMon,
        templates.JPamTue, templates.JPpmTue,
        templates.NJPamTue, templates.NJPpmTue,
        templates.JPamWed, templates.JPpmWed,
        templates.NJPamWed, templates.NJPpmWed,
        templates.JPamThu, templates.JPpmThu,
        templates.NJPamThu, templates.NJPpmThu,
        templates.JPamFri, templates.JPpmFri,
        templates.NJPamFri, templates.NJPpmFri],
    'McIntyre C': [templates.Ooh,
        templates.ThocMon, templates.ThocTue, templates.ThocWed, templates.ThocThu,
        templates.ThocFri, templates.ThSat, templates.ThSun,
        templates.JPamMon, templates.JPpmMon,
        templates.NJPamMon, templates.NJPpmMon,
        templates.JPamTue, templates.JPpmTue,
        templates.NJPamTue, templates.NJPpmTue,
        templates.JPamWed, templates.JPpmWed,
        templates.NJPamWed, templates.NJPpmWed,
        templates.JPamThu, templates.JPpmThu,
        templates.NJPamThu, templates.NJPpmThu,
        templates.JPamFri, templates.JPpmFri,
        templates.NJPamFri, templates.NJPpmFri],
    'Taljard F': [templates.Ooh,
        templates.ThocMon, templates.ThocTue, templates.ThocWed, templates.ThocThu,
        templates.ThocFri, templates.ThSat, templates.ThSun,
        templates.JPamMon, templates.JPpmMon,
        templates.NJPamMon, templates.NJPpmMon,
        templates.JPamTue, templates.JPpmTue,
        templates.NJPamTue, templates.NJPpmTue,
        templates.JPamWed, templates.JPpmWed,
        templates.NJPamWed, templates.NJPpmWed,
        templates.JPamThu, templates.JPpmThu,
        templates.NJPamThu, templates.NJPpmThu,
        templates.JPamFri, templates.JPpmFri,
        templates.NJPamFri, templates.NJPpmFri],
    'Vass C': [templates.Ooh,
        templates.ThocMon, templates.ThocTue, templates.ThocWed, templates.ThocThu,
        templates.ThocFri, templates.ThSat, templates.ThSun,
        templates.JPamMon, templates.JPpmMon,
        templates.NJPamMon, templates.NJPpmMon,
        templates.JPamTue, templates.JPpmTue,
        templates.NJPamTue, templates.NJPpmTue,
        templates.JPamWed, templates.JPpmWed,
        templates.NJPamWed, templates.NJPpmWed,
        templates.JPamThu, templates.JPpmThu,
        templates.NJPamThu, templates.NJPpmThu,
        templates.JPamFri, templates.JPpmFri,
        templates.NJPamFri, templates.NJPpmFri]
}