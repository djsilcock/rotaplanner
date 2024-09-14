"Api requests and responses"

import datetime
import itertools
import uuid
import enum

from .models import Activity, Requirement, Staff, StaffAssignment
from pydantic import BaseModel, Field, RootModel,TypeAdapter
from sqlmodel import select,delete
from sqlalchemy import func
from typing import Literal,Annotated,Union


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
    return response

def get_staff(sess):
    return list(sess.exec(select(Staff)))



class ReallocateStaffDragDropEntry(BaseModel):
    activity:uuid.UUID
    initialstaff:uuid.UUID|None=None
    newstaff:uuid.UUID|None=None
    newdate:datetime.date|None=None

class DragDropHandlerRequest(BaseModel):
    entries:list[ReallocateStaffDragDropEntry]=Field(default_factory=list)

class AllocateStaffRequest(BaseModel):
    alloctype:Literal['allocate']='allocate'
    newstaff:uuid.UUID
    activity:uuid.UUID
    force:bool=False

class SwapStaffRequest(BaseModel):
    alloctype:Literal['swapstaff']
    staff:tuple[uuid.UUID,uuid.UUID]
    activities:list[uuid.UUID]

class RemoveStaffRequest(BaseModel):
    alloctype:Literal['remove']='remove'
    initialstaff:uuid.UUID
    activity:uuid.UUID

#StaffChangeRequest=TypeAdapter(Annotated[Union[RestaffRequest,ReallocateStaffRequest,AllocateStaffRequest,SwapStaffRequest,RemoveStaffRequest],Field(discriminator='alloctype')])

def reallocate_staff(sess,reallocations:DragDropHandlerRequest):
    print(reallocations)
    return []
    for entry in reallocations.entries:
        if entry.initialstaff:
            sess.exec(delete(StaffAssignment).where(StaffAssignment.activity_id.in_(entry.activities)).where(StaffAssignment.staff_id==entry.initialstaff))
        if entry.newstaff:
            for act in entry.activities:
                sess.add(StaffAssignment(activity_id=act,staff_id=entry.newstaff))
        for act in entry.activities:
            if entry.initialstaff:
                sess.exec(delete(StaffAssignment).where(StaffAssignment.activity_id.in_(entry.activities)).where(StaffAssignment.staff_id==entry.initialstaff))
            if entry.newstaff:
                for act in entry.activities:
                    sess.add(StaffAssignment(activity_id=act,staff_id=entry.newstaff))
    dates=set()
    for activity_id in entry.activities:
        print([activity_id],list(act.activity_start.date() for act in sess.exec(select(Activity).where(Activity.activity_id == activity_id))))
    dates.update(act.activity_start.date() for act in sess.exec(select(Activity).where(Activity.activity_id.in_(entry.activities))))
    print ('dates',dates)     
    return [activity.activity_start.date() for activity in sess.exec(select(Activity).where(Activity.activity_id.in_(entry.activities)))]