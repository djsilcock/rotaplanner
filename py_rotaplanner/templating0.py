
import datetime
from dataclasses import dataclass,replace,field,is_dataclass,fields
from enum import StrEnum,IntEnum,auto
from typing import cast,TYPE_CHECKING
import itertools

if TYPE_CHECKING:
    from scheduling import Activity


from ortools.sat.python import cp_model

from typing import List
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

class RuleBase(Base):
    __tablename__="rule"
    id:Mapped[int]=mapped_column(primary_key=True)
    type: Mapped[str]
    parent_id:Mapped[int|None]=mapped_column(ForeignKey('rule.id'))
    parent:Mapped["RuleGroup"]=relationship(back_populates="members",foreign_keys=[parent_id],remote_side=[id])
    __mapper_args__ = {
        "polymorphic_identity": "rule",
        "polymorphic_on":"type"
    }
    @classmethod
    def from_json(cls,data):
        ruleclass=rule_types[data['type']]
        if cls!=ruleclass:
            return ruleclass.from_json(data)
        return cls(**data)

class Rule(RuleBase):
    anchor_date:Mapped[datetime.datetime|None]
    @classmethod
    def from_json(cls,data):
        data['anchor_date']=datetime.datetime.fromisoformat(data['anchor_date'])
        return super().from_json(data)

class GroupType(StrEnum):
    AND='and'
    OR='or'
    NOT='not'

class RuleType(StrEnum):
    "Date rule types"
    DAILY='daily'
    WEEKLY='weekly'
    MONTHLY='day-in-month'
    WEEK_IN_MONTH='week-in-month'
    DATE_RANGE='date-range'
    DATE_TAGS='date-tag'
    GROUP='group'


class RuleGroup(RuleBase):
    group_type:Mapped[str|None]
    members:Mapped[list[RuleBase]]=relationship(back_populates="parent",cascade='save-update,merge,delete')
    __mapper_args__ = {
        "polymorphic_identity": "group",
    }
    def matches(self,match_date):
        match self.group_type:
            case GroupType.AND:
                return all(rule.matches(match_date) for rule in self.members)
            case GroupType.OR:
                return any(rule.matches(match_date) for rule in self.members)
            case GroupType.NOT:
                return not any(rule.matches(match_date)for rule in self.members)
    @classmethod
    def from_json(cls,data):
        data['members']=[Rule.from_json(d) for d in data['members']]
        return super().from_json(data)

class DailyRule(Rule):
    day_interval:Mapped[int|None]
    __mapper_args__ = {
        "polymorphic_identity": RuleType.DAILY,
    }
    def matches(self,match_date:datetime.date):
        return (match_date-self.anchor_date).days%self.day_interval==0


class WeeklyRule(Rule):
    "every nth week"
    week_interval:Mapped[int|None]
    __mapper_args__ = {
        "polymorphic_identity": RuleType.WEEKLY,
    }
    def matches(self,match_date:datetime.date):
        return (match_date-self.anchor_date).days%(7*self.week_interval)==0


class MonthlyRule(Rule):
    "every nth month"
    month_interval:Mapped[int|None]    
    __mapper_args__ = {
        "polymorphic_identity": "monthly",
    }

class DayOfMonthRule(MonthlyRule):
    "nth day of every month"
    __mapper_args__ = {
        "polymorphic_identity": RuleType.MONTHLY,
    }
    def matches(self,match_date:datetime.date):
        if self.anchor_date.day!=match_date.day:
            return False
        return ((self.anchor_date.year*12+self.anchor_date.month)-(match_date.year*12+match_date.month))%self.month_interval==0
    

class WeekInMonthRule(MonthlyRule):
    "the nth week of every mth month"
    __mapper_args__ = {
        "polymorphic_identity": RuleType.WEEK_IN_MONTH,
    }
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
    start_date:Mapped[datetime.datetime|None]
    finish_date:Mapped[datetime.datetime|None]
    range_type:Mapped[str|None]
    __mapper_args__={
        "polymorphic_identity":RuleType.DATE_RANGE
    }
    def matches(self,match_date:datetime.date):
        if self.range_type==DateType.INCLUSIVE:
            return self.start_date<=match_date<=self.finish_date
        return not (self.start_date<=match_date<=self.finish_date)


class DateTagsRule(Rule):
    label:Mapped[str|None]
    date_type:Mapped[str|None]
    __mapper_args__={
        "polymorphic_identity":RuleType.DATE_TAGS
    }



rule_types={
    RuleType.DAILY:DailyRule,
    RuleType.WEEKLY:WeeklyRule,
    RuleType.MONTHLY:MonthlyRule,
    RuleType.WEEK_IN_MONTH:WeekInMonthRule,
    RuleType.DATE_RANGE:DateRangeRule,
    RuleType.DATE_TAGS:DateTagsRule,
    RuleType.GROUP:RuleGroup
}


class Template:
    __tablename__ = "template"
    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str]
    ruleset:Mapped[RuleGroup]=relationship(cascade='save-update,merge,delete')
    __mapper_args__ = {
        "polymorphic_identity": "template",
        "polymorphic_on": "type",
    }

class DemandTemplate(Base):
    "template of demands (ie uncovered duties)"
    __tablename__="demand_template"
    id: Mapped[int] = mapped_column(primary_key=True)
    ruleset_id:Mapped[int]=mapped_column(ForeignKey('rule.id'))
    ruleset:Mapped[RuleGroup]=relationship(cascade='save-update,merge,delete')
    name:Mapped[str]
    activity_tags:Mapped[str]
    start_time:Mapped[datetime.datetime]
    finish_time:Mapped[datetime.datetime]
    def matches(self,date):
        return self.ruleset.matches(date)
    @classmethod
    def from_json(cls,data):
        data['start_time']=datetime.datetime.fromisoformat(data['start_time'])
        data['finish_time']=datetime.datetime.fromisoformat(data['finish_time'])
        data['rules']=Rule.from_json(data['rules'])
        return cls(**data)
    

class SupplyTemplateEntry(Base):
    __tablename__="supply_template_entry"
    id: Mapped[int] = mapped_column(primary_key=True)
    dateoffset:Mapped[int]
    activity_tags:Mapped[str]
    template_id:Mapped[int]=mapped_column(ForeignKey('supply_template.id'))
    
class SupplyTemplate(Base):
    "template of offers of cover"
    __tablename__="supply_template"
    staff:Mapped[str]
    ruleset_id:Mapped[int]=mapped_column(ForeignKey('rule.id'))
    ruleset:Mapped[RuleGroup]=relationship(cascade='save-update,merge,delete')
    name:Mapped[str]
    entries:Mapped[list[SupplyTemplateEntry]]=relationship(cascade='save-update,merge,delete')
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



rule_types={
    RuleType.DAILY:DailyRule,
    RuleType.WEEKLY:WeeklyRule,
    RuleType.MONTHLY:MonthlyRule,
    RuleType.WEEK_IN_MONTH:WeekInMonthRule,
    RuleType.DATE_RANGE:DateRangeRule,
    RuleType.DATE_TAGS:DateTagsRule,
    RuleType.GROUP:RuleGroup
}


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

from sqlalchemy import create_engine,select
engine = create_engine("sqlite://", echo=True)
Base.metadata.create_all(engine)

from sqlalchemy.orm import Session

with Session(engine) as session:
    rulegroup=RuleGroup(group_type="and")
    daily_rule=DailyRule(day_interval=1,anchor_date=datetime.datetime.today())
    rulegroup.members.append(daily_rule)
    template=DemandTemplate(name='x',start_time=datetime.datetime.today(),finish_time=datetime.datetime.today(),activity_tags="")
    template.ruleset=rulegroup
    session.add(template)
    session.commit()
    for row in session.scalars(select(Rule)):
        print(row)
    session.delete(template)
    session.commit()
