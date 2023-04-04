"""contains rules to constrain the model"""
from calendar import SATURDAY
from collections import deque
from datetime import timedelta
from itertools import accumulate, groupby
from uuid import uuid4


from constraints.core_duties import icu

from ortools.sat.python import cp_model


def enforce_max_x_in_y(ctx,filterfunc,config,getkey=icu):
    uid=uuid4()
    for staff in ctx.staff:
        duties={}
        for d in ctx.days:
            for shift in ctx.shifts:
                if filterfunc(shift,d,staff):
                        duty_atom=ctx.dutystore[getkey(shift,d,staff)]
                        duties.setdefault(d,[]).append(duty_atom)
                        duties.setdefault(d+timedelta(days=config['denominator']),[]).append(-duty_atom)
        running_total=0
        for i in sorted(duties):
             running_total+=sum(duties[i])
             assert isinstance(ctx.model,cp_model.CpModel)
             newint=ctx.model.NewIntVar(0,config['numerator'],f'{uid}{i}{staff}')
             ctx.model.Add(newint==running_total)

                  
