from flask import Blueprint,render_template
from flask_pydantic import validate
from .queries import GetActivitiesRequest,GetActivitiesResponse,get_activities,reallocate_staff,DragDropHandlerRequest,get_staff
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
        staff=get_staff(session)
        activities=get_activities(session,query)
        dates=[datetime.date(2024,1,1)+datetime.timedelta(days=d) for d in range(1000)]
        return render_template('table.html',staff=staff,activities=activities.root,dates=dates,as_template=False)
    
@blueprint.post('/reallocate')
@validate()
def reallocate(body:DragDropHandlerRequest):
    print(body)
    dates=[]
    activities={}
    with Session(db.engine) as session:
        dates=reallocate_staff(session,body)
        session.commit()
        staff=get_staff(session)
        activities=get_activities(session,GetActivitiesRequest())
        
    return render_template('table.html',staff=staff,activities=activities.root,dates=dates,as_template=True)