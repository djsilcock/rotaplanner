import strawberry


@strawberry.input
class TimeSlotInput:
    activity_id: str
    start_time: str


@strawberry.input
class RequirementInput:
    requirement_id: strawberry.ID
    attendance: int
    minimum: int
    maximum: int


@strawberry.input
class DailyRecurrenceInput:
    interval: int


@strawberry.input
class WeeklyRecurrenceInput:
    interval: int
    weekday: int


@strawberry.input
class MonthlyRecurrenceInput:
    interval: int
    day_in_month: int


@strawberry.input
class WeekInMonthRecurrenceInput:
    interval: int
    weekday: int
    week_no: int


@strawberry.input(one_of=True)
class RecurrenceGroup:
    all_of: list["RecurrenceRule"]
    any_of: list["RecurrenceRule"]
    none_of: list["RecurrenceRule"]


@strawberry.input(one_of=True)
class RecurrenceRule:
    group: strawberry.Maybe[RecurrenceGroup]
    daily: strawberry.Maybe[DailyRecurrenceInput]
    weekly: strawberry.Maybe[WeeklyRecurrenceInput]
    monthly: strawberry.Maybe[MonthlyRecurrenceInput]
    week_in_month: strawberry.Maybe[WeekInMonthRecurrenceInput]


@strawberry.input
class NewStaffAssignmentInput:
    timeslot: strawberry.Maybe[TimeSlotInput]
    staff: strawberry.Maybe[strawberry.ID | None]
    tags: strawberry.Maybe[list[str]]
    attendance: strawberry.Maybe[int]


@strawberry.input
class ActivityInput:
    id: strawberry.Maybe[strawberry.ID]
    template_id: strawberry.Maybe[strawberry.ID | None]
    activity_start: strawberry.Maybe[str]
    activity_date: strawberry.Maybe[str]
    name: strawberry.Maybe[str]
    location_id: strawberry.Maybe[strawberry.ID]
    recurrence_rules: strawberry.Maybe[RecurrenceGroup]
    requirements: strawberry.Maybe[list[RequirementInput]]
    timeslots: strawberry.Maybe[list[TimeSlotInput]]
