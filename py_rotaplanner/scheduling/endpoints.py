from flask import Blueprint,request
from .database import get_assigned_activities
import datetime
blueprint=Blueprint('scheduling',__name__)

@blueprint.get('/names')
def get_names():
  return 'Adam Bob Charlie Dave'.split()

@blueprint.get('/possible_activities')
def possible_activities():
  start_date=datetime.date(2024,1,1)+datetime.timedelta(days=int(request.args['start']))
  finish_date=datetime.date(2024,1,1)+datetime.timedelta(days=int(request.args['finish'])+1)
  activities=get_assigned_activities(start_date,finish_date)
  act_by_day={}
  for (day,name),value in activities.items():
    act_by_day.setdefault(day,set()).update(value)
  print(act_by_day,activities,start_date,finish_date)
  possible_activities=set.intersection(*act_by_day.values())
  return sorted(possible_activities)

@blueprint.post('/add_activity')
def add_activity():
  print(request.get_json())
  return {}

@blueprint.get('/assigned_activities')
def assigned_activities():
  page=request.args['page']
  start_date=datetime.date(2024,1,1)+datetime.timedelta(days=int(page)*7)
  finish_date=start_date+datetime.timedelta(days=7)
  activities=get_assigned_activities(start_date,finish_date)
  result=[]
  for a in (0,1,2,3,4,5,6):
    thisrow={}
    for name in [None,*get_names()]:
      thisrow[name or ""]=list(activities.get((start_date+datetime.timedelta(days=a),name),['-']))
    thisrow['date']=(start_date+datetime.timedelta(days=a)).isoformat()
    result.append(thisrow)
  
  return result
