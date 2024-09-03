from flask import Blueprint,render_template
from flask_pydantic import validate
from .queries import GetActivitiesRequest,GetActivitiesResponse,get_activities
from py_rotaplanner.database import db
from sqlmodel import Session
import datetime

blueprint=Blueprint('activities',__name__)

@blueprint.post('/assignments')
@validate()
def get_assignments(body:GetActivitiesRequest)->GetActivitiesResponse:
    with Session(db.engine) as session:
        return get_activities(session,body)
    
@blueprint.get('/table')
@validate()
def draw_table(query:GetActivitiesRequest):
    with Session(db.engine) as session:
        names=['adam','bob','charlie','dave']
        activities=get_activities(session,query)
        print(activities)
        dates=[datetime.date(2024,1,1)+datetime.timedelta(days=d) for d in range(1000)]
        for d in dates:
            print(activities.root.get(d))
        return render_template('table.j2',names=names,activities=activities.root,dates=dates)