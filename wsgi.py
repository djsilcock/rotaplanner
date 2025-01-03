from rotaplanner.app import app, db
from rotaplanner.activities.models import (
    Activity,
    Staff,
    StaffAssignment,
    Location,
)
from flask import Blueprint, render_template, current_app, redirect
from rotaplanner.activities.endpoints import blueprint as sched_blueprint
import datetime
import sys
from uuid import UUID
import webbrowser
import pathlib


@app.cli.command("initdb")
def create_db():
    db.create_all()


@app.cli.command("templates")
def templates():
    app.jinja_env.compile_templates("compiled", zip=None)


@app.cli.command("testdata")
def test_data():
    create_test_data()


def create_test_data():

    staff = {
        "Adam": Staff(
            id=UUID("c80b76f3-6e6d-4c8a-8cae-844c77a3e091"), name="Adam", skills=[]
        ),
        "Bob": Staff(
            id=UUID("166ff3c6-66ff-4212-b0a7-bc53d48a47a2"), name="Bob", skills=[]
        ),
        "Charlie": Staff(
            id=UUID("a814a428-89e1-48fe-88fc-d727e4d3f27f"), name="Charlie", skills=[]
        ),
        "Dave": Staff(
            id=UUID("128467bc-8b51-4249-a763-27ff85bbd3ec"), name="Dave", skills=[]
        ),
    }
    locations = {
        "Th4": Location(
            id=UUID("a9fcfd5b-1aed-4cd2-b879-ae140ea4681d"), name="Theatre 4"
        ),
        "Th5": Location(
            id=UUID("6be6bcbe-733f-4169-a830-d995a4bac6cc"), name="Theatre 5"
        ),
    }
    activities = [
        Activity(
            id=UUID("8b168c55-db64-46a8-87f9-0174267b21b3"),
            name="Urology",
            location=locations["Th4"],
            activity_start=datetime.datetime(2024, 1, 1, 12, 0),
            activity_finish=datetime.datetime(2024, 1, 1, 17, 0),
        ),
        Activity(
            id=UUID("87d5dc36-b91b-4102-ba92-244de1fcd6cc"),
            name="ENT",
            location=locations["Th5"],
            activity_start=datetime.datetime(2024, 1, 1, 12, 0),
            activity_finish=datetime.datetime(2024, 1, 1, 17, 0),
        ),
    ]

    for v in staff.values():
        db.session.merge(v)
    for l in locations.values():
        db.session.merge(l)
    staff["Adam"].assignments.append(StaffAssignment(activity=activities[0]))
    for a in activities:
        db.session.merge(a)
    db.session.commit()


@app.cli.command("resetdb")
def reset_db():
    db.drop_all()
    db.create_all()
    create_test_data()


app.register_blueprint(
    sched_blueprint,
    url_prefix="/activities",
)


@app.get("/shutdown")
def quit():
    raise KeyboardInterrupt


@app.get("/sidebar")
def sidebar():
    return render_template("sidebar.html.j2")


@app.get("/")
def home():
    return redirect("/site/index.html")


print(app.root_path)
from threading import Timer

if __name__ == "__main__":

    # Timer(5, lambda: webbrowser.open("http://localhost:5000")).start()
    app.run(debug=True)
