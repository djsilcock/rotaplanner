"Data storage class"

from dataclasses import dataclass, field, fields, replace
from datetime import date, timedelta
from itertools import pairwise
from typing import Iterable
from warnings import warn

import storage.filesystem
from datatypes import SessionDuty
from logger import log

storages = {'filesystem': storage.filesystem}


@dataclass
class Config:
    "config class"
    names: list[str] = field(default_factory=list)
    pubhols: set[date] = field(default_factory=set)


class DataStore:
    "datastore class"

    def __init__(self, storage_type='filesystem'):
        self.data: dict[tuple[str, date], list[SessionDuty]] = {}
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
        data: dict of (name,date):[SessionDuty,...]"""

        if overwrite:
            self.data.clear()
        self.data.update({key: [session if isinstance(session, SessionDuty)
                         else SessionDuty(**session) for session in val]
                         for key, val in data.items()})
        self.notify()

    @property
    def daterange(self) -> tuple[date, date]:
        "get range of dates of known duties"
        mindate = min((key[1] for key in self.data),
                      default=date.today())
        maxdate = max((key[1] for key in self.data),
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

    def as_dict_by_name(self):
        "return datastore as JSON-serializable data"
        data = {}
        for (name, day), sessionduties in self.data.items():
            data.setdefault(day.isoformat()[0:10], {})[name] = [
                {'start': sessionduty.start.seconds//3600,
                 'finish': sessionduty.finish.seconds//3600,
                 'duty': sessionduty.duty,
                 'flags': list(sessionduty.flags)}
                for sessionduty in sessionduties]
        return {**self.get_config(), 'data': data}

    def as_dict_by_location(self):
        "return data by location"
        data = {}
        for (name, day), sessionduties in self.data.items():
            for sessionduty in sessionduties:
                (data.setdefault(day.isoformat()[0:10], {})
                    .setdefault(sessionduty.duty, [])
                    .append(
                        {'name': name,
                         'start': sessionduty.start.seconds/3600,
                         'finish': sessionduty.finish.seconds/3600,
                         'flags': list(sessionduty.flags)}))
        return {**self.get_config(), 'data': data}

    def setduty(self, name, duty_date, start, finish, duty):
        "Set duty as determined by menu"
        log((name,duty,date,start,finish,duty))
        cell = self.data.setdefault((name, date.fromisoformat(duty_date)), [])
        if isinstance(start,int):
            start=timedelta(seconds=start)
        if isinstance(finish,int):
            finish=timedelta(seconds=finish)
            
        for sessionduty in list(cell):
            if start <= sessionduty.start and finish >= sessionduty.finish:
                cell.remove(sessionduty)
                continue
            if start <= sessionduty.finish and finish >= sessionduty.start:
                if start > sessionduty.start and finish < sessionduty.finish:
                    cell.append(replace(sessionduty, start=finish))
                    sessionduty.finish = start
                elif start >= sessionduty.start and finish >= sessionduty.finish:
                    sessionduty.finish = start
                elif start <= sessionduty.start and finish <= sessionduty.finish:
                    sessionduty.start = finish
        cell.append(SessionDuty(start, finish, duty))
        cell.sort(key=lambda d: d.start)

        # error check
        prevtime = None
        for sessionduty in cell:
            if prevtime is not None:
                assert prevtime <= sessionduty.start
                assert sessionduty.finish >= sessionduty.start
            prevtime = sessionduty.finish

        self.notify()

    def split(self, name, duty_date, split_time):
        "Split duty at given time"
        cell = self.data.setdefault((name, date.fromisoformat(duty_date)), [])
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
        cell = self.data.setdefault((name, date.fromisoformat(duty_date)), [])
        for sd1,sd2 in pairwise(cell):
            if sd1.start==start1 and sd2.finish==finish2:
                cell.remove(sd2)
                sd1.finish=sd2.finish
                break
        self.notify()

    def setflag(self, name, duty_date, start, finish, *flags):
        "set flag for duty"
        for duty in self.data.get((name, duty_date), []):
            if start == duty.start and finish == duty.finish:
                duty.flags.update(flags)
        self.notify()

    def delflag(self, name, duty_date, start, finish, *flags):
        "remove flag for duty"
        for duty in self.data.get((name, duty_date), []):
            if start == duty.start and finish == duty.finish:
                duty.flags.difference_update(flags)
        self.notify()

    def toggleflag(self, name, duty_date, start, finish, flags):
        "toggle flag for duty"
        for duty in self.data.get((name, duty_date), []):
            if start == duty.start and finish == duty.finish:
                duty.flags.symmetric_difference_update(flags)
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
            self.data = newfile.data
            self.config = newfile.config
            self.notify()
        except FileNotFoundError:
            warn("Savefile not found")

    def import_clw_csv(self, csvfile: Iterable[str]):
        "import from csv file"
        self.update_data(self.storage.import_clw_csv(csvfile))
