"Api requests and responses"

import datetime
import itertools
import uuid

from models import Activity, Requirement, Staff, StaffAssignment
from pydantic import BaseModel, Field, RootModel
from sqlalchemy import func, select


class StaffApi(BaseModel):
    "response"
    id:uuid.UUID
    name:str

class StaffApiWithAssignments(StaffApi):
    "response"
    assignments:list['AssignmentWithActivity']

class AssignmentApi(BaseModel):
    "staff assignment"
    tags:str=Field(default="")
    start_time:datetime.datetime|None
    finish_time:datetime.datetime|None

class AssignmentWithStaff(AssignmentApi):
    "response"
    staff:StaffApi

class ActivityApi(BaseModel):
    "response class for concrete activity"
    activity_id:uuid.UUID
    template_id:uuid.UUID
    name:str|None
    location:str
    activity_start:datetime.datetime
    activity_finish:datetime.datetime


class AssignmentWithActivity(AssignmentApi):
    "response"
    activity:ActivityApi
    def model_post_init(self,_):
        if self.start_time is None:
            self.start_time=self.activity.activity_start
        if self.finish_time is None:
            self.finish_time=self.activity.activity_finish
class AssignmentWithStaffAndActivity(AssignmentWithStaff,AssignmentWithActivity):
    "response"


RequirementList=RootModel[list[tuple[Requirement]]]


class ActivityApiWithAssignments(ActivityApi):
    "response"
    staff_assignments:list[AssignmentWithStaff]

AssignmentsDict=RootModel[dict[datetime.date,dict[uuid.UUID,list[AssignmentApi]]]]

class ActivitiesByDateAndPersionApi(BaseModel):
    "response"
    activities:dict[uuid.UUID,ActivityApi]
    assignments:AssignmentsDict

class GetActivitiesRequest(BaseModel):
    "request"
    start_date:datetime.date
    finish_date:datetime.date

def get_activities(sess,start_date,finish_date) ->ActivitiesByDateAndPersionApi:
    "get activities and assignments for date range"
    request=GetActivitiesRequest(start_date=start_date,finish_date=finish_date)
    activities_query=select(Activity)
    assignments_query=(
        select(func.date(Activity.activity_start),StaffAssignment.staff_id,StaffAssignment)
            .join(Staff)
            .join(Activity)
            .where(func.date(Activity.activity_start)>=request.start_date)
            .where(func.date(Activity.activity_start)<=request.finish_date)
            .order_by(func.date(Activity.activity_start,StaffAssignment.staff_id)
    ))

    activities={act.activity_id:act for act in sess.exec(activities_query)}
    assignments={date:{staffname:list(d[2] for d in duties)
        for staffname,duties in itertools.groupby(rest,lambda k:k[1])}
        for date,rest in itertools.groupby(sess.exec(assignments_query),lambda k:k[0])}
    response=ActivitiesByDateAndPersionApi.model_validate(
        {'activities':activities,
         'assignments':assignments},from_attributes=True)
    return response
