"various datatypes"
from dataclasses import dataclass, field

@dataclass
class SessionDuty:
    "Session information"
    duty: str|None = None
    flags: set[str]=field(default_factory=set)

    def __str__(self):
        if not self.duty:
            return ""
        representations={
            'locum':'£',
            'locked':'🔒'
        }
        return f'{self.duty} {"".join(representations[f] for f in self.flags)}'
