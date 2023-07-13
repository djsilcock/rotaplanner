"various datatypes"
from dataclasses import dataclass, field
from enum import StrEnum

class DutyFlag(StrEnum):
    "flags for duties"
    LOCUM='locum'
    LOCKED='locked'

@dataclass
class SessionDuty:
    "Session information"
    duty: str|None = None
    flags: set[DutyFlag]=field(default_factory=set)

    def __str__(self):
        if not self.duty:
            return ""
        representations={
            DutyFlag.LOCUM:'£',
            DutyFlag.LOCKED:'🔒'
        }
        return f'{self.duty} {"".join(representations[f] for f in self.flags)}'
