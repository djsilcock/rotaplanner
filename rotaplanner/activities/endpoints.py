from flask import Blueprint, render_template, request
from flask_pydantic import validate
from .queries import (
    GetActivitiesRequest,
    ReallocateStaff,
    ReallocateActivity,
    get_activities,
    reallocate_staff as do_reallocate_staff,
    reallocate_activities as do_reallocate_activities,
    get_staff,
    get_locations,
)
from rotaplanner.database import db
from flask_unpoly import unpoly
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
from wtforms.validators import (
    NumberRange,
    StopValidation,
    ValidationError,
    DataRequired,
    Optional,
    UUID as ValidateUUID,
)
from rotaplanner.date_rules import Rule, GroupType, RuleType, RuleGroup, DateType
from .models import ActivityTemplate
import uuid
from typing import Any, Self, Sequence
from rotaplanner.utils import discard_extra_kwargs
from sqlalchemy import inspect


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


@blueprint.get("/table")
def table():
    staff = get_staff(db.session)
    query = discard_extra_kwargs(GetActivitiesRequest, request.args)
    activities = get_activities(db.session, query)
    dates = [
        datetime.date(2024, 1, 1) + datetime.timedelta(days=d) for d in range(1000)
    ]
    return render_template(
        "table.html",
        staff=staff,
        activities=activities,
        dates=dates,
        errors=[],
    )


@blueprint.get("/table_by_location")
def table_by_location():
    locations = get_locations(db.session)
    query = discard_extra_kwargs(GetActivitiesRequest, request.args)
    activities = get_activities(db.session, query)
    dates = [
        datetime.date(2024, 1, 1) + datetime.timedelta(days=d) for d in range(1000)
    ]
    return render_template(
        "table_by_location.html",
        locations=locations,
        activities=activities,
        dates=dates,
        errors=[],
    )


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
    entries = FieldList(FormField(ReallocateActivitySubForm, default=ReallocateStaff))


@blueprint.post("/reallocate_activity")
def reallocate_activity():
    print(request.form)

    form1 = ReallocateActivityForm()
    form1.validate_on_submit()

    if form1.entries.data:
        obj = ReallocateActivity()
        form1.populate_obj(obj)
        dates, errors = do_reallocate_activities(db.session, obj.entries)
        template_name = "table.html"
    else:
        dates = []
        errors = ["THere is a problem with the form"]
    if len(errors) == 0:
        db.session.commit()
    else:
        db.session.rollback()
    staff = get_staff(db.session)
    activities = get_activities(db.session, GetActivitiesRequest())
    locations = get_locations(db.session)

    return render_template(
        "table.html",
        staff=staff,
        activities=activities,
        locations=locations,
        dates=dates,
        errors=errors,
    ), (200 if len(errors) == 0 else 422)


@blueprint.post("/reallocate_staff")
def reallocate_staff():
    form2 = ReallocateStaffForm()
    form2.validate_on_submit()

    if form2.staff.data:
        obj = ReallocateStaff()
        form2.populate_obj(obj)
        dates, errors = do_reallocate_staff(db.session, obj)
        template_name = "table_by_location.html"
    else:
        dates = []
        errors = ["THere is a problem with the form"]
    if len(errors) == 0:
        db.session.commit()
    else:
        db.session.rollback()
    staff = get_staff(db.session)
    activities = get_activities(db.session, GetActivitiesRequest())
    locations = get_locations(db.session)

    return render_template(
        "table_by_location.html",
        staff=staff,
        activities=activities,
        locations=locations,
        dates=dates,
        errors=errors,
    ), (200 if len(errors) == 0 else 422)


@blueprint.get("/activity_templates")
def activity_templates():
    return render_template(
        "activity_templates.html", templates=[uuid.uuid4() for r in range(100)]
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


class RuleForm(FlaskForm):
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
    tag = SelectMultipleField(
        label="Tags",
        choices=[],
        validators=[OnlyForRuleType(RuleType.DATE_TAGS)],
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
    is_deleted = BooleanField(render_kw={"up-validate": True})
    is_open = BooleanField(render_kw={"class": "is-open"})


class RuleGroupForm(FlaskForm):
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
    should_add_group = BooleanField(render_kw={"up-validate": True})
    is_deleted = BooleanField(render_kw={"up-validate": True})

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


class RequirementForm(FlaskForm):
    skills = SelectMultipleField("Skills", choices=("SDM", "IAC", "Paeds"))
    requirement = IntegerField(
        "Required people", default=1, validators=[NumberRange(min=0)]
    )
    optional = IntegerField(
        "Optional additional people", default=0, validators=[NumberRange(min=0)]
    )
    attendance = IntegerField(
        "Attendance",
        validators=[NumberRange(0, 100)],
        description="Will usually be 100%",
    )
    geofence = SelectField(
        "Geofence (if attendance not 100%)",
        choices=["Main theatre", "Day surgery", "Whole hospital", "Remote"],
    )

    is_deleted = BooleanField()
    is_open = BooleanField(render_kw={"class": "is-open"})


class Autonomy(FlaskForm):
    skill = SelectField("Skill", choices=["SDM", "IAC", "Paeds"])
    autonomy_level = IntegerField("Autonomy level")
    is_supervisor = BooleanField("Can supervise")


def ensure_uuid(val):
    if isinstance(val, str):
        return uuid.UUID(val)
    return val


class EditActivityForm(FlaskForm):
    id = HiddenField(filters=[ensure_uuid])
    ruleset = FormField(RuleGroupForm, default=RuleGroup)
    activity_name = StringField("Activity Name")
    activity_tags = SelectMultipleField("Tags", choices=[(1, "One"), (2, "Two")])
    start_time = TimeField("Start time")
    finish_time = TimeField("Finish Time")
    duration = TimeField("Duration")
    location = StringField("Location")
    # requirements = FieldList(FormField(RequirementForm, default=Requirement))
    should_add_requirement = BooleanField()

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
        id=uuid.uuid4(),
        name="New activity",
        # activity_tags=set(),
        ruleset=RuleGroup(
            group_type="and",
            rules=[
                Rule(
                    rule_type=RuleType.DAILY,
                    day_interval=1,
                    start_date=datetime.date.today(),
                )
            ],
        ),
        start_time=datetime.time(9),
        duration=datetime.timedelta(hours=8),
        # location="Theatre 1",
    )
    form: EditActivityForm = EditActivityForm(obj=def_activity)
    print("validate on submit:", form.validate_on_submit(), form.errors)
    print("unpoly", unpoly().validate)

    if form.validate_on_submit() and not unpoly().validate:
        form.populate_obj(def_activity)
        def_activity.activity_tags = " ".join(def_activity.activity_tags)
        for i in inspect(def_activity).attrs:
            print(i)
        print(def_activity)
        print(form.data)
        db.session.merge(def_activity)
        db.session.commit()
    return render_template(
        "edit_activity_template.html",
        form=form,
        now=datetime.datetime.today().isoformat(),
        rule_types=RuleType,
    )
