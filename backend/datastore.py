"Data storage class"

from dataclasses import dataclass, field, fields, replace,asdict
from datetime import date, timedelta
from itertools import pairwise
from typing import Iterable,TypedDict,Sequence,cast,overload,Literal,Generator,TYPE_CHECKING
from warnings import warn
from enum import IntFlag,auto
import random
import string

import storage.filesystem
from datatypes import SessionDuty
from templating import DemandTemplate,SupplyTemplate,rule_matches
from logger import log

storages = {'filesystem': storage.filesystem}

class Flags(IntFlag):
    NONE=0
    LOCUM=1
    LOCKED=2

@dataclass
class Config:
    "config class"
    names: list[str] = field(default_factory=list)
    pubhols: set[date] = field(default_factory=set)

class DutyDetail(TypedDict):
    start:int
    finish:int
    name:str
    flags:int|Flags


class DataStore:
    "datastore class"

    def __init__(self, storage_type='filesystem'):
        self.duty_allocations: dict[tuple[str, date], dict[str,Flags]] = {}
        self.demand_templates:dict[str,DemandTemplate]={}
        self.supply_templates:list[SupplyTemplate]=[]
        self.storage = storages[storage_type]
        self.config = Config(names=['Fred', 'Barney'])
        self._subscribers = set()

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

    @property
    def pubhols(self) -> set[date]:
        "get tuple of public holidays "
        return self.config.pubhols

    def configure(self, **updates):
        "configuration"
        def set_or_update(attr, setter):
            try:
                setattr(self.config, attr, setter(getattr(self.config, attr)))
            except TypeError:
                setattr(self.config, attr, setter)
        for config_field in fields(Config):
            if config_field.name in updates:
                set_or_update(config_field.name, updates.pop(config_field.name))
        if len(updates) > 0:
            raise ValueError(f'unknown config keys:{",".join(updates.keys())}')
        self.notify()

    def update_data(self, data, overwrite=False):
        """update duty data in sheet
        data: dict of (name,date):{activity_id:flags}"""

        if overwrite:
            self.duty_allocations.clear()
        self.duty_allocations.update(data)
        self.notify()

    @property
    def daterange(self) -> tuple[date, date]:
        "get range of dates of known duties"
        mindate = min((key[1] for key in self.duty_allocations),
                      default=date.today())
        maxdate = max((key[1] for key in self.duty_allocations),
                      default=date.today())
        return (mindate, maxdate)

    @property
    def dates(self):
        "return list of all dates"
        mindate, maxdate = self.daterange
        return [mindate+timedelta(days=i)
                for i in range((maxdate-mindate).days+1)]

    def get_config(self):
        "return configuration options as dict"
        return {
            'names': self.names,
            'minDate': self.daterange[0].isoformat(),
            'maxDate': self.daterange[1].isoformat(),
            'pubhols': [ph.isoformat() for ph in self.pubhols]
        }

    def for_staff_and_date(self,staff,day):
        if isinstance(day,str):
            day=date.fromisoformat(day)
        return self.duty_allocations.get((staff,day),{})
    
    def for_staff_and_date_with_detail(self,staff,day) ->Sequence[DutyDetail]:
        return list(sorted(
            [cast(DutyDetail,{'start':self.demand_templates[demand_id].start,
              'finish':self.demand_templates[demand_id].finish,
              'duty':self.demand_templates[demand_id].name,
              'flags':flags}) for demand_id,flags in self.for_staff_and_date(staff,day).items()],
            key=lambda x:x['start']))

    
    def set_activity(self,name,day,activity):
        if isinstance(day,str):
            day=date.fromisoformat(day)
        self.duty_allocations.setdefault((name,day),{}).setdefault(activity,Flags.NONE)

    def get_clashes(self,name,day,activity):
        if isinstance(day,str):
            day=date.fromisoformat(day)
        current_allocations=self.for_staff_and_date_with_detail(name,day)
        proposed_activity=self.demand_templates[activity]
        return [alloc for alloc in current_allocations if not (alloc['finish']<proposed_activity.start or alloc['start']>proposed_activity.finish)]
    
    def clear_activity(self,name,day,activity):
        if isinstance(day,str):
            day=date.fromisoformat(day)
        self.duty_allocations.setdefault((name,day),{}).pop(activity,None)

    def set_flags(self,name,day,activity,flag):
        self.duty_allocations[(name,day)][activity] |= flag

    def clear_flags(self,name,day,activity,flag):
        self.duty_allocations[(name,day)][activity] &= ~flag

    def toggle_flag(self,name,day,activity,flag):
        self.duty_allocations[(name,day)][activity] ^= flag

    def as_dict_by_name(self):
        "return datastore as JSON-serializable data"
        data = {}
        for (name, day), sessionduties in self.duty_allocations.items():
            data.setdefault(day.isoformat()[0:10], {})[name] = self.for_staff_and_date_with_detail(name,day)
        return {**self.get_config(), 'data': data}

    def as_dict_by_location(self):
        "return data by location"
        data = {}
        for (name, day), sessionduties in self.duty_allocations.items():
            for sessionduty in sessionduties:
                (data.setdefault(day.isoformat()[0:10], {})
                    .setdefault(sessionduty.duty, [])
                    .append(
                        {'name': name,
                         'start': sessionduty.start.seconds/3600,
                         'finish': sessionduty.finish.seconds/3600,
                         'flags': list(sessionduty.flags)}))
        return {**self.get_config(), 'data': data}
    
    def update_demand_template(self,data):
        if data['id'] is None:
            data['id']=''.join([random.choice(string.ascii_letters) for x in range(7)])
            self.demand_templates[data['id']]=DemandTemplate(**data)
        else:
            if data.get('delete'):
                del self.demand_templates[data['id']]
            else:
                self.demand_templates[data['id']]=DemandTemplate(**data)

    @overload
    def get_demand_templates(self,as_dict:Literal[False]) -> Generator[DemandTemplate,None,None]:
        ...
    @overload
    def get_demand_templates(self)-> Generator[DemandTemplate,None,None]:
        ...
    @overload
    def get_demand_templates(self,as_dict:Literal[True]) -> Generator[dict,None,None]:
        ...
    def get_demand_templates(self,as_dict=False):
        return (asdict(m) if as_dict else m for m in self.demand_templates.values())
    
    def get_demand_template(self,template_id):
        return self.demand_templates[template_id]

    @overload
    def get_templates_for_day(self,day:date,as_dict:Literal[False])->Generator[DemandTemplate,None,None]:
        ...
    @overload
    def get_templates_for_day(self,day:date,as_dict:Literal[True])->Generator[dict,None,None]:
        ...
    def get_templates_for_day(self,day:date,as_dict=False):
        "return list of demand templates valid on given day"
        templates=(t for t in self.get_demand_templates() if rule_matches(day,'root',t.rules))
        if as_dict:
            return (asdict(t) for t in templates)
        return templates

    def split(self, name, duty_date, split_time):
        "Split duty at given time"
        cell = self.duty_allocations.setdefault((name, date.fromisoformat(duty_date)), [])
        for sessionduty in cell:
            if split_time > sessionduty.start and split_time < sessionduty.finish:
                cell.append(replace(sessionduty, start=split_time))
                sessionduty.finish = split_time
                break
        cell.sort(key=lambda d: d.start)

        # error check
        prevtime = None
        for sessionduty in cell:
            if prevtime is not None:
                assert prevtime <= sessionduty.start
                assert sessionduty.finish >= sessionduty.start
            prevtime = sessionduty.finish

        self.notify()

    def glue(self,name,duty_date,start1,finish2):
        "join consecutive duties together"
        cell = self.duty_allocations.setdefault((name, date.fromisoformat(duty_date)), [])
        for sd1,sd2 in pairwise(cell):
            if sd1.start==start1 and sd2.finish==finish2:
                cell.remove(sd2)
                sd1.finish=sd2.finish
                break
        self.notify()

    def set_public_holiday(self, _date, is_holiday=True):
        "set or unset public holiday"
        def updater(pubhols):
            if is_holiday:
                pubhols.add(_date)
            else:
                pubhols.discard(_date)
            return pubhols
        self.configure(pubhols=updater)

    def save_data(self):
        "Save data to disc"
        self.storage.save_data(self)

    def load_data(self):
        "load from file"
        try:
            newfile = self.storage.load_data()
            self.duty_allocations = newfile.data
            self.config = newfile.config
            self.notify()
        except FileNotFoundError:
            warn("Savefile not found")

    def import_clw_csv(self, csvfile: Iterable[str]):
        "import from csv file"
        self.update_data(self.storage.import_clw_csv(csvfile))
