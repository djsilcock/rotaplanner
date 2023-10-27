"""contains rules to constrain the model"""
import datetime
from collections import defaultdict
from contextvars import ContextVar
from typing import Any, Literal, TypedDict, cast

import attrs

from constraint_ctx import BaseConstraintConfig, DutyStore
from constraints.core_duties import CoreDuties
from constraints.date_utils import convert_isodate, is_cycle, is_nth_of_month
from constraints.utils import groupby

AnchorType = Literal['MONTH'] | Literal['WEEK']

#template_store: ContextVar[dict] = ContextVar('template_store')

shift_splits=[datetime.timedelta(hours=h) for h in (8,13,17,21)]

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


@attrs.frozen
class BaseTemplate:
    "base template"
    template_id: Any
    anchor_date: datetime.date = attrs.field(converter=convert_isodate)
    anchor_type: AnchorType
    repeat_period: int
    template_entries: tuple[TemplateEntry, ...] = attrs.field(
        converter=lambda dct_list:tuple(TemplateEntry(**tmp) for tmp in dct_list))


@attrs.define
class Template:
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
    templates: list


class TemplateConstraint(BaseConstraintConfig):
    "applies templates to rota"
    dutystore: DutyStore[BoundTemplate]
    templates: list[Template]
    #template_store: dict[str, BaseTemplate]
    constraint_name = 'template'

    def setup(self):
        config = cast(TemplateConfigEntry, self.config())
        template_store:dict[str, BaseTemplate] = config.get('template_store', {}).copy()
        self.templates = [
            Template(base_template=template_store[t['template_id']], **t)
            for t in config.setdefault('templates', [])
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
                for template in self.templates:
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
