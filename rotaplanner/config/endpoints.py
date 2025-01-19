from flask import Blueprint
from rotaplanner.database import db
from flask import abort
from rotaplanner.models import (
    Activity,
    Staff,
    StaffAssignment,
    Location,
)

blueprint = Blueprint("config", __name__)


@blueprint.route("/rota-grid/<location_or_staff>")
def rota_grid(location_or_staff):
    config = {}
    if location_or_staff == "staff":
        all_staff = db.session.query(Staff).all()
        config["y_axis"] = [{"name": staff.name, "id": staff.id} for staff in all_staff]
    elif location_or_staff == "location":
        all_locations = db.session.query(Location).all()
        config["y_axis"] = [{"name": loc.name, "id": loc.id} for loc in all_locations]
    else:
        abort(404)
    config["date_range"] = {"start": "2024-01-01", "finish": "2024-12-31"}
    return config
