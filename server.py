"""Webserver module"""


from collections import namedtuple
from contextlib import contextmanager
import datetime
import itertools
import shelve
import sqlite3

import subprocess
import sys
import json
import asyncio
import os
from typing import List, Tuple
import webbrowser
import socketio

import sanic
from sanic.signals import Event
from constants import Duties, Shifts, Staff
from solver import RotaSolver

from constraints.constraintmanager import get_constraint_class


app = sanic.Sanic('RotaSolver')
sio = socketio.AsyncServer(async_mode='sanic')
sio.attach(app)


def show_tallies(payload):
    """Generate tallies for staff"""
    datestring = payload
    tallies = {}
    names = set()
    with shelve.open('datafile') as db:
        for key in db:
            duty_weekday = datetime.date.fromisoformat(key).weekday()
            oncall_type = 'wdoc' if duty_weekday < 4 else 'weoc'
            day_type = 'wddt' if duty_weekday < 5 else 'wedt'
            if key <= datestring:
                tallies[('tot', day_type)] = tallies.get(
                    ('tot', day_type), 0)+1
                tallies[('tot', oncall_type)] = tallies.get(
                    ('tot', oncall_type), 0)+1
                for name, duty in db[key].get('DAYTIME', {}).items():
                    names.add(name)
                    if duty in ['DEFINITE_ICU', 'ICU']:
                        tallies[(name, day_type)] = tallies.get(
                            (name, day_type), 0)+1

                for name, duty in db[key].get('ONCALL', {}).items():
                    if duty in ['DEFINITE_ICU', 'ICU']:
                        tallies[(name, oncall_type)] = tallies.get(
                            (name, oncall_type), 0)+1
    oncall_types = ["wddt", "wedt", "wdoc", "weoc"]
    rows = [
        f'|{name}|{"|".join([str(tallies.get((name,duty),0)) for duty in oncall_types])}|'
        for name in names]
    targets = "|".join([str(tallies.get(("tot", duty), 0)//9)
                       for duty in oncall_types])

    message = "\n".join([
        '| |Wkday day|Wkend day|Wkday oc|Wkend oc|',
        '|---|---|---|---|---|',
        f'|Targets|{targets}|',
        "\n".join(rows),
        ""])
    return f"Tallies for:{datestring} \n\n{message}"


# Database utils

@contextmanager
def database_cursor(*fields):
    "open database and return cursor as context manager"
    conn = sqlite3.connect('datafile.db')
    if len(fields)>0:
        row_factory=namedtuple('Row',fields)
        conn.row_factory = row_factory._make
    cursor = conn.cursor()
    yield cursor
    cursor.close()
    conn.close()


def get_constraints_from_db():
    "fetch constraints from db"
    with database_cursor() as cursor:
        cursor.execute('select constraint_type,rule_id,rule '
                       'from constraints order by constraint_type,rule_id')
        constraintlist = cursor.fetchall()
    return [
        {'type': constraint_type,
         'id': rule_id,
         **json.loads(rule)}
        for constraint_type, rule_id, rule in constraintlist]


INSERT_DUTY_SQL = ('insert into duties (date,shift,name,duty) values (?,?,?,?) ' +
                   'on conflict (date,shift,name) do update set duty=excluded.duty')
INSERT_CONSTRAINT_SQL = ('insert into constraints (constraint_type,rule_id,rule) values (?,?,?) ' +
                         'on conflict (constraint_type,rule_id) do update set rule=excluded.rule')


def update_duties(updates: List[Tuple[str, str, str, str]]):
    """update list of duties
    :param updates - list of (date,shift,name,duty) tuples
    """
    with database_cursor() as cursor:
        cursor.execute('begin')
        cursor.executemany(INSERT_DUTY_SQL, updates)
        cursor.execute('commit')


def update_constraints(constraints: List[Tuple[str, str, str]]):
    """update list of constraints
    :param updates - list of (constraint_type,constraint_id,rule,duty) tuples
    """
    with database_cursor() as cursor:
        cursor.execute('begin')
        cursor.executemany(INSERT_CONSTRAINT_SQL,
                           [(constraint_type, rule_id, json.dumps(rule))
                            for constraint_type, rule_id, rule in constraints])
        cursor.execute('commit')


def set_duty_in_db(date, shift, name, duty):
    "sets single duty and enforces only one person may be in ICU"
    with database_cursor() as cursor:
        cursor.execute('begin')
        if 'ICU' in duty:
            cursor.execute('delete from duties '
                           'where date=? and shift=? and duty like "%ICU%"', (date, shift))
        cursor.execute(INSERT_DUTY_SQL, (date, shift, name, duty))
        cursor.execute('commit')


def get_duties_from_db(startdate, days_to_display):
    "get data from database"
    with database_cursor('date','shift','name','duty') as cursor:
        cursor.execute('select date,shift,name,duty'
                       ' from duties where date>= ? and date < ? order by date,shift,name', (
                           startdate.isoformat(),
                           (startdate +
                           datetime.timedelta(days=days_to_display)).isoformat()
                       ))
        data = cursor.fetchall()
    return data


abort_current = {'abort': lambda: None}


async def do_recalculate(data, startdate):
    """Run recalculation as background task"""
    enddate = max(*data.keys())
    constraints = get_constraints_from_db()
    constraints.append({
        'type': 'apply_leavebook',
        'id': 'x-leavebook',
        'current_rota': data
    })
    abort_current['abort']()
    rota = RotaSolver(
        slots_on_rota=9,
        people_on_rota=8,
        startdate=startdate,
        enddate=enddate)
    for constraint in constraints:
        rota.apply_constraint(constraint)
    abort_current['abort'], results = rota.solve()
    duties = []
    async for data in results:
        actiontype = data.pop('type', None)
        if actiontype == 'result':
            duties.append((data['day'], data['shift'],
                           data['name'], data['duty']))
        else:
            await sio.emit(actiontype, data)
    update_duties(duties)


@app.post('/recalculate')
def recalculate(request):
    '''run query'''
    try:
        start_date = request.json.get('start_date')
        datetime.date.fromisoformat(start_date)
    except ValueError:
        return sanic.response.json({'error': 'start date is invalid'}, status=400)
    with shelve.open('datafile') as database:
        data = {}
        data.update(database)
    app.add_task(do_recalculate(data, start_date))


status = {1: False}


@sio.event
def connect(*args):
    "Socket connect"
    print(f'hello {args}')
    status[1] = True


# @sio.event
async def disconnect(*_):
    "socket disconnect"
    print('bye')
    status[1] = False
    await asyncio.sleep(5)
    if not status[1]:
        app.stop()


#@app.signal(Event.SERVER_INIT_AFTER)
def launcher(**_):
    "launch web browser"
    try:
        url = 'http://localhost:8000'
        subprocess.run(f'start msedge --app="{url}"',
                       stdout=sys.stdout, stderr=sys.stderr, stdin=subprocess.PIPE,
                       shell=True, check=True)
    except subprocess.SubprocessError:
        webbrowser.open('http://localhost:8000')


@app.signal(Event.SERVER_SHUTDOWN_AFTER)
def shutdown(*_):
    "shutdown after browser exit"
    sys.exit(0)


@app.get('/')
def index(_):
    "returns html skeleton page"
    return sanic.response.html(
        "<!DOCTYPE html><html><head><title>Rota Solver</title></head>"
        "<body>"
        '<div id="target">Loading...</div>'
        f"<script>window.initialData={json.dumps({})}</script>"
        '<script src="/static/script.js"></script>'
        '</body></html>')


app.static('/static', os.path.join(os.getcwd(), 'static'))


@app.get('/statusmessage')
def statusmessage(_):
    "returns status message"
    # TODO: implement statusmessage
    return sanic.response.json({})


@app.get('/duties/<startdate:ymd>')
def get_duties(request, startdate):
    "return duties for date range"
    days_to_display = int(request.args.get('days', 16*7))
    days_array = [(startdate+datetime.timedelta(days=daydelta)).isoformat()
                  for daydelta in range(days_to_display)]
    staff = sorted([e.name for e in Staff])
    duties = {}
    for duty in get_duties_from_db(startdate, days_to_display):
        duties.setdefault(duty.date, {}).setdefault(
            duty.shift, {})[duty.name] = duty.duty
    return sanic.response.json({'days': days_array, 'names': staff, 'duties': duties})


@app.post('/setduty')
def set_duty(request):
    """Update duty for shift"""
    args = request.json
    try:
        duty = Duties[args['duty']].name
        shift = Shifts[args['shift']].name
        staff = Staff[args['staff']].name
        date = args['date']
        datetime.date.fromisoformat(date)
    except (KeyError, ValueError) as err:
        return sanic.response.json({
            'status': 'error',
            'message': f'Missing or invalid value:{err.args[0]}'}, status=400)
    print(f'set duty: {duty},{shift},{staff},{date}')
    set_duty_in_db(date, shift, staff, duty)
    return sanic.response.empty()


@app.get('/getconstraints')
def get_constraints(_):
    """return list of current constraints"""
    constraintslist = get_constraints_from_db()
    constraint_config = {}
    for constraint_type, constraint_rules in itertools.groupby(
            constraintslist, lambda c: c['type']):
        constraint_class = get_constraint_class(constraint_class)
        constraint_config[constraint_type] = {
            'title': constraint_class.name,
            'rules': {c.id: c for c in constraint_rules},
            'addButton': constraint_class.is_configurable}
    return sanic.response.json(constraint_config)


@app.post('/getconstraintinterface')
def constraint_interface(request):
    "generate constraint interface from values"
    config = request.json

    def error(msg):
        return sanic.response.json({'status': 'error', 'message': msg}, status=400)
    if not isinstance(config, dict):
        return error('payload must be json object')
    constraint_type = config.get('type', None)
    if constraint_type is None:
        return error('No constraint_type field')
    constraint_class = get_constraint_class(constraint_type)
    if constraint_class is None:
        return error(f'Unknown constraint type {constraint_type}')
    config_class = constraint_class.config_class(config)
    return sanic.response.json({
        'status': 'ok',
        'errors': config_class.errors(),
        'interface': config_class.get_config_interface()
    })


@app.post('/saveconstraints')
def save_constraints(request):
    "Save constraints to db"
    all_constraints = request.json
    flattened_constraints = [
        (constraint_type, constraint_id, constraint_spec)
        for constraint_type, constraints_by_type in all_constraints.items()
        for constraint_id, constraint_spec in constraints_by_type.items()
    ]

    for constraint_type, constraint_id, constraint in flattened_constraints:
        constraint_class = get_constraint_class(constraint_type)
        if constraint_class is None:
            return sanic.response.json({
                'status': 'error',
                'error': f'unknown constraint type {constraint_type}'}, status=400)
        if constraint_class.config_class(constraint).errors():
            return sanic.response.json({
                'status': 'error',
                'error': f'error in {constraint_type} spec'}, status=400)
    update_constraints(flattened_constraints)
    return sanic.response.json({'status': 'ok'})


if __name__ == "__main__":
    print(os.path.join(os.getcwd(), 'static'))
    app.run(dev=True)
