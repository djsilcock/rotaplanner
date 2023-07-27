import csv
from datetime import date
import pickle

from datatypes import SessionDuty 


def import_clw_csv(csvfile):
    data: dict[tuple, SessionDuty] = {}
    reader = csv.DictReader(csvfile)
    for r in reader:
        key = (r['Person'], date.fromisoformat(r['Date']),r['Session'])
        data[key]=SessionDuty(r['Location'])
    return data


def save_data(data):
    "Save data to disc"
    with open('datafile', 'wb') as f:
        pickle.dump(data, f)


def load_data():
    "load from file"
    with open('datafile', 'rb') as f:
        return pickle.load(f)
