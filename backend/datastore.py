"Data storage class"

from dataclasses import asdict
from typing import Iterable
from warnings import warn
from datetime import date, timedelta
from datatypes import SessionDuty
import storage.filesystem

storages = {'filesystem': storage.filesystem}


class DataStore:
    "datastore class"

    def __init__(self, storage_type='filesystem'):
        self.data: dict[tuple, SessionDuty] = {}
        self.sessions = ('am', 'pm', 'eve', 'night')
        self.storage = storage_type
        self.config = {}

    @property
    def names(self) -> tuple[str]:
        "names of staff members"
        return self.config.get(None, {}).get('names', ())

    @property
    def pubhols(self) -> set[date]:
        "get tuple of public holidays "
        return set(self.config.get(None, {}).get('pubhols', ()))

    def get_storage_class(self):
        "get current storage backend"
        return storages[self.storage]

    def update_config(self, config: dict, overwrite=False):
        "update configuration information"
        if overwrite:
            self.config = config.copy()
        else:
            self.config.update(config)

    def update_data(self, data, overwrite=False):
        """update duty data in sheet
        data: dict of (name,date,session):SessionDuty"""

        if overwrite:
            self.data.clear()
        self.data.update({key: val if isinstance(val, SessionDuty)
                         else SessionDuty(**val) for key, val in data.items()})
        for day in self.dates:
            for name in self.names:
                for sess in self.sessions:
                    self.data.setdefault((name, day, sess), SessionDuty())

    @property
    def daterange(self):
        mindate = min((key[1] for key in self.data),
                      default=date.today())
        maxdate = max((key[1] for key in self.data),
                      default=date.today())
        return (mindate, maxdate)

    @property
    def dates(self):
        mindate, maxdate = self.daterange
        return [mindate+timedelta(days=i)
                for i in range((maxdate-mindate).days+1)]

    def get_config(self):
        "return configuration options as dict"
        return {
            'names': self.names,
            'minDate': self.daterange[0].isoformat(),
            'maxDate': self.daterange[1].isoformat(),
            'knownDays': max(30, (self.daterange[1]-self.daterange[0]).days+1),
            'pubhols': [ph.isoformat() for ph in self.pubhols]
        }

    def as_dict(self):
        "return datastore as JSON-serializable data"
        data = {}
        for (name, day, sess), sessionduty in self.data.items():
            key=f'{day.isoformat()[0:10]}|{name}|{sess}'
            data[key] = {'duty':sessionduty.duty, 'flags': list(sessionduty.flags)}
        return data

    def setduty(self, name, duty_date, session, duty):
        "Set duty as determined by menu"
        cell = self.data.setdefault(
            (name, date.fromisoformat(duty_date), session), SessionDuty())
        if isinstance(cell, SessionDuty):
            cell.duty = duty
        else:
            raise TypeError('not a dutycell instance')

    def setflag(self, name, duty_date, session, flag, mutex=()):
        "set flag for duty"
        try:
            cell = self.data[(name, duty_date, session)]
        except KeyError:
            return
        cell.flags.add(flag)
        cell.flags.difference_update(mutex)

    def delflag(self, name, duty_date, session, flag):
        "remove flag for duty"
        try:
            cell = self.data[(name, duty_date, session)]
            cell.flags.discard(flag)
        except KeyError:
            return

    def toggleflag(self, name, duty_date, session, flag):
        "toggle flag for duty"
        try:
            cell = self.data[(name, duty_date, session)]
            cell.flags.symmetric_difference_update((flag,))
        except KeyError:
            return

    def set_public_holiday(self, _date, is_holiday=True):
        "set or unset public holiday"
        pubhols: set[date] = self.config.setdefault('pubhols', set())
        if is_holiday:
            pubhols.add(_date)
        else:
            pubhols.discard(_date)

    def save_data(self):
        "Save data to disc"
        self.get_storage_class().save_data(self)

    def load_data(self):
        "load from file"
        try:
            newfile = self.get_storage_class().load_data()
            self.data = newfile.data
            self.config = newfile.config
        except FileNotFoundError:
            warn("Savefile not found")

    def import_clw_csv(self, csvfile: Iterable[str]):
        "import from csv file"
        self.update_data(self.get_storage_class().import_clw_csv(csvfile))
