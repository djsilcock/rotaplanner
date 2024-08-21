import datetime
from enum import StrEnum
from typing import List, Optional
import uuid
from pydantic import BaseModel,Field
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
    staff:Mapped[S]

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

class SupplyTemplateEntry(BaseModel):
    dateoffset:int
    activity_tags:set[str]
    template_id:uuid.UUID
    
class SupplyTemplate(BaseModel):
    "template of offers of cover"
    id:uuid.UUID=Field(default_factory=uuid.uuid4)
    staff:str
    ruleset:RuleGroup
    name:str
    entries:list[SupplyTemplateEntry]
    def materialise(self,date,activities:dict[datetime.date,list['Activity']]):
        results=[]
        if not self.ruleset.matches(date):
            return
        for entry in self.entries:
            if date+datetime.timedelta(days=entry.dateoffset) not in activities:
                return
            possibilities=set()
            for activity in activities[date+datetime.timedelta(days=entry.dateoffset)]:
                if not entry.activity_tags.isdisjoint(activity.template.activity_tags):
                    possibilities.add(activity.id)
                if activity.template.id in entry.activity_tags:
                    possibilities.add(activity.id)
            if len(possibilities)==0:
                return
            results.append(possibilities)
        for combination in itertools.product(*results):
            combi=set(combination)
            if len(combi)==len(self.entries):  #de-duplicate
                yield combi

def generate_offers_for_range(start,finish):
    supply_template:SupplyTemplate
    day=start
    activities_by_date={}
    activities_by_offer={}
    offers={}
    offers_active={}
    activities_active={}
    staff=datastore.get_staff()
    while day<finish:
        activities_by_date[day]=datastore.get_activities_for_day(day)
        for s in staff:
            for a in activities_by_date[day]:
                activities_active[a,s]=False
        day+=datetime.timedelta(day=1)
    for supply_template in datastore.get_supply_templates():
        for date in activities_by_date:
            offers_for_day=list(supply_template.materialise(date,activities_by_date))
            for index,offer_combination in enumerate(offers_for_day):
                offers[supply_template.id,date,index]=offer_combination
                for activity in offer_combination:
                    activities_by_offer.setdefault((activity,supply_template.staff),set()).add((supply_template.id,date,index))
                    offers_active[supply_template.id,date,index]=None
                    offers[supply_template.id,date,index]=offer_combination
                    activities_active[activity,supply_template.staff]=None
    for o in offers_active:
        offers_active[o]=model.new_bool_var(repr(o))
    for a in activities_active:
        if activities_active[a] is None:
            activities_active[a]=model.new_bool_var(a)
    for o,v in offers.items():
        model.add_all_true(activities_active[act] for act in v).only_enforce_if(offers_active[o])
    for activity,v in activities_by_offer.items():
        model.at_least_one(offers_active[offer] for offer in v).only_enforce_if(activities_active[activity])
    return activities_active
"""
Offer active =>activity active
activity active =>at least one offer active
"""        


def generate_offers_for_range(start,finish):
    supply_template:SupplyTemplate
    day=start
    activities_by_date={}
    activities_by_offer={}
    offers={}
    offers_active={}
    while day<finish:
        activities_by_date[day]=datastore.get_activities_for_day(day)
        day+=datetime.timedelta(day=1)
    for supply_template in datastore.get_supply_templates():
        for date in activities_by_date:
            offers_for_day=list(supply_template.materialise(date,activities_by_date))
            for index,offer_combination in enumerate(offers_for_day):
                offers[supply_template.id,date,index]=offer_combination
                for activity in offer_combination:
                    activities_by_offer.setdefault((activity,supply_template.staff),set()).add((supply_template.id,date,index))
                    offers[supply_template.id,date,index]=offer_combination
    for o in offers_active:
        offers_active[o]=model.new_bool_var(repr(o))
    for a in activities_active:
        if activities_active[a] is None:
            activities_active[a]=model.new_bool_var(a)
    for o,v in offers.items():
        model.add_all_true(activities_active[act] for act in v).only_enforce_if(offers_active[o])
    for activity,v in activities_by_offer.items():
        model.at_least_one(offers_active[offer] for offer in v).only_enforce_if(activities_active[activity])
    return activities_active
"""
Offer active =>activity active
activity active =>at least one offer active
"""        

@dataclass
class SupplyOffer:
    supply_template:SupplyTemplate
    anchor_date:datetime.date
    staff:str
    active:cp_model.IntVar

@dataclass
class ConcreteActivityOffer:
    demand_template:ActivityTemplate
    anchor_date:datetime.date
    staff:str
    active:cp_model.IntervalVar
    offers:list[SupplyOffer]



