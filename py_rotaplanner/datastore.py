"Data storage class"

from collections import ChainMap
from dataclasses import dataclass, field,fields
from datetime import date, datetime, timedelta
from typing import Iterable, TypedDict, Sequence, cast,Any,TypeVar
from enum import IntFlag
import random
import string
import pickle

from py_rotaplanner.storage import filesystem

from .templating import DemandTemplate, SupplyTemplate, rule_matches
from .scheduling import Activity


storages = {'filesystem': filesystem}


class Flags(IntFlag):
    "flags for duties"
    NONE = 0
    LOCUM = 1
    LOCKED = 2

class Unpickler(pickle.Unpickler):
    def find_class(self, module_name: str, global_name: str) -> Any:
        print(module_name,global_name)
        return super().find_class(module_name, global_name)

@dataclass
class DataStoreEntry:
    duty_allocations: dict[tuple[str, date],
                           dict[str, Flags]] = field(default_factory=dict)
    demand_templates: dict[str, DemandTemplate] = field(default_factory=dict)
    supply_templates: dict[str, SupplyTemplate] = field(default_factory=dict)
    activities:dict[str,Activity]=field(default_factory=dict)
    flagged_dates: dict[tuple[date, str], bool] = field(default_factory=dict)
    staff: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.today)


class DataStoreChainMap:
    maps: list[DataStoreEntry]

    def __init__(self, *maps):
        self._cache = {}
        self.maps = list(maps)
        
    def reset(self):
        self._cache.clear()

    def __getattr__(self, name: str):
        if name not in self._cache:
            self._cache[name] = ChainMap(
                *[getattr(m, name) for m in self.maps if hasattr(m,name)])
        return self._cache[name]

    def add_child(self, entry: DataStoreEntry = None):
        if entry is None:
            entry = DataStoreEntry()
        self.maps.insert(0, entry)
        self.maps.sort(key=lambda e: e.timestamp, reverse=True)
        self.reset()


class Sentinel:
    pass


sentinel = Sentinel()


def update_dict(d, key, updater, default=sentinel):
    orig_val = d.get(key, default)
    if orig_val is sentinel:
        raise KeyError
    d[key] = updater(orig_val)

T=TypeVar('T')
def intervals_overlap(activity1:tuple[T,T],activity2:tuple[T,T]):
    (start1,finish1)=activity1
    (start2,finish2)=activity2
    if start1>=finish2 or start2>=finish1:
        return False
    return True 



class DataStore:
    "datastore class"
    datastore: DataStoreEntry
    def __init__(self, storage_type='filesystem'):
        self._subscribers = set()
        self.datastore = DataStoreChainMap()
        self.storage = storages[storage_type]
        self.load()
        if len(self.datastore.maps)==0:
            self.datastore.add_child()
        
    def flatten(self):
        layer=DataStoreEntry()
        for m in fields(layer):
            if m.name=='timestamp':
                continue
            target=getattr(layer,m.name)
            source=getattr(self.datastore,m.name)
            target.update(source)
        layer.timestamp=datetime.today()
        with self.storage.full_save() as file:
                pickle.dump(layer, file)


    def incremental_save(self):
        with self.storage.incremental_save() as file:
            savedata = cast(DataStoreChainMap, self.datastore).maps[0]
            savedata.timestamp = datetime.today()
            pickle.dump(savedata, file)
            self.datastore.add_child()

    def save_all(self):
        with self.storage.full_save() as file:
            for entry in self.datastore.maps:
                pickle.dump(entry, file)

    def rollback(self, save_point):
        self.datastore.maps = [
            m for m in self.datastore.maps if m.timestamp < save_point]
        

    def load(self):
        with self.storage.load() as file:
            try:
                while (newdict := Unpickler(file).load()):
                    self.datastore.add_child(newdict)
            except (EOFError, pickle.PickleError):
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
        return ('Adam','Bob','Charlie','Dave','Eric','Fred','George')
        return tuple(self.config.names)

    def flagged_dates(self, flag) -> set[date]:
        "get tuple of eg public holidays "
        return {d for (d, flags) in self.datastore.flagged_dates.items() if flag in flags}

    def flag_date(self, d, flag):
        update_dict(self.datastore.flagged_dates, d,
                    lambda s: s.union([flag]), set())
        self.notify()

    def unflag_date(self, d, flag):
        update_dict(self.datastore.flagged_dates, d,
                    lambda s: s.difference([flag]), set())
        self.notify()

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

    def for_staff_and_date(self, staff, day):
        return self.datastore.duty_allocations.get((staff, day), {})
    
    def toggle_activity(self,name,day,activity,overwrite=True):
        print (f'toggling {activity}')
        if activity in self.datastore.duty_allocations.setdefault((name,day),{}):
            self.clear_activity(name,day,activity)
        else:
            self.set_activity(name,day,activity,overwrite)
        self.notify()

    def set_activity(self, name, day, activity,overwrite=True):
        existing_allocations=[self.get_activity(a) for a in self.datastore.duty_allocations.setdefault((name, day), {})]
        proposed_activity=self.get_activity(activity)
        for a in existing_allocations:
            if intervals_overlap((a.start_time,a.finish_time),(proposed_activity.start_time,proposed_activity.finish_time)):
                if overwrite:
                    self.clear_activity(name,day,a.id)
                else:
                    raise ValueError('clash')
        self.datastore.duty_allocations[(name,day)].setdefault(proposed_activity.id, Flags.NONE)
        self.notify()

    def get_clashes(self, name, day, activity):
        current_allocations = self.for_staff_and_date_with_detail(name, day)
        proposed_activity = self.datastore.demand_templates[activity]
        return [alloc for alloc in current_allocations if not (alloc['finish'] < proposed_activity.start_time or alloc['start'] > proposed_activity.finish_time)]
    
    def materialise(self,from_date,to_date):
        this_date=from_date
        while this_date<to_date:
            for templ in self.get_templates_for_day(this_date):
                start_time=datetime.combine(this_date,templ.start_time)
                finish_time=datetime.combine(this_date,templ.finish_time)
                if finish_time<=start_time:
                    finish_time+=datetime.timedelta(days=1)
                activity= Activity(
                    template=templ,
                    name=templ.name,
                    start_time=start_time,
                    finish_time=finish_time,
                    id=f'{this_date.isoformat()}{templ.id}'
                )
                self.datastore.activities[activity.id]=activity
            this_date+=timedelta(days=1)
        self.notify()

    def cancel_activity(self,activity_id):
        for allocation in self.datastore.duty_allocations.values():
            allocation.pop(activity_id,None)
        self.datastore.activities.pop(activity_id,None)
        self.notify()

    def clear_activity(self, name, day, activity):
        if isinstance(day, str):
            day = date.fromisoformat(day)
        self.datastore.duty_allocations.setdefault(
            (name, day), {}).pop(activity, None)
        self.notify()

    def set_flags(self, name, day, activity, flag):
        self.datastore.duty_allocations[(name, day)][activity] |= flag
        self.notify()

    def clear_flags(self, name, day, activity, flag):
        self.datastore.duty_allocations[(name, day)][activity] &= ~flag
        self.notify()

    def toggle_flag(self, name, day, activity, flag):
        self.datastore.duty_allocations[(name, day)][activity] ^= flag
        self.notify()

    def get_activity(self,activity_id):
        activity= self.datastore.activities.get(activity_id)
        return activity
    
    def get_demand_template(self, template_id):
        return self.datastore.demand_templates[template_id]

    def update_demand_template(self, data):
        self.datastore.demand_templates[data.id] = data
        self.notify()

    def delete_demand_template(self, template_id):
        del self.datastore.demand_templates[template_id]
        self.notify()

    def get_demand_templates(self):
        return self.datastore.demand_templates.values()

    def get_supply_template(self, template_id):
        return self.datastore.supply_templates[template_id]

    def update_supply_template(self, data):
        self.datastore.supply_templates[data.id] = data
        self.notify()

    def delete_supply_template(self, template_id):
        del self.datastore.supply_templates[template_id]
        self.notify()

    def get_supply_templates(self):
        return self.datastore.supply_templates.values()

    def get_activities_for_day(self,day:date):
        return (act for act in self.datastore.activities.values() if act.start_time.date()==day)
    
    def get_templates_for_day(self, day: date):
        "return list of demand templates valid on given day"
        templates = (t for t in self.get_demand_templates()
                     if rule_matches(day, t.rules))
        return templates

    def import_clw_csv(self, csvfile: Iterable[str]):
        "import from csv file"
        self.update_data(self.storage.import_clw_csv(csvfile))

datastore=DataStore()
datastore.materialise(date(2024,1,2),date(2024,3,1))
