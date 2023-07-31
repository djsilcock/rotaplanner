"""contains rules to constrain the model"""
import attrs
from contextvars import ContextVar
import datetime
from typing import Any, Literal,TypedDict,cast
from constraint_ctx import DutyStore,BaseConstraintConfig
from constraints.core_duties import CoreDuties
from constraints.date_utils import is_cycle, is_nth_of_month,convert_isodate
from constraints.utils import groupby

AnchorType = Literal['MONTH'] | Literal['WEEK']

template_store:ContextVar[dict]=ContextVar('template_store')

PHAction=Literal['ignore','omit','must_be','must_not_be']

@attrs.frozen
class BoundTemplateEntry:
    "immutable entry in bound template"
    date:datetime.date
    session: str
    tag: str
    ph_action:PHAction

@attrs.frozen
class BoundTemplate:
    "immutable tuple of template bound to date,session, and person"
    staff_member: str
    template_id: Any
    layer:int
    template_entries: tuple[BoundTemplateEntry, ...]


@attrs.frozen
class TemplateEntry:
    "entry in template config"
    date_offset: int
    session: str
    tag: str
    ph_action:PHAction
    @classmethod
    def from_dict_list(cls,dl):
            l=[]
            for d in dl:
                if isinstance(d,dict):
                    l.append(cls(**d))
                l.append(d)
            return tuple(l)

@attrs.frozen
class BaseTemplate:
    template_id:Any
    anchor_date:datetime.date =attrs.field(converter=convert_isodate)
    anchor_type:AnchorType
    repeat_period:int
    template_entries:tuple[TemplateEntry]=attrs.field(
        converter=TemplateEntry.from_dict_list)


@attrs.define
class Template:
    "configuration class for template"
    start_date: datetime.date =attrs.field(converter=convert_isodate)
    end_date: datetime.date =attrs.field(converter=convert_isodate)
    staff_member: str
    layer:int
    template_id:str
    base_template:BaseTemplate

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
                date=day+datetime.timedelta(days=te.date_offset),
                session=te.session,
                tag=te.tag,
                ph_action=te.ph_action) for te in self.base_template.template_entries
            ))
        
class TemplateConfigEntry(TypedDict):
    template_store:dict[str,BaseTemplate]
    templates:list

class TemplateConstraint(BaseConstraintConfig):
    "applies templates to rota"
    dutystore: DutyStore[BoundTemplate]
    templates: list[Template]
    template_store:dict[str,BaseTemplate]
    constraint_name='template'

    def setup(self):
        config=cast(TemplateConfigEntry,self.config())
        template_store=config.get('template_store',{}).copy()
        self.templates = [
            Template(base_template=template_store[t['template_id']],**t) 
            for t in config.setdefault('templates',[])
            if t['template_id'] in template_store]
    def apply_constraint(self):
        core_duties = CoreDuties.from_context(self.ctx)
        core = self.ctx.core_config
        TemplateDict=dict[tuple[str,datetime.date,str,str], set[BoundTemplate]]
        templates_for_duty_session: TemplateDict = {}
        self.dutystore = DutyStore(self.ctx.model)
        for day in core.days:
            for staff in core.staff:
                for template in self.templates:
                    if (bound := template.bind(day, staff)):
                        entries_to_add:TemplateDict={}
                        for entry in bound.template_entries:
                            if day in core.pubhols:
                                if entry.ph_action=="ignore":
                                    pass
                                elif entry.ph_action=='must_not_be':
                                    break
                                elif entry.ph_action=='omit':
                                    continue
                            else:
                                if entry.ph_action=='must_be':
                                    break
                            
                            key = (staff, entry.date, entry.session, entry.tag)
                            entries_to_add.setdefault(key, set()).add(bound)
                        else:
                            for k,v in entries_to_add.items():
                                templates_for_duty_session.setdefault(k,set()).update(v)
        for day in core.days:
            for staff in core.staff:
                for shift in core.shifts:
                    for tag in (*core_duties.locations, *core_duties.tags):
                        key = (staff, day, shift, tag)
                        if key in templates_for_duty_session:
                            for grp in groupby(templates_for_duty_session[key],lambda t:t.layer):
                                self.model.Add(
                                    sum(self.dutystore[bound_templ] for bound_templ in grp) > 0)
                        else:
                            self.model.Add(core_duties.allocated_for_duty(
                                shift, day, staff, tag) == 0)
    @classmethod
    def validate_frontend_json(cls,json_config,orig_config):
        pass



