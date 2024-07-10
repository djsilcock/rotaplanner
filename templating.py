
import datetime
from dataclasses import dataclass,replace,field,is_dataclass,fields
from enum import StrEnum,IntEnum,auto
from typing import Literal,Self,Any,overload,cast,Generic,TypeVar

from ortools.sat.python import cp_model

Intervals=StrEnum('Intervals','week day month')

class RuleType(IntEnum):
    "Date rule types"
    DAILY=auto()
    WEEKLY=auto()
    MONTHLY=auto()
    WEEK_IN_MONTH=auto()
    DATE_RANGE=auto()
    DATE_TAGS=auto()
    GROUP=auto()

GroupType=IntEnum('GroupType','AND OR NOT')


demand_templates:dict[str,'DemandTemplate']={}

  
class Rule:
    rule_type:RuleType
    @classmethod
    def from_rule(cls,other,parent=None):
        my_fields=[f.name for f in fields(cls)] if is_dataclass(cls) else []
        if isinstance(other,cls):
            assert is_dataclass(other) and not isinstance(other,type)
            return cast(Rule,replace(other,**{f:getattr(other,f) for f in my_fields if hasattr(other,f)}))
        return
    def matches(self,match_date:datetime.date):
        raise NotImplementedError
            
@dataclass
class DailyRule(Rule):
    "every nth day"
    day_interval:int=1
    anchor_date:datetime.date=datetime.date.today()
    rule_type:RuleType=RuleType.DAILY

    def matches(self,match_date:datetime.date):
        return (match_date-self.anchor_date).days%self.day_interval==0

@dataclass
class WeeklyRule(Rule):
    "every nth week"
    week_interval:int=1
    anchor_date:datetime.date=datetime.date.today()
    rule_type:RuleType=RuleType.WEEKLY
    
    def matches(self,match_date:datetime.date):
        return (match_date-self.anchor_date).days%(7*self.week_interval)==0

@dataclass
class MonthlyRule(Rule):
    "every nth month"
    month_interval:int=1
    anchor_date:datetime.date=datetime.date.today()
    rule_type:RuleType=RuleType.MONTHLY
    def matches(self,match_date:datetime.date):
        if self.anchor_date.day!=match_date.day:
            return False
        return ((self.anchor_date.year*12+self.anchor_date.month)-(match_date.year*12+match_date.month))%self.month_interval==0
    
@dataclass
class WeekInMonthRule(Rule):
    "the nth week of every mth month"
    month_interval:int=1
    anchor_date:datetime.date=datetime.date.today()
    rule_type:RuleType=RuleType.WEEK_IN_MONTH
    def matches(self,match_date:datetime.date):
        if match_date.weekday()!=self.anchor_date.weekday():
            return False
        if match_date.day//7!=self.anchor_date.day//7:
            return False
        return ((self.anchor_date.year*12+self.anchor_date.month)-(match_date.year*12+match_date.month))%self.month_interval==0


class DateType(IntEnum):
    INCLUSIVE=auto()
    EXCLUSIVE=auto()

@dataclass
class DateRangeRule(Rule):
    start_date:datetime.date=datetime.date(2000,1,1)
    finish_date:datetime.date=datetime.date(2199,12,31)
    range_type:DateType=DateType.INCLUSIVE
    rule_type:RuleType=RuleType.DATE_RANGE
    def matches(self,match_date:datetime.date):
        if self.range_type==DateType.INCLUSIVE:
            return self.start_date<=match_date<=self.finish_date
        return not (self.start_date<=match_date<=self.finish_date)

@dataclass
class DateTagsRule(Rule):
    label:str="PH"
    date_type:DateType=DateType.EXCLUSIVE
    rule_type:RuleType=RuleType.DATE_TAGS

@dataclass
class RuleGroup(Rule):
    "Templating rule group"
    group_type:GroupType=GroupType.AND
    children:list[Rule]=field(default_factory=list)
    rule_type:RuleType=RuleType.GROUP
    def matches(self,match_date):
        match self.group_type:
            case GroupType.AND:
                return all(rule.matches(match_date) for rule in self.children)
            case GroupType.OR:
                return any(rule.matches(match_date) for rule in self.children)
            case GroupType.NOT:
                return not any(rule.matches(match_date)for rule in self.children)


rule_types={
    RuleType.DAILY:DailyRule,
    RuleType.WEEKLY:WeeklyRule,
    RuleType.MONTHLY:MonthlyRule,
    RuleType.WEEK_IN_MONTH:WeekInMonthRule,
    RuleType.DATE_RANGE:DateRangeRule,
    RuleType.DATE_TAGS:DateTagsRule,
    RuleType.GROUP:RuleGroup
}


@dataclass
class DemandTemplate:
    "template of demands (ie uncovered duties)"
    rules:Rule
    name:str
    id:str
    activity_tags:set[str]
    start_time:datetime.time
    finish_time:datetime.time
    
@dataclass
class SupplyTemplateEntry:
    dateoffset:int
    demand_offer:DemandTemplate
    
@dataclass
class SupplyTemplate:
    "template of offers of cover"
    staff:set[str]
    entries:tuple[SupplyTemplateEntry,...]
    
@dataclass
class SupplyOffer:
    supply_template:SupplyTemplate
    anchor_date:datetime.date
    staff:str
    active:cp_model.IntVar

@dataclass
class ConcreteActivityOffer:
    demand_template:DemandTemplate
    anchor_date:datetime.date
    staff:str
    active:cp_model.IntervalVar
    offers:list[SupplyOffer]

def make_calendar(month,year,rules):
    starting_date=datetime.date(year,month,1)
    starting_date-=datetime.timedelta(days=starting_date.weekday()) #will be the monday before the start of the month
    if (starting_date+datetime.timedelta(days=42)).day>7:
        starting_date-=datetime.timedelta(days=7)   #if more than one week of following month displayed then move back to show a complete week of previous month instead
    for d in range(42):
        test_date=starting_date+datetime.timedelta(days=d)
        yield {'day':test_date.day,'active':rule_matches(test_date,rules)}

def rule_matches(date:datetime.date, rule:Rule):
    "does rule match on this day"
    return rule.matches(date)
    
def get_all_templates():
    return demand_templates.values()

@dataclass(frozen=True)
class BoundTemplate:
    template:DemandTemplate
    start_time:datetime.datetime
    finish_time:datetime.datetime

def get_templates_for_date_range(fromdate:datetime.date,todate:datetime.date):
    for day in (fromdate+datetime.timedelta(days=d) for d in range((todate-fromdate).days)):
        for templ in get_all_templates():
            if rule_matches(day,templ.rules):
                start_time=datetime.datetime.combine(day,templ.start_time)
                finish_time=datetime.datetime.combine(day,templ.finish_time)
                if finish_time<=start_time:
                    finish_time+=datetime.timedelta(days=1)
                yield BoundTemplate(
                    template=templ,
                    start_time=start_time,
                    finish_time=finish_time
                )
