import datetime
from enum import StrEnum
import uuid


from typing import Sequence, Annotated, Literal
from pydantic import BaseModel, model_validator, Field


class GroupType(StrEnum):
    "group types"

    AND = "and"
    OR = "or"
    NOT = "not"


class RuleRoot(BaseModel):
    id: uuid.UUID
    type: str
    rules: list["Rule"]
    groups: list["RuleGroup"]

    def matches(self, match_date: datetime.date) -> bool:
        members = [*self.rules, *self.groups]
        match self.group_type:
            case GroupType.AND:
                return all(rule.matches(match_date) for rule in members)
            case GroupType.OR:
                return any(rule.matches(match_date) for rule in members)
            case GroupType.NOT:
                return not any(rule.matches(match_date) for rule in members)


class RuleType(StrEnum):
    "Date rule types"

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    WEEK_IN_MONTH = "week-in-month"
    DATE_RANGE = "date-range"
    DATE_TAGS = "date-tag"
    GROUP = "group"


class DateType(StrEnum):
    INCLUSIVE = "incl"
    EXCLUSIVE = "excl"


class DateTag(BaseModel):
    id: uuid.UUID
    name: str


class RuleBase(BaseModel):
    start_date: datetime.date
    finish_date: datetime.date | None
    anchor_date: datetime.date | None  # None implies use system epoch

    def matches(self, d: datetime.date, **kwargs):
        if self.finish_date is not None:
            if d > self.finish_date:
                return False
        if d < self.start_date:
            return False
        return True


class DailyRule(RuleBase):
    rule_type: Literal["daily"] = "daily"
    cycle_length: int

    def matches(self, d, *, default_anchor: datetime.date, **kwargs):
        if not super().matches(d, **kwargs):
            return False
        return (d - default_anchor).days % self.cycle_length == 0


def validate_all_in_range(
    seq: Sequence, minimum: int, maximum: int, error_message: str
):
    for item in seq:
        if item < minimum or item > maximum:
            raise ValueError(error_message.format(item=item, max=maximum, min=minimum))


class WeekInMonthRule(RuleBase):
    rule_type: Literal["week-in-month"] = "week-in-month"
    weekdays: set[int]
    week_numbers: set[int]
    months: set[int]

    @model_validator(mode="after")
    def validate(self):
        if len(self.weekdays) == 0:
            raise ValueError("Must be at least one weekday selected")
        if len(self.months) == 0:
            raise ValueError("Must be at least one month selected")
        validate_all_in_range(
            self.weekdays,
            0,
            6,
            "weekdays must be an integer between 0 and 6: not {item}",
        )
        validate_all_in_range(self.months, 1, 12, "{item} is not a valid month number")

    def matches(self, d: datetime.date, **kwargs):
        if not super().matches(d):
            return False
        if d.weekday() not in self.weekdays:
            return False
        week_in_month = d.day // 7 + 1
        return week_in_month in self.week_numbers


class WeeklyRule(RuleBase):
    rule_type: Literal["weekly"] = "weekly"
    cycle_length: int
    weekdays: set[int]
    week_numbers: set[int]

    @model_validator(mode="after")
    def validate(self):
        if len(self.weekdays) == 0:
            raise ValueError("Must be at least one weekday selected")
        validate_all_in_range(
            self.weekdays,
            0,
            6,
            "weekdays must be an integer between 0 and 6: not {item}",
        )
        validate_all_in_range(
            self.week_numbers, 1, self.cycle_length, "week {item}/{max} is not valid"
        )

    def matches(self, d: datetime.date, *, default_anchor: datetime.date, **kwargs):
        if not super().matches(d):
            return False
        anchor = self.anchor_date or default_anchor
        if d.weekday() not in self.weekdays:
            return False
        week_in_cycle = ((d - anchor).days % (7 * self.cycle_length)) // 7 + 1
        return week_in_cycle in self.week_numbers


class DayInMonthRule(RuleBase):
    rule_type: Literal["day-in-month"] = "day-in-month"
    months: set[int]
    days: set[int]

    @model_validator(mode="after")
    def validate(self):
        if len(self.days) == 0:
            raise ValueError("Must be at least one day selected")
        if len(self.months) == 0:
            raise ValueError("Must be at least one month selected")
        validate_all_in_range(
            self.days, 1, 31, "weekdays must be an integer between 1 and 31: not {item}"
        )
        validate_all_in_range(self.months, 1, 12, "{item} is not a valid month number")

    def matches(self, d: datetime.date, **kwargs):
        if not super().matches(d, **kwargs):
            return False
        if d.day not in self.days:
            return False
        if d.month not in self.months:
            return False
        return True


class DateTagRule(RuleBase):
    rule_type: Literal["date-tag"] = "date-tag"
    type: DateType
    tag: DateTag

    def matches(self, d, *, tags, **kwargs):
        if not super().matches(d, **kwargs):
            return False
        has_tag = d in tags.get(self.tag.id, [])
        if self.type == DateType.INCLUSIVE and has_tag:
            return True
        if self.type == DateType.EXCLUSIVE and not has_tag:
            return True
        return False


Rule = Annotated[
    DailyRule | WeeklyRule | DayInMonthRule | WeekInMonthRule | DateTagRule,
    Field(discriminator="rule_type"),
]


class RuleGroup(BaseModel):
    group_type: GroupType
    groups: list["RuleGroup"]
    rules: list[Rule]

    def matches(self, d: datetime.date, **kwargs):
        if self.group_type == GroupType.AND:
            return all(g.matches(d, **kwargs) for g in self.groups) and all(
                r.matches(d, **kwargs) for r in self.rules
            )
        if self.group_type == GroupType.OR:
            return any(g.matches(d, **kwargs) for g in self.groups) or any(
                r.matches(d, **kwargs) for r in self.rules
            )
        if self.group_type == GroupType.NOT:
            if any(g.matches(d, **kwargs) for g in self.groups):
                return False
            if any(r.matches(d, **kwargs) for r in self.rules):
                return False
            return True


class Schedule(BaseModel):
    start_time: datetime.timedelta
    finish_time: datetime.timedelta
    matching_days: RuleGroup
