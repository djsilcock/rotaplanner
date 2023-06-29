from dataclasses import dataclass, field
from enum import Flag, StrEnum,auto
from typing import Optional
from copy import deepcopy

class DutyFlag(StrEnum):
    locum='locum'
    locked='locked'

@dataclass
class DutyCell:
    duties:dict
    
@dataclass
class SessionDuty:
    "Session information"
    duty: str|None = None
    flags: set[DutyFlag]=field(default_factory=set)

    def __deepcopy__(self, memo):
        return SessionDuty(self.duty, self.flags)

    def __str__(self):
        if not self.duty:
            return ""
        representations={
            DutyFlag.locum:'£',
            DutyFlag.locked:'🔒'
        }
        return f'{self.duty} {"".join(representations[f] for f in self.flags)}'
