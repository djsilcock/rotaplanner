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
        return ruleclass.from_json(data)

class Rule(RuleBase):
    anchor_date:Mapped[datetime.datetime|None]
    @classmethod
    def from_json(cls,data):
        data['anchor_date']=datetime.datetime.fromisoformat(data['anchor_date'])
        return cls(**data)

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
    template_id:Mapped[int|None]=mapped_column(ForeignKey('template.id'))
    members:Mapped[list[RuleBase]]=relationship(back_populates="parent")
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


class Template(Base):
    __tablename__ = "template"
    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str]
    rules:Mapped[RuleGroup]=relationship()
    __mapper_args__ = {
        "polymorphic_identity": "template",
        "polymorphic_on": "type",
    }

class DemandTemplate(Template):
    "template of demands (ie uncovered duties)"
    __tablename__="demand_template"
    id: Mapped[int]=mapped_column(ForeignKey('template.id'),primary_key=True)
    
    name:Mapped[str]
    activity_tags:Mapped[str]
    start_time:Mapped[datetime.datetime]
    finish_time:Mapped[datetime.datetime]
    __mapper_args__={
        "polymorphic_identity":"demand_template"
    }
    def matches(self,date):
        return self.rules.matches(date)
    @classmethod
    def from_json(cls,data):
        data['start_time']=datetime.datetime.fromisoformat(data['start_time'])
        data['finish_time']=datetime.datetime.fromisoformat(data['finish_time'])
        data['rules']=Rule.from_json(data['rules'])
        return cls(**data)
    

class SupplyTemplateEntry:
    dateoffset:int
    activity_tags:set[str]
    id:str
    
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


    
from sqlalchemy import create_engine,select
engine = create_engine("sqlite://", echo=True)
Base.metadata.create_all(engine)

from sqlalchemy.orm import Session

with Session(engine) as session:
    rulegroup=RuleGroup(group_type="and")
    daily_rule=DailyRule(day_interval=1,anchor_date=datetime.datetime.today())
    rulegroup.members.append(daily_rule)
    template=DemandTemplate(name='x',start_time=datetime.datetime.today(),finish_time=datetime.datetime.today(),activity_tags="")
    template.rules=rulegroup
    session.add(template)
    session.commit()
    for row in session.scalars(select(Template)):
        print(row.rules)
    