from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from rotaplanner.database import Connection


from rotaplanner.utils import get_locations

router = APIRouter()

"""
class RequirementForm(Form):

    skills = SelectMultipleField("Skills", choices=())
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


class StaffAllocationForm(Form):
    staff_id = SelectField("Staff", choices=())
    attendance = IntegerField(
        "Attendance",
        default=100,
        validators=[NumberRange(0, 100)],
        description="Will usually be 100%",
    )


class EditActivityForm(Form):
    activity_id = HiddenField()
    name = StringField("Activity Name", validators=[InputRequired()])
    activity_tags = SelectMultipleField("Tags")
    start_time = DateTimeLocalField("Start time")
    finish_time = DateTimeLocalField("Finish Time")

    location = SelectField(choices=())
    requirements = FieldList(FormField(RequirementForm), min_entries=1, max_entries=10)


def recurse(value):

    yield value
    try:
        i = iter(value)
    except TypeError:
        return
    for x in i:
        yield from recurse(x)

"""


@router.get("/create_new_activity")
def create_new_activity(
    request: Request,
    connection: Connection,
    staff_id: str = None,
    location_id: str = None,
    date: str = None,
):
    form = EditActivityForm(data={"staff_id": staff_id, "location": location_id})
    form.location.choices = [
        (location.id, location.name) for location in get_locations(connection).values()
    ]
    form.activity_tags.choices = [
        (location.id, location.name) for location in get_locations(connection).values()
    ]
    form.validate()
    errors = {}
    for f in recurse(form):
        try:
            if isinstance(f.name, str):
                errors.setdefault(f.name, []).extend(f.errors)
        except AttributeError:
            pass
    print(errors)
    return templates.TemplateResponse(
        "edit_activity_template.html.mako",
        {"form": form, "request": request},
        media_type="text/vnd.turbo-stream.html",
    )


@router.get("/edit_activity_add_requirement")
def edit_activity_add_requirement(
    after: str,
):
    root, index = after.rsplit("-", 1)
    index = int(index) + 1
    form = RequirementForm(prefix=f"{root}-{index}-")
    return HTMLResponse(
        templates.get_template("edit_activity_template.html.mako")
        .get_def("new_requirement_form")
        .render(old_ref=after, new_ref=f"{root}-{index}", req=form),
        media_type="text/vnd.turbo-stream.html",
    )
