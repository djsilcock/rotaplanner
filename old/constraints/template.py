"""contains rules to constrain the model"""
import datetime
from collections import defaultdict
from contextvars import ContextVar
from itertools import pairwise
from typing import Any, Literal, TypedDict, cast,TypeVar,Callable,Sequence,overload

import attrs
from ortools.sat.python.cp_model import IntVar,IntervalVar

from old.constraint_ctx import BaseConstraintConfig, DutyStore
from constraints.core_duties import CoreDuties
from constraints.date_utils import convert_isodate, is_cycle, is_nth_of_month
from constraints.utils import groupby

AnchorType = Literal['MONTH'] | Literal['WEEK']

#template_store: ContextVar[dict] = ContextVar('template_store')



PHAction = Literal[
    'ignore',  # ignore PH and treat as normal day
    'omit',  # omit PH sessions, but keep remainder of template
    'must_be',  # template only valid if this day is a PH
    'must_not_be'  # template only valid if this day is not a PH
]


@attrs.frozen
class BoundTemplateEntry:
    "immutable entry in bound template"
    start: datetime.datetime
    finish: datetime.datetime
    tag: str
    ph_action: PHAction


@attrs.frozen
class BoundTemplate:
    "immutable tuple of template bound to date,session, and person"
    staff_member: str
    template_id: Any
    layer: int
    template_entries: tuple[BoundTemplateEntry, ...]


@attrs.frozen
class TemplateEntry:
    "entry in template config"
    start:datetime.datetime
    finish:datetime.datetime
    tag: str
    ph_action: PHAction
    
def validate_weekday(self,attrib,weekday):
    if weekday not in {0,1,2,3,4,5,6}:
        raise ValueError('weekday invalid')
    
def validate_weekdays(self,attrib,weekdays):
    for w in weekdays:
        validate_weekday(self,attrib,w)

@attrs.define
class NthOfMonth:
    days:set[int]=attrs.field(converter=set)
    repeat_type='nth_of_month'
    def generate(self,start:datetime.date,finish:datetime.date):

        if finish<start:
            return
        month=start.month
        year=start.year
        days=sorted(self.days)
        current=start
        while current<=finish:
            for d in days:
                yield datetime.date(year,month,d)
            month+=1
            if month>12:
                month=1
                year+=1


@attrs.define
class NthWeekOfMonth:
    weekdays:set[int]=attrs.field(converter=set)
    weeks:set[int]=attrs.field(converter=set)
    repeat_type='nth_week_of_month'
    def generate(self,start:datetime.date,finish:datetime.date):
        for day in range(start.toordinal(),finish.toordinal()):
            date=datetime.date.fromordinal(day)
            if date.weekday in self.weekdays and (date.day//7)+1 in self.weeks:
                yield date

        

@attrs.define
class EveryNthWeek:
    cycle_length:int
    weeks:set[int]=attrs.field(converter=set)
    weekday:int=attrs.field()
    anchor_date:datetime.date=attrs.field(converter=convert_isodate)
    repeat_type='every_nth_week'
    def generate(self,start:datetime.date,finish:datetime.date):
        anchor_ord=self.anchor_date.toordinal()+(7+self.weekday-self.anchor_date.weekday())%7
        start_ord=start.toordinal()-(start.toordinal()-anchor_ord)%(self.cycle_length*7)
        cycles=(finish.toordinal()-start_ord)//(self.cycle_length*7)+1
        for cycle in range(cycles):
            for week in range(self.cycle_length):
                if (week+1) in self.weeks:
                    day= start_ord+(cycle*self.cycle_length*7)+(week*7)
                    if finish.toordinal()>=day>=start.toordinal():
                        yield datetime.date.fromordinal(day)
        
        

repeat_types={
    'nth_of_month':NthOfMonth,
    'nth_week_of_month':NthWeekOfMonth,
    'every_nth_week':EveryNthWeek}

RepeatType=NthOfMonth|NthWeekOfMonth|EveryNthWeek

def make_repeat_type(rpt):
    match rpt:
        case {'repeat_type':repeat_type}:
            return repeat_types[repeat_type](**rpt)
    if isinstance(rpt,RepeatType):
        return rpt
    raise TypeError

def from_dict(cls):
    def inner(dct_or_inst):
        if isinstance(dct_or_inst,cls):
            return dct_or_inst
        if isinstance(dct_or_inst,dict):
            return cls(dct_or_inst)
    return inner

G=TypeVar('G')

def for_each(converter:Callable[[Any],G])->Callable[[Sequence],list[G]]:
    def inner(sequence:Sequence):
        return [converter(v) for v in sequence]
    return inner


@attrs.frozen
class BaseTemplate:
    "base template"
    template_id: Any
    anchor_date: datetime.date=attrs.field(converter=convert_isodate)
    repeat:RepeatType=attrs.field(converter=make_repeat_type)
    template_entries: tuple[TemplateEntry, ...] = attrs.field(
        converter=attrs.converters.pipe(for_each(from_dict(TemplateEntry)),tuple))

@attrs.define
class Staffing:
    "staffing demand in an activity"
    maximum:int
    minimum:int
    acceptable_staff:set[str]
    staff_in_place:dict[str,IntVar]

@attrs.define
class DemandTemplate:
    "config class for demand at a location"
    start_date: datetime.date = attrs.field(converter=convert_isodate)
    end_date: datetime.date = attrs.field(converter=convert_isodate)
    staff_demands:set[Staffing]
    base_template:BaseTemplate

@attrs.define
class Activity:
    "concrete activity to generate demand"
    source_template:DemandTemplate
    activity_name:str
    location:str
    start_time:datetime.datetime
    finish_time:datetime.datetime
    staff_demands:set[Staffing]

@attrs.define
class SupplyTemplate:
    "configuration class for template"
    start_date: datetime.date = attrs.field(converter=convert_isodate)
    end_date: datetime.date = attrs.field(converter=convert_isodate)
    staff_member: str
    layer: int
    template_id: str
    base_template: BaseTemplate

    def bind(self, day, staff) -> BoundTemplate | None:
        "attempt to bind to day and staff"
        if day < self.start_date:
            return None
        if day > self.end_date:
            return None
        if self.base_template.anchor_type == 'MONTH':
            if not is_nth_of_month(day, self.base_template.anchor_date):
                return None
        if self.base_template.anchor_type == 'WEEK':
            if not is_cycle(self.base_template.anchor_date, day, self.base_template.repeat_period):
                return None

        return BoundTemplate(
            staff_member=staff,
            template_id=self.base_template.template_id,
            layer=self.layer,
            template_entries=tuple(BoundTemplateEntry(
                start=day+te.start,
                finish=day+te.finish,
                tag=te.tag,
                ph_action=te.ph_action) for te in self.base_template.template_entries
            ))
    

class TemplateConfigEntry(TypedDict):
    "entry in config"
    template_store: dict[str, BaseTemplate]
    demand_templates: list
    supply_templates:list


class TemplateConstraint(BaseConstraintConfig):
    "applies templates to rota"
    dutystore: DutyStore[BoundTemplate]
    demand_templates: list[DemandTemplate]
    supply_templates: list[SupplyTemplate]
    constraint_name = 'template'

    def setup(self):
        config = cast(TemplateConfigEntry, self.config())
        template_store:dict[str, BaseTemplate] = config.get('template_store', {}).copy()
        self.demand_templates = [
            DemandTemplate(base_template=template_store[t['template_id']], **t)
            for t in config.setdefault('demand_templates', [])
            if t['template_id'] in template_store]
        self.supply_templates = [
            SupplyTemplate(base_template=template_store[t['template_id']], **t)
            for t in config.setdefault('supply_templates', [])
            if t['template_id'] in template_store]
        

    def apply_constraint(self):
        core_duties = CoreDuties.from_context(self.ctx)
        core = self.ctx.core_config
        TemplateDict = dict[tuple[str, datetime.datetime,
                                  datetime.datetime, str], set[BoundTemplate]]
        templates_for_duty_session = cast(
            TemplateDict, defaultdict(default_factory=set))
        self.dutystore = DutyStore(self.ctx.model)
        for day in core.days:
            for staff in core.staff:
                for template in self.supply_templates:
                    if (bound := template.bind(day, staff)):
                        entries_to_add = cast(
                            TemplateDict, defaultdict(default_factory=set))
                        for entry in bound.template_entries:
                            if day in core.pubhols:
                                if entry.ph_action == "ignore":
                                    pass
                                elif entry.ph_action == 'must_not_be':
                                    break
                                elif entry.ph_action == 'omit':
                                    continue
                            else:
                                if entry.ph_action == 'must_be':
                                    break
                            key = (staff, entry.start, entry.finish, entry.tag)
                            entries_to_add[key].add(bound)
                        else:
                            for k, v in entries_to_add.items():
                                templates_for_duty_session[k].update(v)
        for day in core.days:
            for staff in core.staff:
                for shift in core.shifts:
                    for tag in (*core_duties.locations, *core_duties.tags):
                        key = (staff, day, shift, tag)
                        if key in templates_for_duty_session:
                            for grp in groupby(templates_for_duty_session[key], lambda t: t.layer):
                                self.model.Add(
                                    sum(self.dutystore[bound_templ] for bound_templ in grp) > 0)
                        else:
                            self.model.Add(core_duties.allocated_for_duty(
                                shift, day, staff, tag) == 0)

    @classmethod
    def validate_frontend_json(cls, json_config, orig_config):
        pass
