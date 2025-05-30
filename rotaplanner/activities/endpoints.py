from flask import Blueprint, render_template, request, redirect, url_for
from flask_pydantic import validate
from .queries import (
    GetActivitiesRequest,
    ReallocateStaff,
    ReallocateActivity,
    get_activities,
    reallocate_staff as do_reallocate_staff,
    reallocate_activity as do_reallocate_activity,
    get_staff,
    get_locations,
    get_daterange,
)
from ..utils import get_instance_fields
from rotaplanner.database import db
from scrapyard.flask_unpoly import unpoly
import datetime
from flask_wtf import FlaskForm
from wtforms import widgets
from wtforms import (
    StringField,
    SelectField,
    FieldList,
    FormField,
    DateField,
    HiddenField,
    SelectMultipleField,
    TimeField,
    BooleanField,
    IntegerField,
    IntegerRangeField,
    Field,
)

from wtforms_sqlalchemy.fields import QuerySelectField, QuerySelectMultipleField

from wtforms.validators import (
    NumberRange,
    StopValidation,
    ValidationError,
    DataRequired,
    Optional,
    UUID as ValidateUUID,
)
from rotaplanner.date_rules import (
    Rule,
    GroupType,
    RuleType,
    RuleGroup,
    DateType,
    DateTag,
)
from ..models import ActivityTemplate, Location, Requirement, ActivityTag, Skill
import uuid
from typing import Any, Self, Sequence
from rotaplanner.utils import discard_extra_kwargs
from sqlalchemy import inspect, select


blueprint = Blueprint("activities", __name__)


class DerivedField(Field):
    def __init__(
        self,
        label: str | None = None,
        validators=None,
        filters=...,
        description: str = "",
        id: str | None = None,
        default: object | None = None,
        widget=None,
        render_kw: dict[str, Any] | None = None,
        name: str | None = None,
        _form=None,
        _prefix: str = "",
        _translations=None,
        _meta=None,
        derivation=None,
    ) -> None:
        super().__init__(
            label,
            validators,
            filters,
            description,
            id,
            default,
            widget,
            render_kw,
            name,
            _form,
            _prefix,
            _translations,
            _meta,
        )
        self.form = _form
        assert callable(derivation)
        self.derivation = derivation

    @property
    def data(self):
        return self.derivation(self.form)


def daterange(start_date, finish_date):
    d = start_date
    while d <= finish_date:
        yield d
        d += datetime.timedelta(days=1)


@blueprint.get("/table/staff")
def table_by_staff():
    return table("staff")


@blueprint.get("/table/location")
def table_by_location():
    return table("location")


def get_row_headers(y):
    if y == "staff":
        y_axis = get_staff()
    elif y == "location":
        y_axis = get_locations()
    else:
        raise ValueError
    return y_axis


def table(y):
    row_headings = get_row_headers(y)
    begin_date, end_date = get_daterange()
    today = datetime.date.today().toordinal()

    return render_template(
        "table.html.j2",
        y_axis=row_headings,
        errors=[],
        table_info={
            "first": min(begin_date.toordinal(), today),
            "last": max(end_date.toordinal(), today),
            "today": today,
            "yAxis": y,
        },
    )


@blueprint.get("/rota_segment")
def table_segment():
    staff = get_staff()
    query = discard_extra_kwargs(GetActivitiesRequest, request.args)
    activities = get_activities(query)
    min_date, max_date = get_daterange()
    dates = list(daterange(query.start_date, query.finish_date))
    return render_template(
        "rota_segment.html.j2",
        y_axis=staff,
        activities=activities,
        dates=dates,
        errors=[],
        begin_ordinal=0,
        end_ordinal=700000,
        is_prepend=(query.finish_date < min_date),
        is_append=(query.start_date > max_date),
    )


"""
class Activity(ActivityBase):
    "concrete activity class"
    __mapper_args__ = {"polymorphic_identity": "concrete"}
    id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("activity_base.id"), primary_key=True
    )
    activity_start: Mapped[datetime.datetime]
    activity_finish: Mapped[datetime.datetime]
    template_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("activity_template.id")
    )
    staff_assignments: Mapped[list["StaffAssignment"]] = relationship()


class StaffAssignment(db.Model):
    "staff assignment"
    activity_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("activity.id"), primary_key=True
    )
    staff_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("staff.id"), primary_key=True
    )
    activity: Mapped["Activity"] = relationship(back_populates="staff_assignments")
    staff: Mapped[Staff] = relationship(back_populates="assignments")
    attendance: Mapped[int] = 100
    staff: Mapped[Staff] = relationship()
    tags: Mapped[list[AssignmentTag]] = relationship(
        secondary=AssignmentTagAssoc.__table__
    )
    start_time: Mapped[datetime.datetime | None]
    finish_time: Mapped[datetime.datetime | None]
"""


@blueprint.post("/by_date")
def table_by_date(dates=None, include_all=False):
    if dates is None:
        dates = [datetime.date.fromisoformat(d) for d in request.json.get("dates")]
    query = GetActivitiesRequest(start_date=min(dates), finish_date=max(dates))
    activities = get_activities(query)
    print(activities)
    return [
        {
            "date": activity_date.isoformat(),
            "activities": [
                {
                    "id": str(activity.id),
                    "name": activity.name,
                    "start_time": activity.activity_start.time().hour,
                    "finish_time": activity.activity_finish.time().hour,
                    "location": activity.location
                    and {
                        "id": activity.location.id,
                        "name": activity.location.name,
                    },
                    "staff_assignments": [
                        {
                            "staff": {
                                "id": str(assn.staff.id),
                                "name": assn.staff.name,
                            }
                        }
                        for assn in activity.staff_assignments
                    ],
                }
                for activity in activities.get(activity_date, [])
            ],
        }
        for activity_date in (dates if include_all else activities)
    ]


def nullable_UUID(data):
    try:
        return uuid.UUID(data)
    except (ValueError, TypeError):
        return None


class ReallocateStaffForm(FlaskForm):
    staff = HiddenField(filters=[uuid.UUID])
    initialactivity = HiddenField(filters=[uuid.UUID])
    newactivity = HiddenField(filters=[uuid.UUID])


class ReallocateActivitySubForm(FlaskForm):
    activityid = HiddenField(filters=[uuid.UUID])
    initialstaff = HiddenField(filters=[nullable_UUID])
    newstaff = HiddenField(filters=[nullable_UUID])
    newdate = DateField()


class ReallocateActivityForm(FlaskForm):
    entries = FieldList(
        FormField(ReallocateActivitySubForm, default=ReallocateActivity)
    )


@blueprint.post("/reallocate_activity")
def reallocate_activity():
    query = ReallocateActivity(**request.json)

    dates, error = do_reallocate_activity(query)
    if error is None:
        db.session.commit()
    else:
        db.session.rollback()

    return {
        "error": error,
        "status": "error" if error else "ok",
        "data": table_by_date(dates=dates, include_all=True),
    }


@blueprint.post("/reallocate_staff")
def reallocate_staff():
    form2 = ReallocateStaffForm()
    form2.validate_on_submit()

    if form2.staff.data:
        obj = ReallocateStaff()
        form2.populate_obj(obj)
        dates, errors = do_reallocate_staff(obj)
        template_name = "table_by_location.html"
    else:
        dates = []
        errors = ["THere is a problem with the form"]
    if len(errors) == 0:
        db.session.commit()
    else:
        db.session.rollback()
    staff = get_staff()
    activities = get_activities(GetActivitiesRequest())
    locations = get_locations()

    return render_template(
        "table_by_location.html",
        staff=staff,
        activities=activities,
        locations=locations,
        dates=dates,
        errors=errors,
    ), (200 if len(errors) == 0 else 422)


def get_activity_templates():
    return db.session.scalars(select(ActivityTemplate))


@blueprint.get("/activity_templates")
def activity_templates():
    return render_template(
        "activity_templates.html",
        templates=get_activity_templates(),
        new_template_id=uuid.uuid4(),
    )


def ordinal(index):
    if (index % 100 > 3) and (index % 100 < 21):
        return f"{index}th"
    elif index % 10 == 1:
        return f"{index}st"
    elif index % 10 == 2:
        return f"{index}nd"
    elif index % 10 == 3:
        return f"{index}rd"
    else:
        return f"{index}th"


class OnlyForRuleType:
    def __init__(self, *rule_types):
        self.rule_types = rule_types
        self.field_flags = {"usf": " ".join(rule_types)}

    def __call__(self, form: FlaskForm, field):
        if form.rule_type.data not in self.rule_types:
            field.errors[:] = []
            raise StopValidation


class SwitchingSelectField(SelectField):
    def __call__(self, **kwargs):
        kwargs.setdefault("up-switch", f".rule-box:has(#{self.id}) [up-show-for]")
        return super().__call__(**kwargs)


def get_date_tags():
    return db.session.scalars(select(DateTag))


class RuleForm(FlaskForm):
    rule_id = HiddenField(name="id", default=uuid.uuid4)
    rule_type = SwitchingSelectField(
        label="Rule Type",
        choices=[
            (RuleType.DAILY, "Every n days"),
            (RuleType.WEEKLY, "Every n weeks"),
            (RuleType.MONTHLY, "Nth day of month"),
            (RuleType.WEEK_IN_MONTH, "Nth week of month"),
            (RuleType.DATE_RANGE, "Date Range"),
            (RuleType.DATE_TAGS, "Date Tags"),
        ],
        validate_choice=True,
        render_kw={
            "class": "rule-type",
        },
    )
    day_interval = SelectField(
        label="Frequency",
        choices=[(1, "every day")]
        + [(i, f"every {ordinal(i)} day") for i in range(2, 31)],
        validators=[OnlyForRuleType(RuleType.DAILY)],
        render_kw={"class": "day-interval"},
    )
    week_interval = SelectField(
        label="Frequency",
        choices=[(1, "every week")]
        + [(i, f"every {ordinal(i)} week") for i in range(2, 53)],
        validators=[OnlyForRuleType(RuleType.WEEKLY)],
        render_kw={"class": "week-interval"},
    )
    month_interval = SelectField(
        label="Frequency",
        choices=[(1, "every month")]
        + [(i, f"every {ordinal(i)} month") for i in range(2, 31)],
        validators=[OnlyForRuleType(RuleType.MONTHLY, RuleType.WEEK_IN_MONTH)],
        render_kw={"class": "month-interval"},
    )
    tag = QuerySelectField(
        label="Tags",
        validators=[OnlyForRuleType(RuleType.DATE_TAGS)],
        query_factory=get_date_tags,
        get_label="name",
    )
    date_type = SelectField(
        "Type",
        choices=[
            (DateType.INCLUSIVE, "Include dates"),
            (DateType.EXCLUSIVE, "Exclude dates"),
        ],
        validators=[OnlyForRuleType(RuleType.DATE_RANGE, RuleType.DATE_TAGS)],
    )
    start_date = DateField(
        "Start date",
        default=datetime.date.today(),
    )
    finish_date = DateField(
        "Finish date", default=datetime.date(2099, 12, 31), validators=[Optional()]
    )
    is_deleted = BooleanField("Delete rule", render_kw={"up-validate": True})
    is_open = BooleanField(render_kw={"class": "is-open"})


class RuleGroupForm(FlaskForm):
    id = HiddenField(default=uuid.uuid4)
    group_type = SelectField(
        label="Group Type",
        choices=(
            (GroupType.AND, "All must match"),
            (GroupType.OR, "Any must match"),
            (GroupType.NOT, "None must match"),
        ),
        render_kw={"class": "group-type"},
        default=GroupType.AND,
    )
    rules = FieldList(FormField(RuleForm, default=Rule), "Rules")
    should_add_group = BooleanField("Add group", render_kw={"up-validate": True})
    is_deleted = BooleanField("Delete group", render_kw={"up-validate": True})

    def validate_should_add_group(self, field: BooleanField):
        if field.data:
            self.groups.append_entry()
        field.data = False

    should_add_rule = BooleanField(render_kw={"up-validate": True})

    def validate_should_add_rule(self, field: BooleanField):
        if field.data:
            self.rules.append_entry({"rule_type": "daily", "is_open": True})
        field.data = False

    def validate_rules(self, field):
        field.entries = [f for f in field.entries if not f.data["is_deleted"]]

    def validate_groups(self, field):
        field.entries = [f for f in field.entries if not f.data["is_deleted"]]


RuleGroupForm.groups = FieldList(FormField(RuleGroupForm, default=RuleGroup), "Groups")


def get_skills():
    return db.session.scalars(select(Skill))


class RequirementForm(FlaskForm):
    req_id = HiddenField(name="id", default=uuid.uuid4)
    skills = QuerySelectMultipleField(
        "Skills", query_factory=get_skills, get_label="name"
    )
    requirement = IntegerField(
        "Required people", default=1, validators=[NumberRange(min=0)]
    )
    optional = IntegerField(
        "Optional additional people", default=0, validators=[NumberRange(min=0)]
    )
    attendance = IntegerField(
        "Attendance",
        default=100,
        validators=[NumberRange(0, 100)],
        description="Will usually be 100%",
    )
    geofence = SelectField(
        "Geofence (if attendance not 100%)",
        default="_immediate",
        choices=[
            ("_immediate", "Local location"),
            ("main", "Main theatre"),
            ("dsu", "Day surgery"),
            ("hosp", "Whole hospital"),
            ("remote", "Remote"),
        ],
    )

    is_deleted = BooleanField("Delete requirement")
    is_open = BooleanField(render_kw={"class": "is-open"})


class Autonomy(FlaskForm):
    skill = SelectField("Skill", choices=["SDM", "IAC", "Paeds"])
    autonomy_level = IntegerField("Autonomy level")
    is_supervisor = BooleanField("Can supervise")


def ensure_uuid(val):
    if isinstance(val, str):
        return uuid.UUID(val)
    return val


def get_tags():
    return db.session.scalars(select(ActivityTag))


class EditActivityTemplateForm(RuleGroupForm):
    id = HiddenField(filters=[ensure_uuid])
    name = StringField("Activity Name")
    activity_tags = QuerySelectMultipleField(
        "Tags", query_factory=get_tags, get_label="name"
    )
    start_time = TimeField("Start time")
    finish_time = TimeField("Finish Time")
    duration = TimeField("Duration")
    location = QuerySelectField(query_factory=get_locations, get_label="name")
    requirements = FieldList(FormField(RequirementForm, default=Requirement))
    should_add_requirement = BooleanField("Add requirement")

    def validate_should_add_requirement(self, field: BooleanField):
        print(self, field.data)
        if field.data:
            self.requirements.append_entry({"is_open": True})
        field.data = False

    def validate_requirements(self, field):
        field.entries = [f for f in field.entries if not f.data["is_deleted"]]


@blueprint.route("/edit_activity_template/<uuid:template_id>", methods=["GET", "POST"])
def edit_activity_template(template_id):
    def_activity = db.session.get(ActivityTemplate, template_id) or ActivityTemplate(
        id=template_id,
        name="New activity",
        activity_tags=[],
        group_type="and",
        start_time=datetime.time(9),
        finish_time=datetime.time(17),
    )
    form: EditActivityTemplateForm = EditActivityTemplateForm(obj=def_activity)
    print("validate on submit:", form.validate_on_submit(), form.errors)
    print("unpoly", unpoly().validate)

    if form.validate_on_submit() and not unpoly().validate:
        form.populate_obj(def_activity)
        print(get_instance_fields(def_activity))
        print(def_activity)
        print(form.data)
        db.session.merge(def_activity)
        db.session.commit()
        return redirect(url_for("activities.activity_templates"))
    return render_template(
        "edit_activity_template.html",
        form=form,
        now=datetime.datetime.today().isoformat(),
        rule_types=RuleType,
    )
