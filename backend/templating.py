
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

@dataclasses.dataclass
class SupplyOffer:
    demand:DemandTemplate
    
@dataclasses.dataclass
class SupplyTemplate:
    "template of offers of cover"
    staff:set[str]



def update_demand_template(data):
    if data['id'] is None:
        data['id']=''.join([random.choice(string.ascii_letters) for x in range(7)])
        demand_templates[data['id']]=DemandTemplate(**data)
    else:
        if data.get('delete'):
            del demand_templates[data['id']]
        else:
            demand_templates[data['id']]=DemandTemplate(**data)

@overload
def get_demand_templates(asdict:Literal[False]) -> Generator[DemandTemplate,None,None]:
    ...
@overload
def get_demand_templates()-> Generator[DemandTemplate,None,None]:
    ...
@overload
def get_demand_templates(asdict:Literal[True]) -> Generator[dict,None,None]:
    ...

def get_demand_templates(asdict=False):
    return (dataclasses.asdict(m) if asdict else m for m in demand_templates.values())

def rule_matches(date:datetime.date, rule_id, rules:dict[str,Rule|RuleGroup],default=None):
    "does rule match on this day"
    rule = rules[rule_id]
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
    

@overload
def get_templates_for_day(date:datetime.date,asdict:Literal[False])->Generator[DemandTemplate,None,None]:
    ...
@overload
def get_templates_for_day(date:datetime.date,asdict:Literal[True])->Generator[dict,None,None]:
    ...
    
def get_templates_for_day(date:datetime.date,asdict=False):
    "return list of demand templates valid on given day"
    templates=(t for t in get_demand_templates() if rule_matches(date,'root',t.rules))
    if asdict:
        return (dataclasses.asdict(t) for t in templates)
    return templates

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
