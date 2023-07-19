"""contains rules to constrain the model"""
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Literal, NamedTuple
from constraint_ctx import DutyStore,BaseConstraintConfig
from constraints.core_duties import CoreDuties
from constraints.date_utils import is_cycle, is_nth_of_month
from config.jobplans import jobplans, trainee_default


AnchorType = Literal['MONTH'] | Literal['WEEK']


class TemplateEntry:
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
    anchor_date: date
    template_entries: tuple[BoundTemplateEntry, ...]


@dataclass
class Template:
    "configuration class for template"
    template_id: Any
    anchor_date: date
    start_date: date
    end_date: date
    anchor_type: AnchorType
    repeat_period: int
    staff_members: set
    template_entries: list[TemplateEntry]

    def bind(self, day, staff) -> BoundTemplate | None:
        "attempt to bind to day and staff"
        if day < self.start_date:
            return None
        if day > self.end_date:
            return None
        if self.anchor_type == 'MONTH':
            if not is_nth_of_month(day, self.anchor_date):
                return None
        if self.anchor_type == 'WEEK':
            if not is_cycle(self.anchor_date, day, self.repeat_period):
                return None
        return BoundTemplate(
            staff_member=staff,
            template_id=self.template_id,
            anchor_date=day,
            template_entries=tuple(BoundTemplateEntry(
                date=day+timedelta(days=te.date_offset),
                session=te.session,
                tag=te.tag) for te in self.template_entries
            ))


class BoundTemplateKey(NamedTuple):
    "namedtuple for internal use"
    staff: str
    day: date
    session: str
    tag: str


class TemplateConstraint(BaseConstraintConfig):
    "applies templates to rota"
    dutystore: DutyStore[BoundTemplate]
    templates: list[Template]

    def configure(self):
        self.templates = []
        # TODO: implement loading config

    def apply_constraint(self):
        core_duties = CoreDuties.from_context(self.ctx)
        core = self.ctx.core_config
        bound_templates: dict[BoundTemplateKey, set[BoundTemplate]] = {}
        self.dutystore = DutyStore(self.ctx.model)
        for day in core.days:
            for template in self.templates:
                for staff in template.staff_members:
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
                            self.model.Add(
                                sum(self.dutystore[bound] for bound in bound_templates[key]) > 0)
                        else:
                            self.model.Add(core_duties.allocated_for_duty(
                                shift, day, staff, tag) == 0)
