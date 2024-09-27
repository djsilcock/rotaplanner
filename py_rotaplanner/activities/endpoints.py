from flask import Blueprint,render_template,request
from flask_pydantic import validate
from .queries import GetActivitiesRequest,GetActivitiesResponse,get_activities,reallocate_staff,DragDropHandlerRequest,get_staff
from py_rotaplanner.database import db
from sqlmodel import Session
import datetime
import json
import string

blueprint=Blueprint('activities',__name__)

def unflatten(d:dict):
    root_value={}
    for key,value in request.form.items():
        path=key.split('.')
        final_key=path.pop()
        target=root_value
        for this_key in path:
            target=target.setdefault(this_key,{})
        target[final_key]=value
    def list_or_dict(obj):
        if isinstance(obj,(tuple,list)):
            return [list_or_dict(i) for i in obj]
        if not isinstance(obj,dict):
            return obj
        if not all(i.isdigit() for i in obj.keys()):
            return {k:list_or_dict(v) for k,v in obj.items()}
        return [obj.get(str(a)) for a in range(max(int(k) for k in obj.keys())+1)]
    return list_or_dict(root_value)
    

@blueprint.get('/table')
@validate()
def table(query:GetActivitiesRequest):
    with Session(db.engine) as session:
        staff=get_staff(session)
        activities=get_activities(session,query)
        dates=[datetime.date(2024,1,1)+datetime.timedelta(days=d) for d in range(1000)]
        return render_template('table.html',staff=staff,activities=activities.root,dates=dates,errors=[])
    
@blueprint.post('/reallocate')
@validate()
def reallocate(body:DragDropHandlerRequest):
    dates=[]
    activities={}
    with Session(db.engine) as session:
        dates,errors=reallocate_staff(session,body)
        if len(errors)==0:
            session.commit()
        else:
            session.rollback()
        staff=get_staff(session)
        activities=get_activities(session,GetActivitiesRequest())   
        return render_template('table.html',staff=staff,activities=activities.root,dates=dates,errors=errors),200 if len(errors)==0 else 422




@blueprint.get('/activity_templates')
def activity_templates():
    return render_template('activity_templates.html',templates=list(range(100)))

@blueprint.get('/edit_activity_template')
def edit_activity_template():
    return render_template('edit_activity_template.html',form={},ruleset={'id':'A','rule_type':'group','description':'All of','children':[{'id':'B','description':'every Monday','rule_type':'weekly','anchor_date':'1998-02-29'}]})

@blueprint.post('/edit_activity_template')
def edit_activity_template_post():
    print(json.dumps(unflatten(request.form),indent=2))
    return ""