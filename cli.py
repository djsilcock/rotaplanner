from rotaplanner.models import (
    Activity,
    ActivityType,
    Staff,
    StaffAssignment,
    Location,
    RequirementGroup,
    RequirementType,
)
import rotaplanner

import datetime
import sys
from uuid import UUID
import webbrowser
import pathlib
import importlib
import typer
from sqlmodel import SQLModel, Session
from rotaplanner.database import engine

app = typer.Typer()


@app.command()
def create_db():
    SQLModel.metadata.create_all(engine)


@app.command()
def test_data():

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
            type=ActivityType.CONCRETE,
            name="Urology",
            location=locations["Th4"],
            activity_start=datetime.datetime(2024, 1, 1, 12, 0),
            activity_finish=datetime.datetime(2024, 1, 1, 17, 0),
            requirements=RequirementGroup(
                rule_or_group="group", group_type=RequirementType.AND, requirements=[]
            ),
        ),
        Activity(
            id=UUID("87d5dc36-b91b-4102-ba92-244de1fcd6cc"),
            type=ActivityType.CONCRETE,
            name="ENT",
            location=locations["Th5"],
            activity_start=datetime.datetime(2024, 1, 1, 12, 0),
            activity_finish=datetime.datetime(2024, 1, 1, 17, 0),
            requirements=RequirementGroup(
                rule_or_group="group", group_type=RequirementType.AND, requirements=[]
            ),
        ),
    ]
    with Session(engine) as session:
        for v in staff.values():
            session.merge(v)
        for l in locations.values():
            session.merge(l)
        staff["Adam"].assignments.append(StaffAssignment(activity=activities[0]))
        for a in activities:
            session.merge(a)
        session.commit()


@app.command()
def reset_db():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


if __name__ == "__main__":
    app()
