import csv
from datetime import date
import pickle

from datatypes import DutyCell,SessionDuty 


def import_clw_csv(csvfile):
    data: dict[tuple, DutyCell] = {}
    with open(csvfile, 'rt', encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            key = (r['Person'], date.fromisoformat(r['Date']))
            cell = data.setdefault(key, DutyCell(duties={}))
            cell.duties[r['Session']] = SessionDuty(r['Location'])
    return data


def save_data(data):
    "Save data to disc"
    with open('savefile', 'wb') as f:
        pickle.dump(data, f)


def load_data():
    "load from file"
    with open('savefile', 'rb') as f:
        return pickle.load(f)
