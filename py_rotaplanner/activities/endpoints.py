from flask import Blueprint, render_template, request
from flask_pydantic import validate
from .queries import (
    GetActivitiesRequest,
    GetActivitiesResponse,
    get_activities,
    reallocate_staff,
    DragDropHandlerRequest,
    get_staff,
)
from py_rotaplanner.database import db
from sqlmodel import Session
import datetime
import json
from flask_wtf import FlaskForm
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
)
from wtforms.validators import NumberRange
from py_rotaplanner.date_rules import GroupType, RuleType, RuleGroup, DailyRule
from .models import ActivityTemplate
import uuid

blueprint = Blueprint("activities", __name__)


@blueprint.get("/table")
@validate()
def table(query: GetActivitiesRequest):
    with Session(db.engine) as session:
        staff = get_staff(session)
        activities = get_activities(session, query)
        dates = [
            datetime.date(2024, 1, 1) + datetime.timedelta(days=d) for d in range(1000)
        ]
        return render_template(
            "table.html",
            staff=staff,
            activities=activities.root,
            dates=dates,
            errors=[],
        )


@blueprint.post("/reallocate")
@validate()
def reallocate(body: DragDropHandlerRequest):
    dates = []
    activities = {}
    with Session(db.engine) as session:
        dates, errors = reallocate_staff(session, body)
        if len(errors) == 0:
            session.commit()
        else:
            session.rollback()
        staff = get_staff(session)
        activities = get_activities(session, GetActivitiesRequest())
        return render_template(
            "table.html",
            staff=staff,
            activities=activities.root,
            dates=dates,
            errors=errors,
        ), (200 if len(errors) == 0 else 422)


@blueprint.get("/activity_templates")
def activity_templates():
    return render_template("activity_templates.html", templates=list(range(100)))


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


class RuleForm(FlaskForm):
    rule_type = SelectField(
        label="Rule Type",
        choices=[
            (RuleType.DAILY, "daily"),
            (RuleType.WEEKLY, "weekly"),
            (RuleType.MONTHLY, "day-in-month"),
            (RuleType.WEEK_IN_MONTH, "week-in-month"),
            (RuleType.DATE_RANGE, "date-range"),
            (RuleType.DATE_TAGS, "date-tag"),
        ],
        validate_choice=False,
        render_kw={"class": "rule-type"},
    )
    group_type = SelectField(
        label="Group Type",
        choices=(
            (GroupType.AND, "All must match"),
            (GroupType.OR, "Any must match"),
            (GroupType.NOT, "None must match"),
        ),
        render_kw={"class": "group-type"},
    )
    day_interval = SelectField(
        label="Frequency",
        choices=[(1, "Every day")]
        + [(i, f"every {ordinal(i)} day") for i in range(2, 31)],
        render_kw={"class": "day-interval"},
    )
    week_interval = SelectField(
        label="Frequency",
        choices=[(1, "Every week")]
        + [(i, f"every {ordinal(i)} week") for i in range(2, 53)],
        render_kw={"class": "week-interval"},
    )
    month_interval = SelectField(
        label="Frequency",
        choices=[(1, "Every month")]
        + [(i, f"every {ordinal(i)} month") for i in range(2, 31)],
        render_kw={"class": "month-interval"},
    )
    anchor_date = DateField("Start date", default=datetime.date.today())
    description = StringField()
    is_deleted = BooleanField(render_kw={"up-validate": True})
    is_open = BooleanField()

    def validate_should_add_group(self, field: BooleanField):
        print("validate_should_add_group", self, field.data)
        if field.data:
            self.members.append_entry({"rule_type": "group"})
        field.data = False

    should_add_rule = BooleanField(render_kw={"up-validate": True})

    def validate_should_add_rule(self, field: BooleanField):
        if field.data:
            self.members.append_entry({"rule_type": "daily", "is_open": True})
        field.data = False


RuleForm.members = FieldList(FormField(RuleForm), "Rules")


class RequirementForm(FlaskForm):
    skills = SelectMultipleField("Skills", choices=("SDM", "IAC", "Paeds"))
    allow_promotion = BooleanField(
        "Allow promotion", description="allow promotion with appropriate supervision"
    )
    attendance = IntegerField("Attendance", description="Will usually be 100%")
    geofence = SelectField(
        "Geofence (if attendance not 100%)",
        choices=["Main theatre", "Day surgery", "Whole hospital", "Remote"],
    )


class Autonomy(FlaskForm):
    skill = SelectField("Skill", choices=["SDM", "IAC", "Paeds"])
    autonomy_level = IntegerField("Autonomy level")
    is_supervisor = BooleanField("Can supervise")


class EditActivityForm(FlaskForm):
    id = HiddenField()
    ruleset = FormField(RuleForm)
    activity_name = StringField("Activity Name")
    activity_tags = SelectMultipleField("Tags", choices=[(1, "One"), (2, "Two")])
    start_time = TimeField("Start time")
    duration = TimeField("Duration")
    location = StringField("Location")
    requirements = FormField(RequirementForm)


@blueprint.route("/edit_activity_template", methods=["GET", "POST"])
def edit_activity_template():
    def_activity = ActivityTemplate(
        id=uuid.uuid4(),
        name="New activity",
        activity_tags=set(),
        ruleset=RuleGroup(
            group_type="and",
            members=[DailyRule(day_interval=1, anchor_date=datetime.date.today())],
        ),
        start_time=datetime.time(9),
        duration=datetime.timedelta(hours=8),
        location="Theatre 1",
    )
    form: EditActivityForm = EditActivityForm(obj=def_activity)
    form.validate_on_submit()
    return render_template(
        "edit_activity_template.html",
        form=form,
        now=datetime.datetime.today().isoformat(),
    )
