"""Contains the constants for duty types"""
from enum import Enum,auto
from calendar import MONDAY,TUESDAY,WEDNESDAY,THURSDAY,FRIDAY

class Shifts(Enum):
    DAYTIME=auto()
    ONCALL=auto()

class Duties(Enum):
    """all the duty types"""
    ICU_COTW = auto()
    ICU_LOCUM_COTW = auto()
    ICU = auto()
    IS_LOCUM=auto()
    THEATRE = auto()
    LEAVE = auto()
    OFF = auto()
    LOCUM_ICU = auto()
    QUOTA_ICU = auto()


Staff = Enum('Staff', 'SANJIV RORY SCOTT BARTEK DAN SAM CHOITI JIM')


jobplans = {
    Staff.SANJIV: {MONDAY, FRIDAY},
    Staff.CHOITI: {TUESDAY, WEDNESDAY},
    Staff.BARTEK: {MONDAY, WEDNESDAY, FRIDAY},
    Staff.SAM: {TUESDAY, WEDNESDAY},
    Staff.DAN: {TUESDAY, THURSDAY, FRIDAY},
    Staff.JIM: {MONDAY, THURSDAY},
    Staff.SCOTT: {THURSDAY, FRIDAY},
    Staff.RORY: {MONDAY, WEDNESDAY, THURSDAY}
}
