import datetime
from enum import StrEnum
from typing import List, Optional

from sqlalchemy import ForeignKey, select,delete
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship,aliased
import sys,os,pathlib

if __name__=='__main__':
    sys.path.append(pathlib.Path(os.getcwd()).parent.parent)

from py_rotaplanner.database import db


class Activity(db.Model):
    __tablename__="activities"
    id:Mapped[int]=mapped_column(primary_key=True)
    name:Mapped[str]
    activity_start:Mapped[datetime.datetime]
    activity_finish:Mapped[datetime.datetime]
    staff:Mapped[list['StaffActivities']]=relationship()

class StaffActivities(db.Model):
    __tablename__="staff_activities"
    staff_id:Mapped[str]=mapped_column(primary_key=True)
    activity_id:Mapped[str]=mapped_column(ForeignKey('activities.id') ,primary_key=True)
    activity:Mapped[Activity]=relationship(back_populates='staff')

def get_assigned_activities(start_date,end_date):
    activities={}
    result=db.session.execute(
        #select(Activity.id,Activity.name,Activity.activity_start,StaffActivities.staff_id)
        select(Activity,StaffActivities.staff_id)
        .select_from(Activity)
        .join(StaffActivities,full=True)
        .where(Activity.activity_start>=start_date)
        .where(Activity.activity_start<=end_date))
    #for activity_id,name,day,staff in result:
    for activity,staff in result:
        activities.setdefault((activity.activity_start.date(),staff),set()).add(activity)
        activities.setdefault((activity.activity_start.date(),None),set()).add(activity)
    return activities

def get_activities_for_date(date):
    start_date=date
    finish_date=date+datetime.timedelta(days=1)
    return db.session.execute(select(Activity).where((Activity.activity_start>=start_date) & (Activity.activity_start<=finish_date))).scalars()

def assign_activity(staff,activity_id):
    db.session.merge(StaffActivities(staff_id=staff,activity_id=activity_id))
    db.session.commit()


def unassign_activity(staff,activity_id):
    db.session.execute(delete(StaffActivities).where((StaffActivities.activity_id==activity_id)&(StaffActivities.staff_id==staff)))
    db.session.commit()

def find_overlaps(staff,activity_id):
    target_activity=aliased(Activity)
    candidate_activity=aliased(Activity)
    result=db.session.execute(select(candidate_activity)
           .join(StaffActivities)
           .where(target_activity.activity_start<candidate_activity.activity_finish)
           .where(target_activity.activity_finish>candidate_activity.activity_start)
           .where(target_activity.id==activity_id)
           .where(StaffActivities.staff_id==staff)).scalars()
    return list(result)


