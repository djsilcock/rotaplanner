"""contains rules to constrain the model"""
from dataclasses import dataclass,asdict,field
from datetime import date, timedelta
from typing import Any, Literal, NamedTuple,TypedDict,cast
from constraint_ctx import DutyStore,BaseConstraintConfig
from constraints.core_duties import CoreDuties
from constraints.date_utils import is_cycle, is_nth_of_month
from constraints.utils import groupby

AnchorType = Literal['MONTH'] | Literal['WEEK']


class TemplateEntry(NamedTuple):
    "entry in template config"
    date_offset: int
    session: str
    tag: str


class BoundTemplateEntry(NamedTuple):
    "immutable entry in bound template"
    date: date
    session: str
    tag: str


class BoundTemplate(NamedTuple):
    "immutable tuple of template bound to date,session, and person"
    staff_member: str
    template_id: Any
    layer:int
    anchor_date: date
    template_entries: tuple[BoundTemplateEntry, ...]

@dataclass
class BaseTemplate:
    template_id:Any
    anchor_date:date
    anchor_type:AnchorType
    repeat_period:int
    template_entries:list[TemplateEntry]

    @classmethod
    def from_json(cls,template_entries,**d):
        return cls(template_entries=[TemplateEntry(**te) for te in template_entries],**d)

@dataclass
class Template:
    "configuration class for template"
    base_template: BaseTemplate
    start_date: date
    end_date: date
    staff_member: str
    layer:int

    @classmethod
    def from_json(cls,template_store:dict,base_template:str,**val):
        return cls(base_template=template_store[base_template],**val)
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
            anchor_date=day,
            template_entries=tuple(BoundTemplateEntry(
                date=day+timedelta(days=te.date_offset),
                session=te.session,
                tag=te.tag) for te in self.base_template.template_entries
            ))


class BoundTemplateKey(NamedTuple):
    "namedtuple for internal use"
    staff: str
    day: date
    session: str
    tag: str

class TemplateConfigEntry(TypedDict):
    template_store:dict[str,dict]
    templates:list

class TemplateConstraint(BaseConstraintConfig):
    "applies templates to rota"
    dutystore: DutyStore[BoundTemplate]
    templates: list[Template]
    constraint_name='template'
    def setup(self):
        config=cast(TemplateConfigEntry,self.config())
        template_store={k:BaseTemplate.from_json(template_id=k,**v) for k,v in config.setdefault('template_store',{}).items()}
        self.templates = [Template.from_json(template_store,**t) for t in config.setdefault('templates',[])]

    def apply_constraint(self):
        core_duties = CoreDuties.from_context(self.ctx)
        core = self.ctx.core_config
        bound_templates: dict[BoundTemplateKey, set[BoundTemplate]] = {}
        self.dutystore = DutyStore(self.ctx.model)
        for day in core.days:
            for staff in core.staff:
                for template in self.templates:
                    if (bound := template.bind(day, staff)):
                        for entry in bound.template_entries:
                            key = BoundTemplateKey(
                                staff, entry.date, entry.session, entry.tag)
                            bound_templates.setdefault(key, set()).add(bound)
        for day in core.days:
            for staff in core.staff:
                for shift in core.shifts:
                    for tag in (*core_duties.locations, *core_duties.tags):
                        key = BoundTemplateKey(staff, day, shift, tag)
                        if key in bound_templates:
                            for grp in groupby(bound_templates[key],lambda t:t.layer):
                                self.model.Add(
                                    sum(self.dutystore[bound] for bound in grp) > 0)
                        else:
                            self.model.Add(core_duties.allocated_for_duty(
                                shift, day, staff, tag) == 0)


