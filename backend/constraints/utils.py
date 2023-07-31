"""constraint manager"""


from collections import deque
from typing import TypeVar, Iterable,Callable,Any


T=TypeVar('T')                    
def groupby(iterable:Iterable[T],func:Callable[[T],Any]) ->Iterable[list[T]]:
    groups={}
    for i in iterable:
        groups.setdefault(func(i),[]).append(i)
    return groups.values()

def sliding_date_range(days,length):
    "returns window of dates.Pre-filters are passed to underlying days iterator"
    date_deque = deque(maxlen=length)
    for day in days:
        date_deque.append(day)
        if len(date_deque) == length:
            yield date_deque
