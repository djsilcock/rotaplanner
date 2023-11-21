import datetime
from itertools import pairwise

class ShiftSplitter:
    def __init__(self) -> None:
        self.splits=set()
    def register(self,start:datetime.timedelta,finish:datetime.timedelta):
        self.splits.add(start.seconds)
        self.splits.add(finish.seconds)
    def intervals(self,start:datetime.datetime,finish:datetime.datetime):
        if datetime.timedelta(hours=start.hour,minutes=start.minute,seconds=start.second).seconds not in self.splits:
            raise ValueError('start time not registered')
        if datetime.timedelta(hours=finish.hour,minutes=finish.minute,seconds=finish.second).seconds not in self.splits:
            raise ValueError('finish time not registered')
        def inner():
            splits=sorted(self.splits)
            if finish<start:
                raise ValueError('start date must not be later than finish date')
            current_date=start.replace(hour=0,minute=0,second=0,microsecond=0)
            while current_date<=finish:
                for s in splits:
                    current_datetime=current_date+datetime.timedelta(seconds=s)
                    if start<=current_datetime<=finish:
                        yield current_datetime
                current_date+=datetime.timedelta(days=1)
        return pairwise(inner())