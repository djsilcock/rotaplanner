"Data storage class"

from collections import ChainMap
from dataclasses import dataclass, field
from datetime import date, datetime,timedelta
from typing import Iterable,TypedDict,Sequence,cast
from enum import IntFlag
import random
import string
import pickle

import storage.filesystem

from templating import DemandTemplate,SupplyTemplate,rule_matches


storages = {'filesystem': storage.filesystem}

class Flags(IntFlag):
    "flags for duties"
    NONE=0
    LOCUM=1
    LOCKED=2

class Singleton(type):
    _instances={}
    def __call__(cls,*args,**kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

@dataclass
class DataStoreEntry:
    duty_allocations:dict[tuple[str, date], dict[str,Flags]]=field(default_factory=dict)
    demand_templates:dict[str,DemandTemplate]=field(default_factory=dict)
    supply_templates:dict[str,SupplyTemplate]=field(default_factory=dict)
    flagged_dates:dict[tuple[date,str],bool]=field(default_factory=dict)
    staff:dict=field(default_factory=dict)
    timestamp:datetime=field(default_factory=datetime.today)

class DataStoreChainMap:
    maps:list[DataStoreEntry]
    def __init__(self,*maps):
        self._cache={}
        self.maps=list(maps)
    def reset(self):
        self._cache.clear()
    def __getattr__(self, name: str):
        if name not in self._cache:
            self._cache[name]=ChainMap(*[getattr(m,name) for m in self.maps])
        return self._cache[name]
    def add_child(self,entry:DataStoreEntry=None):
        if entry is None:
            entry=DataStoreEntry()
        self.maps.insert(0,entry)
        self.maps.sort(key=lambda e:e.timestamp,reverse=True)
        self.reset()

class Sentinel:
    pass

sentinel=Sentinel()

def update_dict(d,key,updater,default=sentinel):
    orig_val=d.get(key,default)
    if orig_val is sentinel:
        raise KeyError
    d[key]=updater(orig_val)


class DataStore(metaclass=Singleton):
    "datastore class"
    datastore:DataStoreEntry
    def __init__(self, storage_type='filesystem'):
        self.datastore=DataStoreChainMap()
        self.storage = storages[storage_type]
        self._subscribers = set()


    def incremental_save(self,file):
        savedata=cast(DataStoreChainMap,self.datastore).maps[0]
        savedata.timestamp=datetime.today()
        pickle.dump(savedata,file)
        self.datastore.add_child()

    def save_all(self,file):
        for entry in self.datastore.maps:
            pickle.dump(entry,file)

    def rollback(self,save_point):
        self.datastore.maps=[m for m in self.datastore.maps if m.timestamp<save_point]

    def load(self,file):
        try:
            while (newdict:=pickle.load(file)):
                self.datastore.add_child(newdict)
        except (EOFError,pickle.PickleError):
            pass
        self.notify()

    def subscribe(self, callback):
        "add callback to notify changes"
        self._subscribers.add(callback)
        return lambda: self.unsubscribe(callback)

    def unsubscribe(self, callback):
        "remove callback to notify changes"
        self._subscribers.discard(callback)

    def notify(self):
        "notify subscribed listeners of changes"
        for callback in self._subscribers:
            try:
                callback(self)
            except TypeError:
                pass

    @property
    def names(self) -> tuple[str, ...]:
        "names of staff members"
        return tuple(self.config.names)

    def flagged_dates(self,flag) -> set[date]:
        "get tuple of public holidays "
        return {d for (d,flags) in self.datastore.flagged_dates.items() if flag in flags}

    def flag_date(self,d,flag):
        update_dict(self.datastore.flagged_dates,d,lambda s:s.union([flag]),set())

    def unflag_date(self,d,flag):
        update_dict(self.datastore.flagged_dates,d,lambda s:s.difference([flag]),set())

    def update_data(self, data):
        """update duty data in sheet
        data: dict of (name,date):{activity_id:flags}"""

        self.datastore.duty_allocations.update(data)
        self.notify()

    @property
    def daterange(self) -> tuple[date, date]:
        "get range of dates of known duties"
        mindate = min((key[1] for key in self.datastore.duty_allocations),
                      default=date.today())
        maxdate = max((key[1] for key in self.datastore.duty_allocations),
                      default=date.today())
        return (mindate, maxdate)

    @property
    def dates(self):
        "return list of all dates"
        mindate, maxdate = self.daterange
        return [mindate+timedelta(days=i)
                for i in range((maxdate-mindate).days+1)]

    
    def for_staff_and_date(self,staff,day):
        return self.datastore.duty_allocations.get((staff,day),{})
    
    
    
    def set_activity(self,name,day,activity):
        self.datastore.duty_allocations.setdefault((name,day),{}).setdefault(activity,Flags.NONE)

    def get_clashes(self,name,day,activity):
        current_allocations=self.for_staff_and_date_with_detail(name,day)
        proposed_activity=self.datastore.demand_templates[activity]
        return [alloc for alloc in current_allocations if not (alloc['finish']<proposed_activity.start_time or alloc['start']>proposed_activity.finish_time)]
    
    def clear_activity(self,name,day,activity):
        if isinstance(day,str):
            day=date.fromisoformat(day)
        self.datastore.duty_allocations.setdefault((name,day),{}).pop(activity,None)

    def set_flags(self,name,day,activity,flag):
        self.datastore.duty_allocations[(name,day)][activity] |= flag

    def clear_flags(self,name,day,activity,flag):
        self.datastore.duty_allocations[(name,day)][activity] &= ~flag

    def toggle_flag(self,name,day,activity,flag):
        self.datastore.duty_allocations[(name,day)][activity] ^= flag

    
    def update_demand_template(self,data):
        if data['id'] is None:
            data['id']=''.join([random.choice(string.ascii_letters) for x in range(7)])
            self.datastore.demand_templates[data['id']]=DemandTemplate(**data)
        else:
            self.datastore.demand_templates[data['id']]=DemandTemplate(**data)

    def delete_demand_template(self,template_id):
        del self.datastore.demand_templates[template_id]

    def get_demand_templates(self):
        return self.datastore.demand_templates.values()
    
    def get_demand_template(self,template_id):
        return self.datastore.demand_templates[template_id]

    def get_templates_for_day(self,day:date):
        "return list of demand templates valid on given day"
        templates=(t for t in self.get_demand_templates() if rule_matches(day,t.rules))
        return templates

    def import_clw_csv(self, csvfile: Iterable[str]):
        "import from csv file"
        self.update_data(self.storage.import_clw_csv(csvfile))

