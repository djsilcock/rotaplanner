"""contains rules to constrain the model"""
from calendar import SATURDAY
from collections import deque
from datetime import timedelta


from constraints.core_duties import icu

from ortools.sat.python import cp_model

def sliding_window(iter,length):
    d=deque([],length)
    for i in iter:
        d.append(i)
        if len(d)<length:
            continue
        yield list(d)

def gen(datelist,ctx,filterfunc,staff):
     for d in datelist:
        for shift in ctx.shifts:
            if filterfunc(shift,d,staff):
                    yield ctx.dutystore[icu(shift,d,staff)]

def enforce_max_x_in_y(ctx,filterfunc,config):
            enforced = 1 #self.get_constraint_atom(day=day)
            print(ctx.days)
            for staff in ctx.staff:
                for datelist in sliding_window(ctx.days,config['denominator']):
                    #print(datelist)    
                    ctx.model.Add(
                        sum(gen(datelist,ctx,filterfunc,staff)) <= config['numerator']
                    ).OnlyEnforceIf(enforced)

def new_enforce_max_x_in_y(ctx,filterfunc,config):
        enforced = 1 #self.get_constraint_atom()
        startdate=ctx.days[0]
        for staff in ctx.staff:
            duties=[(day,ctx.dutystore[icu(shift,day,staff)])
                    for day in ctx.days
                    for shift in ctx.shifts
                    if filterfunc(shift,day,staff)]
            changes=[]
            times=[]
            actives=[]
            for day,duty in duties:
                  changes.append(1)
                  actives.append(duty)
                  times.append((day-startdate).days)
                  changes.append(-1)
                  actives.append(duty)
                  times.append((day-startdate).days+config['denominator'])
            assert isinstance(ctx.model,cp_model.CpModel)
            ctx.model.AddReservoirConstraintWithActive(times,changes,actives,0,config['numerator'])

                  
