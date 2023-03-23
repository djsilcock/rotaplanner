from enum import StrEnum

class DutyBasis(StrEnum):
    "duty basis"
    DCC = 'DCC'
    FLEX = 'FLEX'
    LOCUM = 'LOCUM'
    TIMESHIFT = 'TIMESHIFT'
    DUTYCHANGE = 'DUTYCHANGE'


class RotationType(StrEnum):
    "rotation types (every week, nth week of month etc)"
    EV = 'EV'
    XINY = 'XINY'
    XINMONTH = 'XINMONTH'

