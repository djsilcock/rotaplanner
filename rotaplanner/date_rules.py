import datetime
from enum import StrEnum
from rotaplanner.database import db
from sqlalchemy.orm import Mapped, relationship, mapped_column
from sqlalchemy import ForeignKey
import uuid

from .utils import get_instance_fields


from typing import Union, TYPE_CHECKING, ClassVar
from functools import reduce


class GroupType(StrEnum):
    "group types"
    AND = "and"
    OR = "or"
    NOT = "not"


class RuleRoot(db.Model):
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    type: Mapped[str]
    rules: Mapped[list["Rule"]] = relationship(cascade="all,delete")
    groups: Mapped[list["RuleGroup"]] = relationship(
        foreign_keys="RuleGroup.parent_group_id"
    )

    __mapper_args__ = {"polymorphic_identity": "rule_root", "polymorphic_on": "type"}

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
    MONTHLY = "day-in-month"
    WEEK_IN_MONTH = "week-in-month"
    DATE_RANGE = "date-range"
    DATE_TAGS = "date-tag"
    GROUP = "group"


class DateType(StrEnum):
    INCLUSIVE = "incl"
    EXCLUSIVE = "excl"


class DateTag(db.Model):
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    name: Mapped[str]


class Rule(db.Model):
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    group_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("rule_root.id"))
    rule_type: Mapped[RuleType]
    day_interval: Mapped[int | None]
    week_interval: Mapped[int | None]
    month_interval: Mapped[int | None]
    start_date: Mapped[datetime.date | None]
    finish_date: Mapped[datetime.date | None]
    date_tag_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("date_tag.id"))
    tag: Mapped[DateTag | None] = relationship(DateTag)
    date_type: Mapped[DateType | None]

    def matches(self, match_date: datetime.date):
        if self.start_date is not None and self.start_date > match_date:
            return False
        if self.finish_date is not None and self.finish_date < match_date:
            return False
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

    def clone(self):
        fields = get_instance_fields(self)
        fields["id"] = uuid.uuid4()
        del fields["group_id"]
        return Rule(**fields)


class RuleGroup(RuleRoot):

    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("rule_root.id"), primary_key=True)
    group_type: Mapped[GroupType]
    parent_group_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("rule_root.id"))
    parent_group: Mapped[RuleRoot] = relationship(
        back_populates="groups", foreign_keys=[parent_group_id]
    )

    "group of rules"
    __mapper_args__ = {
        "polymorphic_identity": "rule_group",
        "inherit_condition": id == RuleRoot.id,
    }

    def finish_date(self):
        finish_dates = list(filter(None, (r.finish_date for r in self.rules)))
        finish_dates.extend(filter(None, (g.finish_date() for g in self.groups)))
        if len(finish_dates) == 0:
            return None
        return max(finish_dates)

    def clone(self):
        fields = get_instance_fields(self)
        fields["id"] = uuid.uuid4()
        del fields["parent_group_id"]
        fields["groups"] = [group.clone() for group in self.groups]
        fields["rules"] = [rule.clone() for rule in self.rules]
        return RuleGroup(**fields)
