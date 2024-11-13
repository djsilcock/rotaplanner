import datetime
from enum import StrEnum
from rotaplanner.database import db
from sqlalchemy.orm import Mapped, relationship, mapped_column
from sqlalchemy import ForeignKey


from typing import Union


class RuleType(StrEnum):
    "Date rule types"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "day-in-month"
    WEEK_IN_MONTH = "week-in-month"
    DATE_RANGE = "date-range"
    DATE_TAGS = "date-tag"
    GROUP = "group"


class GroupType(StrEnum):
    "group types"
    AND = "and"
    OR = "or"
    NOT = "not"


class DateType(StrEnum):
    INCLUSIVE = "incl"
    EXCLUSIVE = "excl"


class Rule(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("rule_group.id"))
    rule_type: Mapped[RuleType]
    day_interval: Mapped[int | None]
    week_interval: Mapped[int | None]
    month_interval: Mapped[int | None]
    start_date: Mapped[datetime.date | None]
    finish_date: Mapped[datetime.date | None]
    tag: Mapped[str | None]
    date_type: Mapped[DateType | None]

    def matches(self, match_date: datetime.date):
        match (self.rule_type):
            case RuleType.DAILY:
                return (match_date - self.start_date).days % self.day_interval == 0
            case RuleType.WEEKLY:
                return (match_date - self.start_date).days % (
                    7 * self.week_interval
                ) == 0
            case RuleType.MONTHLY:
                if self.start_date.day != match_date.day:
                    return False
                return (
                    (self.start_date.year * 12 + self.start_date.month)
                    - (match_date.year * 12 + match_date.month)
                ) % self.month_interval == 0
            case RuleType.WEEK_IN_MONTH:
                if match_date.weekday() != self.start_date.weekday():
                    return False
                if match_date.day // 7 != self.start_date.day // 7:
                    return False
                return (
                    (self.start_date.year * 12 + self.start_date.month)
                    - (match_date.year * 12 + match_date.month)
                ) % self.month_interval == 0
            case RuleType.DATE_RANGE:
                if self.range_type == DateType.INCLUSIVE:
                    return self.start_date <= match_date <= self.finish_date
                return not self.start_date <= match_date <= self.finish_date
            case RuleType.DATE_TAGS:
                pass


class RuleGroup(db.Model):
    "group of rules"
    id: Mapped[int] = mapped_column(primary_key=True)
    group_type: Mapped[GroupType]
    rules: Mapped[list[Rule]] = relationship(cascade="all,delete")
    parent_group_id: Mapped[int | None] = mapped_column(ForeignKey("rule_group.id"))
    parent_group: Mapped["RuleGroup | None"] = relationship(remote_side=[id])
    groups: Mapped[list["RuleGroup"]] = relationship(cascade="all,delete")

    def matches(self, match_date: datetime.date) -> bool:
        members = [*self.rules, *self.groups]
        match self.group_type:
            case GroupType.AND:
                return all(rule.matches(match_date) for rule in members)
            case GroupType.OR:
                return any(rule.matches(match_date) for rule in members)
            case GroupType.NOT:
                return not any(rule.matches(match_date) for rule in members)
