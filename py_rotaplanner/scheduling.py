"models for concrete activities"

import datetime
from dataclasses import dataclass
from .templating import DemandTemplate


@dataclass
class Activity:
    template:DemandTemplate
    name:str
    start_time:datetime.datetime
    finish_time:datetime.datetime
    id:str
    def materialise(self,from_date,to_date,templates:list[DemandTemplate]):
        for templ in templates:
            this_date=from_date
            while this_date<to_date:
                if templ.matches(this_date):    
                    start_time=datetime.datetime.combine(this_date,templ.start_time)
                    finish_time=datetime.datetime.combine(this_date,templ.finish_time)
                    if finish_time<=start_time:
                        finish_time+=datetime.timedelta(days=1)
                    yield Activity(
                        template=templ,
                        name=templ.name,
                        start_time=start_time,
                        finish_time=finish_time,
                        id=f'{this_date.isoformat()}{templ.id}'
                    )
                this_date+=datetime.timedelta(days=1)
        

@dataclass(unsafe_hash=True)
class Timeslot:
    location:str
    start:datetime.datetime
    finish:datetime.datetime
    def includes_segment(self,seg):
        if self.start>seg[1]:
            return False
        if self.finish<seg[0]:
            return False
        return True


