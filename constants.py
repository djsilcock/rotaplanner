from enum import IntEnum,IntFlag,auto

class Locations(IntEnum):
    ICU=1
    THEATRE=2
    TIMEBACK=3
    LEAVE=4
    
class Shifts(IntEnum):
    AM=1
    PM=2
    ONCALL=3

class Flags(IntFlag):
    IS_LOCUM=1
    IS_CONFIRMED=2
    LOCUM_CONFIRMED=4

APPLY_CONSTRAINT='apply_constraint'
