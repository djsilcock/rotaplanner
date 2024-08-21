import datetime
from pydantic import BaseModel,Field
from enum import StrEnum
from typing import cast,Annotated,Literal


from typing import Union



class RuleType(StrEnum):
    "Date rule types"
    DAILY='daily'
    WEEKLY='weekly'
    MONTHLY='day-in-month'
    WEEK_IN_MONTH='week-in-month'
    DATE_RANGE='date-range'
    DATE_TAGS='date-tag'
    GROUP='group'


class GroupType(StrEnum):
    "group types"
    AND='and'
    OR='or'
    NOT='not'

class RuleBase(BaseModel):
    def matches(self,match_date:datetime.date)->bool:
        raise NotImplementedError

class RuleGroup(RuleBase):
    "group of rules"
    rule_type:Literal[RuleType.GROUP]=RuleType.GROUP
    group_type:GroupType
    members:list['Rule']=Field(default_factory=list)
    def matches(self,match_date:datetime.date)->bool:
        members=cast(list,self.members)
        match self.group_type:
            case GroupType.AND:
                return all(rule.matches(match_date) for rule in members)
            case GroupType.OR:
                return any(rule.matches(match_date) for rule in members)
            case GroupType.NOT:
                return not any(rule.matches(match_date)for rule in members)

class DailyRule(RuleBase):
    rule_type:Literal[RuleType.DAILY]=RuleType.DAILY
    day_interval:int
    anchor_date:datetime.date
    def matches(self,match_date:datetime.date):
        return (match_date-self.anchor_date).days%self.day_interval==0

class WeeklyRule(RuleBase):
    "every nth week"
    rule_type:Literal[RuleType.WEEKLY]=RuleType.WEEKLY
    week_interval:int
    anchor_date:datetime.date
    def matches(self,match_date:datetime.date):
        return (match_date-self.anchor_date).days%(7*self.week_interval)==0

class DayOfMonthRule(RuleBase):
    "nth day of every month"
    rule_type:Literal[RuleType.MONTHLY]=RuleType.MONTHLY
    month_interval:int
    anchor_date:datetime.date
    def matches(self,match_date:datetime.date):
        if self.anchor_date.day!=match_date.day:
            return False
        return ((self.anchor_date.year*12+self.anchor_date.month)-(match_date.year*12+match_date.month))%self.month_interval==0
    

class WeekInMonthRule(RuleBase):
    "the nth week of every mth month"
    rule_type:Literal[RuleType.WEEK_IN_MONTH]=RuleType.WEEK_IN_MONTH
    month_interval:int
    anchor_date:datetime.date
    def matches(self,match_date:datetime.date):
        if match_date.weekday()!=self.anchor_date.weekday():
            return False
        if match_date.day//7!=self.anchor_date.day//7:
            return False
        return ((self.anchor_date.year*12+self.anchor_date.month)-(match_date.year*12+match_date.month))%self.month_interval==0


class DateType(StrEnum):
    INCLUSIVE='incl'
    EXCLUSIVE='excl'

class DateRangeRule(RuleBase):
    "date within given range"
    rule_type:Literal[RuleType.DATE_RANGE]=RuleType.DATE_RANGE
    start_date:datetime.date
    finish_date:datetime.date
    range_type:DateType
    def matches(self,match_date:datetime.date):
        if self.range_type==DateType.INCLUSIVE:
            return self.start_date<=match_date<=self.finish_date
        return not self.start_date<=match_date<=self.finish_date


class DateTagsRule(RuleBase):
    "day is tagged eg as a PH"
    rule_type:Literal[RuleType.DATE_TAGS]=RuleType.DATE_TAGS
    label:str
    date_type:DateType

Rule=Annotated[
        Union[RuleGroup,DailyRule,WeeklyRule,DayOfMonthRule,WeekInMonthRule,DateRangeRule,DateTagsRule,RuleGroup],
        Field(discriminator='rule_type')]
