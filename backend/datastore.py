from dataclasses import asdict
from typing import Iterable
from warnings import warn
from datetime import date, timedelta
from datatypes import SessionDuty
import storage as default_storage


class DataStore:
    def __init__(self, storage=default_storage):
        self.data: dict[tuple, SessionDuty] = {}
        self.names = []
        self.dates = []
        self.sessions = ('am', 'pm', 'eve', 'night')
        self.pubhols = set()
        self.storage = storage

    def update_data(self, data, overwrite=False):
        """update duty data in sheet
        data: dict of (name,date):DutyCell"""
        if overwrite:
            self.data.clear()
        self.data.update(data)
        mindate = min((key[1] for key in self.data),
                      default=date.today())
        maxdate = max((key[1] for key in self.data),
                      default=date.today())
        self.dates = [mindate+timedelta(days=i)
                      for i in range((maxdate-mindate).days+1)]
        self.names = sorted({d[0] for d in self.data})
        for day in self.dates:
            for name in self.names:
                for sess in self.sessions:
                    self.data.setdefault((name, day, sess), SessionDuty())

    def get_config(self):
        return {
            'names': self.names,
            'minDate': min(self.dates).isoformat(),
            'maxDate': max(self.dates).isoformat(),
            'dates': [d.isoformat() for d in self.dates],
            'pubhols': [ph.isoformat() for ph in self.pubhols]
        }

    def as_dict(self):
        data = {}
        for (name, day, sess), sessionduty in self.data.items():
            data[f'{day.isoformat()[0:10]}|{name}|{sess}'] = asdict(sessionduty)
        return data

    def setduty(self, name, d, session, duty):
        "Set duty as determined by menu"
        cell = self.data.get((name, date.fromisoformat(d), session))
        if isinstance(cell, SessionDuty):
            cell.duty = duty
        else:
            raise TypeError('not a dutycell instance')

    def setflag(self, name, d, session, flag, mutex=()):
        try:
            cell = self.data[(name, d, session)]
        except KeyError:
            return
        cell.flags.add(flag)
        cell.flags.difference_update(mutex)

    def delflag(self, name, d, session, flag):
        try:
            cell = self.data[(name, d, session)]
            cell.flags.remove(flag)
        except KeyError:
            return

    def toggleflag(self, name, d, session, flag):
        try:
            cell = self.data[(name, d, session)]
            cell.flags.symmetric_difference_update((flag,))
        except KeyError:
            return

    def save_data(self):
        "Save data to disc"
        self.storage.save_data(self.data)

    def load_data(self):
        "load from file"
        try:
            self.update_data(self.storage.load_data(), overwrite=True)
        except FileNotFoundError:
            warn("Savefile not found")

    def import_clw_csv(self, csvfile: Iterable[str]):
        "import from csv file"
        self.update_data(self.storage.import_clw_csv(csvfile))
