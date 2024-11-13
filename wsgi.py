from rotaplanner.app import app, db
from rotaplanner.activities.models import (
    Activity,
    Staff,
    StaffAssignment,
    Location,
)
from flask import Blueprint, render_template, current_app
from rotaplanner.activities.endpoints import blueprint as sched_blueprint
import datetime
import sys
import uuid
import webbrowser


@app.cli.command("initdb")
def create_db():
    db.create_all()


@app.cli.command("templates")
def templates():
    app.jinja_env.compile_templates("compiled", zip=None)


@app.cli.command("testdata")
def create_test_data():

    staff = {
        name: Staff(id=uuid.uuid4(), name=name, skills="")
        for name in ("Adam", "Bob", "Charlie", "Dave")
    }
    locations = {
        "Th4": Location(id=uuid.uuid4(), name="Theatre 4"),
        "Th5": Location(id=uuid.uuid4(), name="Theatre 5"),
    }
    activities = [
        Activity(
            id=uuid.uuid4(),
            name="Urology",
            location=locations["Th4"],
            activity_start=datetime.datetime(2024, 1, 1, 12, 0),
            activity_finish=datetime.datetime(2024, 1, 1, 17, 0),
        ),
        Activity(
            id=uuid.uuid4(),
            name="ENT",
            location=locations["Th5"],
            activity_start=datetime.datetime(2024, 1, 1, 12, 0),
            activity_finish=datetime.datetime(2024, 1, 1, 17, 0),
        ),
    ]
    staff["Adam"].assignments.append(StaffAssignment(activity=activities[0]))
    for v in staff.values():
        db.session.add(v)
    for a in activities:
        db.session.add(a)
    db.session.commit()


app.register_blueprint(
    sched_blueprint,
    url_prefix="/activities",
)


@app.get("/shutdown")
def quit():
    raise KeyboardInterrupt


@app.get("/sidebar.html")
def home():
    return render_template("sidebar.html", name="world")


from threading import Timer

if __name__ == "__main__":
    # Timer(5, lambda: webbrowser.open("http://localhost:5000")).start()
    app.run(debug=True)
