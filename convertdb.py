import sqlite3
import json
import shelve

def get_duties():
    with shelve.open('datafile') as db:
        for date in db:
            for shift in db[date]:
                for name in db[date][shift]:
                    duty=db[date][shift][name]
                    yield (date,shift,name,duty)

def get_constraints():
    with open('constraints.json') as f:
        constraints=json.load(f)
    for constraint_type,rules in constraints.items():
        for ruleid,rule in rules.items():
            yield (constraint_type,ruleid,json.dumps(rule))

with sqlite3.connect('datafile.db') as conn:
    cur=conn.cursor()
    cur.execute('create table duties (date,shift,name,duty)')
    cur.executemany('insert into duties (date,shift,name,duty) values (?,?,?,?)',get_duties())
    cur.execute('create table constraints (constraint_type,rule_id,rule)')
    cur.executemany('insert into constraints (constraint_type,rule_id,rule) values (?,?,?)',get_constraints())
    cur.execute('create unique index idx on duties (date,shift,name)')
    cur.execute('create unique index idx2 on constraints (constraint_type,rule_id)')
