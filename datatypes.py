from dataclasses import dataclass
from typing import Optional
from copy import deepcopy

@dataclass
class SessionDuty:
    "Session information"
    duty: Optional[str] = None
    locum: Optional[bool] = None
    locked: bool = False

    def __deepcopy__(self, memo):
        return SessionDuty(self.duty, self.locum, self.locked)

    def __str__(self):
        if not self.duty:
            return ""
        return f'{self.duty} {"£" if self.locum else ""} {"🔒" if self.locked else ""}'


@dataclass
class DutyCell:
    "Duties for given person on a given day"

    duties: dict[str, SessionDuty]
    def __str__(self):
        return '\n'.join(f'{k}:{v}' for k, v in self.duties.items() if str(v))

    def __deepcopy__(self, memo):
        return DutyCell(duties={k: deepcopy(v) for k, v in self.duties.items()})