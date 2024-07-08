import csv
import contextlib



def import_clw_csv(csvfile):
    raise NotImplementedError
    data: dict[tuple, SessionDuty] = {}
    reader = csv.DictReader(csvfile)
    for r in reader:
        #todo
        pass
    return data

@contextlib.contextmanager
def full_save():
    "Save data to disc"
    with open('datafile', 'wb') as f:
        yield f

@contextlib.contextmanager        
def incremental_save():
    with open('datafile','ab') as f:
        yield f

@contextlib.contextmanager
def load():
    with open('datafile','rb') as f:
        yield f

