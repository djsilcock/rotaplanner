
import datetime
from dataclasses import dataclass,replace,field,is_dataclass,fields
from enum import StrEnum,IntEnum,auto
from typing import cast,TYPE_CHECKING
import itertools

if TYPE_CHECKING:
    from scheduling import Activity


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
    def matches(self,date):
        return self.rules.matches(date)
    
@dataclass
class SupplyTemplateEntry:
    dateoffset:int
    activity_tags:set[str]
    id:str
    
@dataclass
class SupplyTemplate:
    "template of offers of cover"
    staff:set[str]
    rules:Rule
    name:str
    id:str
    entries:tuple[SupplyTemplateEntry,...]
    def materialise(self,date,activities:dict[datetime.date,list['Activity']]):
        results=[]
        if not self.rules.matches(date):
            return
        for entry in self.entries:
            if date+datetime.timedelta(days=entry.dateoffset) not in activities:
                return
            possibilities=set()
            for activity in activities[date+datetime.timedelta(days=entry.dateoffset)]:
                if not entry.activity_tags.isdisjoint(activity.template.activity_tags):
                    possibilities.add(activity.id)
                if activity.template.id in entry.activity_tags:
                    possibilities.add(activity.id)
            if len(possibilities)==0:
                return
            results.append(possibilities)
        for combination in itertools.product(*results):
            combi=set(combination)
            if len(combi)==len(self.entries):  #de-duplicate
                yield combi

def generate_offers_for_range(start,finish):
    supply_template:SupplyTemplate
    day=start
    activities_by_date={}
    activities_by_offer={}
    offers={}
    offers_active={}
    activities_active={}
    while day<finish:
        activities_by_date[day]=datastore.get_activities_for_day(day)    
        day+=datetime.timedelta(day=1)
        
        activities_active.update(dict.fromkeys(activities_by_date[day],False))
    for supply_template in datastore.get_supply_templates():
        for date in activities_by_date:
            offers[supply_template.id,date]=list(supply_template.materialise(date,activities_by_date))
            
            for index,offer_combination in enumerate(offers[supply_template.id,date]):
                offers[supply_template.id,date,index]=offer_combination
                for activity in offer_combination:
                    activities_by_offer.setdefault(activity,set()).add((supply_template.id,date,index))
                    offers_active[supply_template.id,date,index]=None
                    offers[supply_template.id,date,index]=offer_combination
                    activities_active[activity]=None
    for o in offers_active:
        offers_active[o]=model.new_bool_var(repr(o))
    for a in activities_active:
        if activities_active[a] is None:
            activities_active[a]=model.new_bool_var(a)
    for o,v in offers.items():
        if len(o)==2:
            continue
        model.add_all_true(activities_active[act] for act in v).only_enforce_if(offers_active[o])
    for activity,v in activities_by_offer.items():
        model.at_least_one(offers_active[offer] for offer in v).only_enforce_if(activities_active[activitity])
"""
Offer active =>activity active
activity active =>at least one offer active
"""        
                
        
                
    


    
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

def rule_matches(date:datetime.date, rule:Rule):
    "does rule match on this day"
    return rule.matches(date)
    
def get_all_templates():
    return demand_templates.values()

