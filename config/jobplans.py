from calendar import MONDAY,TUESDAY,WEDNESDAY,THURSDAY,FRIDAY,SATURDAY,SUNDAY

class templates:
    ICUweek = [
        ('icu', MONDAY, 'am'),
        ('icu', MONDAY, 'pm'),
        ('icu', TUESDAY, 'am'),
        ('icu', TUESDAY, 'pm'),
        ('icu', WEDNESDAY, 'am'),
        ('icu', WEDNESDAY, 'pm'),
        ('icu', THURSDAY, 'am'),
        ('icu', THURSDAY, 'pm'),
        ('icu', THURSDAY, 'oncall')
    ]
    ICUocwkend = [
        ('icu', FRIDAY, 'oncall'),
        ('icu', SATURDAY, 'oncall')
    ]
    ICUwkend = [
        ('icu', FRIDAY, 'am'),
        ('icu', FRIDAY, 'pm'),
        ('icu', SATURDAY, 'am'),
        ('icu', SATURDAY, 'pm'),
        ('icu', SUNDAY, 'am'),
        ('icu', SUNDAY, 'pm'),
        ('icu', SUNDAY, 'oncall')
    ]
    ThSun = [
        ('theatre', SUNDAY, 'am'),
        ('theatre', SUNDAY, 'pm'),
        ('theatre', SUNDAY, 'oncall')
    ]
    ThSat = [
        ('theatre', SATURDAY, 'am'),
        ('theatre', SATURDAY, 'pm'),
        ('theatre', SATURDAY, 'oncall')
    ]
    ICUocMon = [('icu', MONDAY, 'oncall')]
    ICUocTue = [('icu', TUESDAY, 'oncall')]
    ICUocWed = [('icu', WEDNESDAY, 'oncall')]
    ThocMon = [('theatre', MONDAY, 'oncall')]
    ThocTue = [('theatre', TUESDAY, 'oncall')]
    ThocWed = [('theatre', WEDNESDAY, 'oncall')]
    ThocThu = [('theatre', THURSDAY, 'oncall')]
    ThocFri = [('theatre', FRIDAY, 'oncall')]
    ThamMon = [(('theatre', 'timeback'), MONDAY, 'am')]
    ThamTue = [(('theatre', 'timeback'), TUESDAY, 'am')]
    ThamWed = [(('theatre', 'timeback'), WEDNESDAY, 'am')]
    ThamThu = [(('theatre', 'timeback'), THURSDAY, 'am')]
    ThamFri = [(('theatre', 'timeback'), FRIDAY, 'am')]
    ThpmMon = [(('theatre', 'timeback'), MONDAY, 'pm')]
    ThpmTue = [(('theatre', 'timeback'), TUESDAY, 'pm')]
    ThpmWed = [(('theatre', 'timeback'), WEDNESDAY, 'pm')]
    ThpmThu = [(('theatre', 'timeback'), THURSDAY, 'pm')]
    ThpmFri = [(('theatre', 'timeback'), FRIDAY, 'pm')]

    NCocMon = [('nonclinical', MONDAY, 'oncall')]
    NCocTue = [('nonclinical', TUESDAY, 'oncall')]
    NCocWed = [('nonclinical', WEDNESDAY, 'oncall')]
    NCocThu = [('nonclinical', THURSDAY, 'oncall')]
    NCocFri = [('nonclinical', FRIDAY, 'oncall')]
    NCocSat = [('nonclinical', SATURDAY, 'oncall')]
    NCocSun = [('nonclinical', SUNDAY, 'oncall')]
    NCamMon = [('nonclinical', MONDAY, 'am')]
    NCamTue = [('nonclinical', TUESDAY, 'am')]
    NCamWed = [('nonclinical', WEDNESDAY, 'am')]
    NCamThu = [('nonclinical', THURSDAY, 'am')]
    NCamFri = [('nonclinical', FRIDAY, 'am')]
    NCamSat = [('nonclinical', SATURDAY, 'am')]
    NCamSun = [('nonclinical', SUNDAY, 'am')]
    NCpmMon = [('nonclinical', MONDAY, 'pm')]
    NCpmTue = [('nonclinical', TUESDAY, 'pm')]
    NCpmWed = [('nonclinical', WEDNESDAY, 'pm')]
    NCpmThu = [('nonclinical', THURSDAY, 'pm')]
    NCpmFri = [('nonclinical', FRIDAY, 'pm')]
    NCpmSat = [('nonclinical', SATURDAY, 'pm')]
    NCpmSun = [('nonclinical', SUNDAY, 'pm')]


all_nc_oncalls = [templates.NCocMon, templates.NCocTue, templates.NCocWed, templates.NCocThu, templates.NCocFri,
                  templates.NCocSat, templates.NCocSun, templates.NCamSat, templates.NCpmSat, templates.NCamSun, templates.NCpmSun]
all_th_daytime = [
        templates.ThamMon, templates.ThpmMon,
        templates.ThamTue, templates.ThpmTue,
        templates.ThamWed, templates.ThpmWed,
        templates.ThamThu, templates.ThpmThu,
        templates.ThamFri, templates.ThpmFri,
]
trainee_default=all_nc_oncalls+all_th_daytime
jobplans = {
    'Chohan S': all_nc_oncalls+[
        templates.ICUocMon, templates.ICUocWed,
        templates.ICUweek, templates.ICUwkend, templates.ICUocwkend,
        templates.ThamMon, templates.ThpmMon,
        templates.NCamTue, templates.NCpmTue,
        templates.ThamWed, templates.ThpmWed,
        templates.NCamThu, templates.NCpmThu,
        templates.NCamFri, templates.NCpmFri],
    'Ley S': all_nc_oncalls+[
        templates.ICUocWed,
        templates.ICUweek, templates.ICUwkend, templates.ICUocwkend,
        templates.NCamMon, templates.NCpmMon,
        templates.ThamTue, templates.NCpmTue,
        templates.ThamWed, templates.ThpmWed,
        templates.NCamThu, templates.NCpmThu,
        templates.NCamFri, templates.NCpmFri],
    'Marshall S': all_nc_oncalls+[
        templates.ICUocMon, templates.ICUocTue,
        templates.ICUweek, templates.ICUwkend, templates.ICUocwkend,
        templates.NCamMon, templates.NCpmMon,
        templates.NCamTue, templates.NCpmTue,
        templates.NCamWed, templates.NCpmWed,
        templates.ThamThu, templates.ThpmThu,
        templates.ThamFri, templates.ThpmFri],
    'Mackenzie R': all_nc_oncalls+[
        templates.ICUocMon, templates.ICUocWed,
        templates.ICUweek, templates.ICUwkend, templates.ICUocwkend,
        templates.NCamMon, templates.NCpmMon,
        templates.NCamTue, templates.NCpmTue,
        templates.NCamWed, templates.NCpmWed,
        templates.NCamThu, templates.NCpmThu,
        templates.NCamFri, templates.NCpmFri],
    'Ruddy J': all_nc_oncalls+[
        templates.ICUocMon, templates.ICUocTue,
        templates.ICUweek, templates.ICUwkend, templates.ICUocwkend,
        templates.ThamMon, templates.ThpmMon,
        templates.NCamTue, templates.NCpmTue,
        templates.ThamWed, templates.ThpmWed,
        templates.NCamThu, templates.NCpmThu,
        templates.NCamFri, templates.NCpmFri],
    'Silcock D': all_nc_oncalls+[
        templates.ICUocTue,
        templates.ICUweek, templates.ICUwkend, templates.ICUocwkend,
        templates.NCamMon, templates.NCpmMon,
        templates.ThamTue, templates.NCpmTue,
        templates.NCamWed, templates.NCpmWed,
        templates.ThamThu, templates.ThpmThu,
        templates.ThamFri, templates.ThpmFri],
    'Stieblich B': all_nc_oncalls+[
        templates.ICUocMon, templates.ICUocWed,
        templates.ICUweek, templates.ICUwkend, templates.ICUocwkend,
        templates.ThamMon, templates.ThpmMon,
        templates.ThamTue, templates.NCpmTue,
        templates.ThamWed, templates.ThpmWed,
        templates.NCamThu, templates.NCpmThu,
        templates.ThamFri, templates.ThpmFri],
    'Bell J': all_nc_oncalls+[
        templates.ThocMon, templates.ThocTue, templates.ThocWed, templates.ThocThu,
        templates.ThocFri, templates.ThSat, templates.ThSun,
        templates.ThamMon, templates.ThpmMon,
        templates.NCamMon, templates.NCpmMon,
        templates.ThamTue, templates.ThpmTue,
        templates.NCamTue, templates.NCpmTue,
        templates.ThamWed, templates.ThpmWed,
        templates.NCamWed, templates.NCpmWed,
        templates.ThamThu, templates.ThpmThu,
        templates.NCamThu, templates.NCpmThu,
        templates.ThamFri, templates.ThpmFri,
        templates.NCamFri, templates.NCpmFri],
    'Cowan G': all_nc_oncalls+[
        templates.ThocMon, templates.ThocTue, templates.ThocWed, templates.ThocThu,
        templates.ThocFri, templates.ThSat, templates.ThSun,
        templates.ThamMon, templates.ThpmMon,
        templates.NCamMon, templates.NCpmMon,
        templates.ThamTue, templates.ThpmTue,
        templates.NCamTue, templates.NCpmTue,
        templates.ThamWed, templates.ThpmWed,
        templates.NCamWed, templates.NCpmWed,
        templates.ThamThu, templates.ThpmThu,
        templates.NCamThu, templates.NCpmThu,
        templates.ThamFri, templates.ThpmFri,
        templates.NCamFri, templates.NCpmFri],
    'Currie C': all_nc_oncalls+[
        templates.ThocMon, templates.ThocTue, templates.ThocWed, templates.ThocThu,
        templates.ThocFri, templates.ThSat, templates.ThSun,
        templates.ThamMon, templates.ThpmMon,
        templates.NCamMon, templates.NCpmMon,
        templates.ThamTue, templates.ThpmTue,
        templates.NCamTue, templates.NCpmTue,
        templates.ThamWed, templates.ThpmWed,
        templates.NCamWed, templates.NCpmWed,
        templates.ThamThu, templates.ThpmThu,
        templates.NCamThu, templates.NCpmThu,
        templates.ThamFri, templates.ThpmFri,
        templates.NCamFri, templates.NCpmFri],
    'Dunn T': all_nc_oncalls+[
        templates.ThocMon, templates.ThocTue, templates.ThocWed, templates.ThocThu,
        templates.ThocFri, templates.ThSat, templates.ThSun,
        templates.ThamMon, templates.ThpmMon,
        templates.NCamMon, templates.NCpmMon,
        templates.ThamTue, templates.ThpmTue,
        templates.NCamTue, templates.NCpmTue,
        templates.ThamWed, templates.ThpmWed,
        templates.NCamWed, templates.NCpmWed,
        templates.ThamThu, templates.ThpmThu,
        templates.NCamThu, templates.NCpmThu,
        templates.ThamFri, templates.ThpmFri,
        templates.NCamFri, templates.NCpmFri],
    'Jamil S': all_nc_oncalls+[
        templates.ThocMon, templates.ThocTue, templates.ThocWed, templates.ThocThu,
        templates.ThocFri, templates.ThSat, templates.ThSun,
        templates.ThamMon, templates.ThpmMon,
        templates.NCamMon, templates.NCpmMon,
        templates.ThamTue, templates.ThpmTue,
        templates.NCamTue, templates.NCpmTue,
        templates.ThamWed, templates.ThpmWed,
        templates.NCamWed, templates.NCpmWed,
        templates.ThamThu, templates.ThpmThu,
        templates.NCamThu, templates.NCpmThu,
        templates.ThamFri, templates.ThpmFri,
        templates.NCamFri, templates.NCpmFri],
    'McIntyre C': all_nc_oncalls+[
        templates.ThocMon, templates.ThocTue, templates.ThocWed, templates.ThocThu,
        templates.ThocFri, templates.ThSat, templates.ThSun,
        templates.ThamMon, templates.ThpmMon,
        templates.NCamMon, templates.NCpmMon,
        templates.ThamTue, templates.ThpmTue,
        templates.NCamTue, templates.NCpmTue,
        templates.ThamWed, templates.ThpmWed,
        templates.NCamWed, templates.NCpmWed,
        templates.ThamThu, templates.ThpmThu,
        templates.NCamThu, templates.NCpmThu,
        templates.ThamFri, templates.ThpmFri,
        templates.NCamFri, templates.NCpmFri],
    'Taljard F': all_nc_oncalls+[
        templates.ThocMon, templates.ThocTue, templates.ThocWed, templates.ThocThu,
        templates.ThocFri, templates.ThSat, templates.ThSun,
        templates.ThamMon, templates.ThpmMon,
        templates.NCamMon, templates.NCpmMon,
        templates.ThamTue, templates.ThpmTue,
        templates.NCamTue, templates.NCpmTue,
        templates.ThamWed, templates.ThpmWed,
        templates.NCamWed, templates.NCpmWed,
        templates.ThamThu, templates.ThpmThu,
        templates.NCamThu, templates.NCpmThu,
        templates.ThamFri, templates.ThpmFri,
        templates.NCamFri, templates.NCpmFri],
    'Vass C': all_nc_oncalls+[
        templates.ThocMon, templates.ThocTue, templates.ThocWed, templates.ThocThu,
        templates.ThocFri, templates.ThSat, templates.ThSun,
        templates.ThamMon, templates.ThpmMon,
        templates.NCamMon, templates.NCpmMon,
        templates.ThamTue, templates.ThpmTue,
        templates.NCamTue, templates.NCpmTue,
        templates.ThamWed, templates.ThpmWed,
        templates.NCamWed, templates.NCpmWed,
        templates.ThamThu, templates.ThpmThu,
        templates.NCamThu, templates.NCpmThu,
        templates.ThamFri, templates.ThpmFri,
        templates.NCamFri, templates.NCpmFri]
}