from flask import Blueprint,request
from .database import get_assigned_activities,Activity,get_activities_for_date,assign_activity,unassign_activity
import datetime
blueprint=Blueprint('scheduling',__name__)

@blueprint.get('/names')
def get_names():
  return 'Adam Bob Charlie Dave'.split()

@blueprint.get('/possible_activities')
def possible_activities():
  start_date=datetime.date.fromisoformat(request.args['start'])
  finish_date=datetime.date.fromisoformat(request.args['finish'])+datetime.timedelta(days=1)
  activities=get_assigned_activities(start_date,finish_date)
  act_by_day={}
  for (day,name),activityset in activities.items():
    act_by_day.setdefault(day,set()).update(act.name for act in activityset)
  poss_activities=set.intersection(*act_by_day.values())
  return sorted(poss_activities)

@blueprint.post('/add_activity')
def add_activity():
  req=request.get_json()
  startdate=datetime.date.fromisoformat(req['key']['x1'])
  finishdate=datetime.date.fromisoformat(req['key']['x2'])
  days=(finishdate-startdate).days+1
  names=get_names()[int(req['key']['y1']):int(req['key']['y2'])+1]
  for d in range(days):
    this_date=startdate+datetime.timedelta(days=d)
    acts=[a for a in get_activities_for_date(this_date) if a.name==req['activity']]
    for n in names:
      for a in acts:
        assign_activity(n,a.id)
  return {}

@blueprint.post('/remove_activity')
def remove_activity():
  req=request.get_json()
  startdate=datetime.date.fromisoformat(req['key']['x1'])
  finishdate=datetime.date.fromisoformat(req['key']['x2'])
  days=(finishdate-startdate).days+1
  names=get_names()[int(req['key']['y1']):int(req['key']['y2'])+1]
  for d in range(days):
    this_date=startdate+datetime.timedelta(days=d)
    acts=[a for a in get_activities_for_date(this_date) if a.name==req['activity']]
    for n in names:
      for a in acts:
        unassign_activity(n,a.id)
  return {}


@blueprint.get('/assigned_activities')
def assigned_activities():
  page=request.args['page']
  start_date=datetime.date.fromisoformat(page+'-01')
  finish_date=start_date+datetime.timedelta(days=31)
  activities=get_assigned_activities(start_date,finish_date)
  result={}
  for a in range(31):
    thisrow={}
    for name in [None,*get_names()]:
      thisrow[name or ""]=list(act.name for act in activities.get((start_date+datetime.timedelta(days=a),name),[]))
    result[(start_date+datetime.timedelta(days=a)).isoformat()]=thisrow
  
  return result
