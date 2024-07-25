from ortools.sat.python import cp_model
from itertools import pairwise
from time import perf_counter
from collections import defaultdict,namedtuple
from typing import NamedTuple
from dataclasses import dataclass
import datetime
from scheduling import Activity,Timeslot
def date_as_int(date,reference_date=datetime.datetime(2022,1,1),resolution=1):
    if isinstance(date,datetime.date):
        date=datetime.datetime.combine(date,datetime.time(0,0))
    if isinstance(reference_date,datetime.date):
        reference_date=datetime.datetime.combine(reference_date,datetime.time(0,0))
    if isinstance(date,datetime.timedelta):
        reference_date=datetime.timedelta(seconds=0)
    return (date-reference_date)//datetime.timedelta(seconds=resolution)


def make_test_activities():
    planned_activities_template={
        'pm theatre 1':(13,18),
        'pm theatre 2':(13,18),
        'am theatre 1':(9,13),
        'am theatre 2':(9,13),
        'ICU daytime':(9,18)
    }
    index_date=datetime.datetime(2024,1,1)
    for day in range(7):
        for name,times in planned_activities_template.items():
            yield Timeslot(
                location=name,
                start=index_date+datetime.timedelta(days=day,hours=times[0]),
                finish=index_date+datetime.timedelta(days=day,hours=times[1]))

def solve():
    model=cp_model.CpModel()
    peeps=('Adam','Brenda','Charlie')
    activities={}
    activities=list(make_test_activities())
    jobplan={'Adam':((0,'pm theatre 1'),(0,'Mon am theatre 2')),'Brenda':((0,'pm theatre 1'),(0,'am theatre 1')),'Charlie':((0,'pm theatre 1'),(0,'am theatre 2'))}
    offer_templates=[
        ((0,'ICU daytime'),(1,'ICU daytime'),(2,'ICU daytime'),(3,'ICU daytime')),
        ((4,'ICU daytime'),(5,'ICU daytime'),(6,'ICU daytime')),
        ((0,'am theatre 1'),(0,'pm theatre 1')),
        ((0,'am theatre 2'),(0,'pm theatre 2')),
    ]

    leave={'Adam':[],'Brenda':[],'Charlie':[]}
    basis_types=('pay','for_time','available','flex')
    leave_types=('AL','time_back')
    idle_type='idle'
    boundaries={datetime.datetime(2024,1,1),datetime.datetime(2024,8,1)}
    
    for activity in activities:
        boundaries.add(activity.start)
        boundaries.add(activity.finish)
    segments=list(pairwise(sorted(boundaries)))
    
    for start,finish in segments:
            for area in leave_types:
                activities.append(Timeslot(location=area,start=start,finish=finish))
            activities.append(Timeslot(start=start,finish=finish,location=idle_type))

    
    activity_segs_by_name=defaultdict(set)
    activity_segs_by_slot=defaultdict(set)
    basis_segments={}
    for activity in activities:
        for seg in segments:
            if activity.includes_segment(seg):
                activity_segs_by_name[activity].add(seg)
                activity_segs_by_slot[seg].add(activity)

    is_active={}
    for staffname in peeps:
        local_is_active={(staffname,activity):model.new_bool_var(f'active {staffname} {activity}') for activity in activities}
        leave_segments=set()
        for leavetype,start,finish in leave[staffname]:
            for seg in segments:
                if seg[0]>=start and seg[1]<=finish:
                    leave_segments.add((leavetype,*seg)) 
        for seg in segments:
            this_segment={(staffname,'idle',seg):local_is_active[staffname,Timeslot(location='idle',start=seg[0],finish=seg[1])]}
            for basis  in basis_types:
                this_segment[(staffname,basis,seg)]=model.new_bool_var(f'{staffname} basis {basis} segment {seg}')
            model.add_exactly_one(this_segment.values())
            model.add_exactly_one(local_is_active[staffname,activity] for activity in activity_segs_by_slot[seg])
            basis_segments.update(this_segment)
        intervals={}
        for node in activities:
            active=local_is_active[staffname,node]
            intervals[staffname,node]=model.new_optional_fixed_size_interval_var(date_as_int(node.start),date_as_int(node.finish-node.start),active,f'interval {staffname} {node}')
        for activitygroup in activity_segs_by_slot.values():
            model.add_exactly_one(local_is_active[staffname,activity] for activity in activitygroup)
        jobplan_segments=set()
        for activity,seg_set in activity_segs_by_name.items():
            if (activity.day,activity.location) in jobplan[staffname]:
                jobplan_segments.update(seg_set)
        for seg in segments:
                model.add(basis_segments[(staffname,'available',seg)]==(seg in jobplan_segments))
                for lt in leave_types:
                    model.add_implication(local_is_active[staffname,Timeslot(location=lt,start=seg[0],finish=seg[1])],basis_segments[(staffname,'available',seg)])
                    pass

        #make sure timeshift is symmetrical
        time_back=sum(v*(activity.finish_int-activity.start_int) for (staff,activity),v in local_is_active.items() if activity.location=='time_back')
        for_time=sum(v*(finish[1]-start[1]) for (staff,basis,(start,finish)),v in basis_segments.items() if basis=='for_time')
        model.add(time_back==for_time)

        #enforce leave types
        for (staff,activity),active in local_is_active.items():
            if activity.location in leave_types and activity.location!='time_back':
                pass
                model.add(active==((activity.location,start,finish) in leave_segments)) 
        model.add_no_overlap(list(intervals.values()))
        is_active.update(local_is_active)
    model.minimize(sum(is_active[staffname,activity]*date_as_int(activity.finish-activity.start) for activity in activities for staffname in peeps if activity.location in ('idle',)))
    
    #for pa in planned_activities_template:
    #    model.add(sum(v for (staff,activity),v in is_active.items() if activity.location==pa)==1)

    solver=cp_model.CpSolver()
    print(solver.status_name(solver.solve(model)))
    duties={}
    for p in peeps:
        duties[p]=[]
        for activity in sorted(activities,key=lambda n:n.start_int):
            if solver.value(is_active[p,activity]):
                basis=[basis for (staff,basis,(start,finish)),v in basis_segments.items() if start>=activity.start and finish<=activity.finish and staff==p and solver.value(v)]
                duties[p].append(f'{activity.day} {activity.location} ({",".join(basis)})')
        print(p,";".join(duties[p]))
    #for i in is_active.items():
    #    if solver.value(i[1]):
    #        print(i)
    #for v in basis_segments.values():
    #    if solver.value(v):
    #        print(v.name,solver.value(v))


start_time=perf_counter()
solve()
finish_time=perf_counter()
print (finish_time-start_time)

