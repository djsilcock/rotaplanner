import tinydb
from datetime import date,timedelta

from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware

db1=tinydb.TinyDB('datafile.json.bak')
db2 = tinydb.TinyDB('datafile.json', storage=CachingMiddleware(JSONStorage))

def update(record):
    newdate=(date(2020, 11 , 2)+timedelta(days=record['day'])).isoformat()
    record['day']=newdate
    return record

with db2 as db2a:
    for record in db1.all():
        db2a.insert(update(record))
