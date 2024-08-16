
import datetime
from dataclasses import dataclass,replace,field,is_dataclass,fields
from pydantic import BaseModel,Field,RootModel
from enum import StrEnum,IntEnum,auto
from typing import cast,TYPE_CHECKING,Annotated,Literal
import itertools
import uuid
import json

if TYPE_CHECKING:
    from scheduling import Activity


from ortools.sat.python import cp_model

from typing import List,Union
from typing import Optional
import datetime
from enum import StrEnum
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

class Base(DeclarativeBase):
    pass

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
    AND='and'
    OR='or'
    NOT='not'



class RuleGroup(BaseModel):
    rule_type:Literal[RuleType.GROUP]=RuleType.GROUP
    group_type:GroupType
    members:list['Rule']=Field(default_factory=list)
    def matches(self,match_date):
        match self.group_type:
            case GroupType.AND:
                return all(rule.matches(match_date) for rule in self.members)
            case GroupType.OR:
                return any(rule.matches(match_date) for rule in self.members)
            case GroupType.NOT:
                return not any(rule.matches(match_date)for rule in self.members)

class DailyRule(BaseModel):
    rule_type:Literal[RuleType.DAILY]=RuleType.DAILY
    day_interval:int
    anchor_date:datetime.date
    def matches(self,match_date:datetime.date):
        return (match_date-self.anchor_date).days%self.day_interval==0

class WeeklyRule(BaseModel):
    "every nth week"
    rule_type:Literal[RuleType.WEEKLY]=RuleType.WEEKLY
    week_interval:int
    anchor_date:datetime.date
    def matches(self,match_date:datetime.date):
        return (match_date-self.anchor_date).days%(7*self.week_interval)==0


 

class DayOfMonthRule(BaseModel):
    "nth day of every month"
    rule_type:Literal[RuleType.MONTHLY]=RuleType.MONTHLY
    month_interval:int
    anchor_date:datetime.date
    def matches(self,match_date:datetime.date):
        if self.anchor_date.day!=match_date.day:
            return False
        return ((self.anchor_date.year*12+self.anchor_date.month)-(match_date.year*12+match_date.month))%self.month_interval==0
    

class WeekInMonthRule(BaseModel):
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

class DateRangeRule(BaseModel):
    rule_type:Literal[RuleType.DATE_RANGE]=RuleType.DATE_RANGE
    start_date:datetime.date
    finish_date:datetime.date
    range_type:DateType
    def matches(self,match_date:datetime.date):
        if self.range_type==DateType.INCLUSIVE:
            return self.start_date<=match_date<=self.finish_date
        return not (self.start_date<=match_date<=self.finish_date)


class DateTagsRule(BaseModel):
    rule_type:Literal[RuleType.DATE_TAGS]=RuleType.DATE_TAGS
    label:str
    date_type:DateType

Rule=Annotated[Union[RuleGroup,DailyRule,WeeklyRule,DayOfMonthRule,WeekInMonthRule,DateRangeRule,DateTagsRule,RuleGroup],Field(discriminator='rule_type')]




class DemandTemplate(BaseModel):
    id:uuid.UUID=Field(default_factory=uuid.uuid4)
    ruleset:RuleGroup
    name:str
    activity_tags:set[str]
    start_time:datetime.time
    duration:datetime.timedelta
    def matches(self,date):
        return self.ruleset.matches(date)
    

class SupplyTemplateEntry(BaseModel):
    dateoffset:int
    activity_tags:set[str]
    template_id:uuid.UUID
    
class SupplyTemplate(BaseModel):
    "template of offers of cover"
    id:uuid.UUID=Field(default_factory=uuid.UUID4)
    staff:str
    ruleset:RuleGroup
    name:str
    entries:list[SupplyTemplateEntry]
    def materialise(self,date,activities:dict[datetime.date,list['Activity']]):
        results=[]
        if not self.ruleset.matches(date):
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

rulegroup=RuleGroup(group_type="and")
daily_rule=DailyRule(day_interval=1,anchor_date=datetime.datetime.today().date())
rulegroup.members.append(daily_rule)
template=DemandTemplate(name='x',ruleset=rulegroup,start_time=datetime.datetime.today().time(),duration='P1DT1H59M59S',activity_tags={'1','2','3'})
print (template)
template_str=template.model_dump_json()
print(DemandTemplate.model_validate_json(template_str))

print(json.dumps(template.model_json_schema(),indent=2))