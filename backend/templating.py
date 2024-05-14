
import datetime
import dataclasses
import enum
from typing import Literal,cast,overload,Iterable,Generator,Any
import random
import string

from ortools.sat.python import cp_model

Intervals=enum.StrEnum('Intervals','week day month')
RuleType=enum.StrEnum('RuleType','EN ENWM')
GroupType=enum.StrEnum('GroupType','AND OR NOT')


demand_templates={}


@dataclasses.dataclass
class Rule:
    "Templating rule"
    rule_id:str
    anchor_date:datetime.date
    frequency:int
    interval:Intervals
    rule_type:RuleType

    def __post_init__(self):
        self.interval=Intervals(self.interval)
        self.rule_type=RuleType(self.rule_type)
        if isinstance(self.anchor_date,str):
            self.anchor_date=datetime.date.fromisoformat(self.anchor_date)

@dataclasses.dataclass
class RuleGroup:
    "Templating rule group"
    rule_id:str
    group_type:GroupType
    rules:list[str]
    rule_type:Literal['group']

    def __post_init__(self):
        self.group_type=GroupType(self.group_type)

def rule_or_rulegroup(data:Rule|RuleGroup|dict) -> Rule|RuleGroup:
    if isinstance(data,(Rule,RuleGroup)):
        return data
    if data['rule_type']=='group':
        return RuleGroup(**data)
    return Rule(**data)
    
@dataclasses.dataclass
class DemandTemplate:
    "template of demands (ie uncovered duties)"
    rules:dict[str,Rule|RuleGroup]
    name:str
    id:str
    activity_type:str
    start:int
    finish:int
    def __post_init__(self):
        self.rules={key:rule_or_rulegroup(value) for key,value in self.rules.items()}
    @classmethod
    def validate(cls,data):
        errors=[f"{field} needs to be supplied" for field in ('rules','name','id','activity_type','start','finish') if field not in data]
        if data['finish'] < data['start']:
            errors.append('finish must not be before start time')
        return errors


    
@dataclasses.dataclass
class SupplyTemplateEntry:
    dateoffset:int
    demand_templates:tuple[str,...]
    
@dataclasses.dataclass
class SupplyTemplate:
    "template of offers of cover"
    staff:set[str]
    rules:dict[str,Rule|RuleGroup]
    entries:tuple[SupplyTemplateEntry,...]
    def __post_init__(self):
        self.entries=tuple((SupplyTemplateEntry(**v) if isinstance(v,dict) else v) for v in self.entries )
        self.rules={key:rule_or_rulegroup(value) for key,value in self.rules.items()}

@dataclasses.dataclass
class SupplyOffer:
    supply_template:SupplyTemplate
    anchor_date:datetime.date
    staff:str
    active:cp_model.IntVar

@dataclasses.dataclass
class ConcreteActivityOffer:
    demand_template:DemandTemplate
    anchor_date:datetime.date
    staff:str
    active:cp_model.IntervalVar
    offers:list[SupplyOffer]




def make_calendar(month,year,rules):
    rules={k:rule_or_rulegroup(v) for k,v in rules.items()}
    starting_date=datetime.date(year,month,1)
    starting_date-=datetime.timedelta(days=starting_date.weekday()) #will be the monday before the start of the month
    if (starting_date+datetime.timedelta(days=42)).day>7:
        starting_date-=datetime.timedelta(days=7)   #if more than one week of following month displayed then move back to show a complete week of previous month instead
    for d in range(42):
        test_date=starting_date+datetime.timedelta(days=d)
        yield {'day':test_date.day,'active':rule_matches(test_date,'root',rules)}

def rule_matches(date:datetime.date, rule_id, rules:dict[str,Rule|RuleGroup],default=None):
    "does rule match on this day"
    rule = rule_or_rulegroup(rules[rule_id])
    if rule is None: 
        return default
    if isinstance(date,str):
        return rule_matches(datetime.date.fromisoformat(date), rule_id, rules)
    if isinstance(rule,RuleGroup):
        match rule.group_type:
            case GroupType.AND:
                return all(rule_matches(date,item,rules,True) for item in rule.rules)
            case GroupType.OR:
                return any(rule_matches(date,item,rules,False) for item in rule.rules)
            case GroupType.NOT:
                return not(rule_matches(date,item,rules,False) for item in rule.rules)
    if rule.rule_type==RuleType.EN:
        if rule.interval==Intervals.month:
            if date.day != rule.anchor_date.day:
                 return False
            return ((date.year*12+date.month)-(rule.anchor_date.year*12+rule.anchor_date.month)%rule.frequency) ==0
        if rule.interval==Intervals.week:
            return (rule.anchor_date-date).days % (rule.frequency*7) == 0
        if rule.interval==Intervals.day:
            return (rule.anchor_date-date).days % (rule.frequency*7) == 0
    if rule.rule_type==RuleType.ENWM:
        if date.weekday()!=rule.anchor_date.weekday():
            return False
        if (date.day - 1) // 7 != (rule.anchor_date.day - 1) // 7:
            return False
        return ((date.year*12+date.month)-(rule.anchor_date.year*12+rule.anchor_date.month)%rule.frequency) ==0
    



@dataclasses.dataclass(frozen=True)
class BoundTemplate:
    template:DemandTemplate
    start_time:int
    finish_time:int

def get_templates_for_date_range(fromdate:datetime.date,todate:datetime.date):
    for day in range((todate-fromdate).days):
        for templ in get_templates_for_day(fromdate+datetime.timedelta(days=day),False):
            yield BoundTemplate(
                template=templ,
                start_time=day*24+templ.start,
                finish_time=day*24+templ.finish
            )
