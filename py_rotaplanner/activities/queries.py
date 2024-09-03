"Api requests and responses"

import datetime
import itertools
import uuid

from .models import Activity, Requirement, Staff, StaffAssignment
from pydantic import BaseModel, Field, RootModel
from sqlalchemy import func, select


class StaffApi(BaseModel):
    "response"
    id:uuid.UUID
    name:str

class AssignmentWithStaff(BaseModel):
    "staff assignment"
    tags:str=Field(default="")
    start_time:datetime.datetime|None
    finish_time:datetime.datetime|None
    staff:StaffApi

class ActivityWithAssignmentsApi(BaseModel):
    "response class for concrete activity"
    activity_id:uuid.UUID
    template_id:uuid.UUID
    name:str|None
    location:str
    activity_start:datetime.datetime
    activity_finish:datetime.datetime
    staff_assignments:list[AssignmentWithStaff]
    def includes_staff(self,staff_id):
        return any((a.staff.id==staff_id or a.staff.name==staff_id) for a in self.staff_assignments)

class GetActivitiesRequest(BaseModel):
    "request"
    start_date:datetime.date=datetime.date(1970,1,1)
    finish_date:datetime.date=datetime.date(2099,1,1)

GetActivitiesResponse=RootModel[dict[datetime.date,list[ActivityWithAssignmentsApi]]]

def get_activities(sess,request:GetActivitiesRequest) ->GetActivitiesResponse:
    "get activities and assignments for date range"
    activities_query=(select(func.date(Activity.activity_start),Activity)
            .where(func.date(Activity.activity_start)>=(request.start_date))
            .where(func.date(Activity.activity_start)<=(request.finish_date))
            .order_by(func.date(Activity.activity_start)
    ))
    activities={date:list(a[1] for a in activities)
        for date,activities in itertools.groupby(sess.exec(activities_query),lambda k:k[0])}
    response=GetActivitiesResponse.model_validate(activities,from_attributes=True)
    print(response)
    return response
