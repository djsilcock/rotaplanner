from dataclasses import field, dataclass
import datetime


@dataclass
class Location:
    id: str
    name: str


@dataclass
class Staff:
    id: str
    name: str


@dataclass
class AssignmentFlags:
    id: str
    name: str


@dataclass
class ActivityTag:
    id: str
    name: str


@dataclass
class StaffAssignment:
    id: int
    staff: Staff
    timeslot: "TimeSlot"
    flags: list[AssignmentFlags]


@dataclass
class TimeSlot:
    id: int
    activity: "Activity"
    start: datetime.datetime
    finish: datetime.datetime
    assignments: list[StaffAssignment] = field(default_factory=list)


@dataclass
class Activity:
    id: str
    name: str
    type: str
    template_id: str | None
    location: Location | None
    timeslots: list[TimeSlot] = field(default_factory=list)
    tags: list[ActivityTag] = field(default_factory=list)

    @property
    def activity_start(self) -> datetime.datetime:
        return min(t.start for t in self.timeslots)

    @property
    def activity_finish(self) -> datetime.datetime:
        return max(t.finish for t in self.timeslots)

    @property
    def assignments(self) -> list[StaffAssignment]:
        return [assn for timeslot in self.timeslots for assn in timeslot.assignments]

    requirements: dict = field(default_factory=dict)


@dataclass
class DateRange:
    start: datetime.date
    end: datetime.date
