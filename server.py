"""Webserver module"""


from datetime import date,timedelta
from importlib import import_module
import multiprocessing
import shelve

import subprocess
import sys
import json
import asyncio
import os
import webbrowser
import socketio

import sanic
from sanic.signals import Event
from constants import Duties, Shifts, Staff
from solver import RotaSolver


app = sanic.Sanic('RotaSolver')
sio = socketio.AsyncServer(async_mode='sanic')
sio.attach(app)


def launch_solver(pipe, startdate, enddate):
    """Launches solver task"""
    rota = RotaSolver(
        slots_on_rota=9,
        people_on_rota=8,
        pipe=pipe,
        startdate=startdate,
        enddate=enddate)
    rota.apply_base_rules()
    while True:
        message = pipe.recv()
        messagetype = message.pop('type')
        if messagetype == 'constraint':
            rota.apply_constraint(message)
        if messagetype == 'solve':
            rota.solve()
        if messagetype == 'exit':
            sys.exit()


def show_tallies(payload):
    """Generate tallies for staff"""
    datestring = payload
    tallies = {}
    names = set()
    with shelve.open('datafile') as db:
        for key in db:
            duty_weekday = date.fromisoformat(key).weekday()
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

    rows = [
        f'|{name}|{"|".join([str(tallies.get((name,duty),0)) for duty in ["wddt","wedt","wdoc","weoc"]])}|' for name in names]
    targets = f'|Targets|{"|".join([str(tallies.get(("tot",duty),0)//9) for duty in ["wddt","wedt","wdoc","weoc"]])}|'

    message = "\n".join([
        '| |Wkday day|Wkend day|Wkday oc|Wkend oc|',
        '|---|---|---|---|---|',
        targets,
        "\n".join(rows),
        ""])
    return f"Tallies for:{datestring} \n\n{message}"


async def do_recalculate(data, startdate):
    """Run recalculation as background task"""
    await sio.emit('message', {'message': 'recalculating...'})
    localpipe, remotepipe = multiprocessing.Pipe()
    #startdate = min(*data.keys())
    enddate = max(*data.keys())
    process = multiprocessing.Process(
        target=launch_solver, args=(remotepipe, startdate, enddate))
    process.start()
    # remap data
    with open('constraints.json', 'r', encoding='utf-8') as constraintsfile:
        constraints = json.load(constraintsfile)
        for (constraint, defs) in constraints.items():
            for (constraintid, constraintparams) in defs.items():
                if constraintparams.get('enabled'):
                    localpipe.send(dict(
                        constraintparams,
                        type='constraint',
                        constraint=constraint,
                        id=constraintid))
    localpipe.send({
        'type': 'constraint',
        'constraint': 'apply_leavebook',
        'id': 'x-leavebook',
        'current_rota': data
    })

    localpipe.send({'type': 'solve'})
    try:
        d = {}
        while True:
            if localpipe.poll():
                data = localpipe.recv()
                if data['type'] == 'eof':
                    localpipe.send({'type': 'exit'})
                    break
                actiontype = data.pop('type', None)
                if actiontype == 'result':
                    d.setdefault(data['day'], {}).setdefault(
                        data['shift'], {})[data['name']] = data['duty']

                else:
                    await sio.emit(actiontype, data)
            else:
                await asyncio.sleep(0.01)
    except EOFError:
        print('pipe was closed')
    with shelve.open('datafile') as database:
        database.update(d)


@app.post('/recalculate')
def recalculate(request):
    '''run query'''
    try:
        start_date = request.json.get('start_date')
        date.fromisoformat(start_date)
    except ValueError:
        return sanic.response.json({'error': 'start date is invalid'}, status=400)
    with shelve.open('datafile') as database:
        data = {}
        data.update(database)
    app.add_task(do_recalculate(data, start_date))



status = {1: False}


@sio.event
def connect(*args):
    print(f'hello {args}')
    status[1] = True


# @sio.event
async def disconnect(*sid):
    print('bye')
    status[1] = False
    await asyncio.sleep(5)
    if status[1] == False:
        app.stop()


@app.signal(Event.SERVER_INIT_AFTER)
def launcher(app, loop):
    try:
        subprocess.run('start msedge --app="{}"'.format('http://localhost:8000'),
                       stdout=sys.stdout, stderr=sys.stderr, stdin=subprocess.PIPE, shell=True, check=True)
    except:
        webbrowser.open('http://localhost:8000')


@app.signal(Event.SERVER_SHUTDOWN_AFTER)
def shutdown(app, loop):
    sys.exit(0)


@app.get('/')
def index(request):
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
def statusmessage(request):
    return sanic.response.json({})


@app.get('/duties/<startdate:ymd>')
def get_duties(request, startdate):
    "return duties for date range"
    days_to_display = int(request.args.get('days', 16*7))
    print(type(startdate))

    days_array = [(startdate+timedelta(days=daydelta)).isoformat()
                  for daydelta in range(days_to_display)]
    staff=sorted([e.name for e in Staff])
    with shelve.open('datafile') as db:
        duties = dict([(day, db.get(day))
                       for day in days_array if day in db])
        
    return sanic.response.json({'days': days_array, 'names': staff, 'duties': duties})


@app.post('/setduty')
def set_duty(request):
    """Update duty for shift"""
    args = request.json
    try:
        duty = args['duty']
        shift = args['shift']
        staff = args['staff']
        day = args['date']
    except KeyError as err:
        return sanic.response.json({
            'status':'error',
            'message':f'Missing value:{err.args}'},status=400)
    try:
        Duties[duty]
        Staff[staff]
        Shifts[shift]
        date.fromisoformat(day)
    except (ValueError, KeyError) as err:
        return sanic.response.json({
            'status': 'error',
            'message': f'Missing value:{err.args}'}, status=400)

    print(f'set duty: {duty},{shift},{staff},{day}')
    with shelve.open('datafile', writeback=True) as database:
        day_allocs = database.setdefault(day, {})
        shift_allocs = day_allocs.setdefault(shift, {})
        if duty in ['DEFINITE_ICU', 'DEFINITE_LOCUM_ICU', 'ICU_MAYBE_LOCUM']:
            shift_allocs.update({
                name1: (None if duty1 in [
                    'ICU',
                    'LOCUM_ICU',
                    'DEFINITE_ICU',
                    'DEFINITE_LOCUM_ICU',
                    'ICU_MAYBE_LOCUM'] else duty1)
                for name1, duty1 in shift_allocs.items()})
        shift_allocs[staff] = duty
    return sanic.response.empty()


@app.get('/getconstraints')
def get_constraints(request):
    """return list of current constraints"""
    with open('constraints.json', encoding='utf-8') as constraint_file:
        constraints = json.load(constraint_file)
    constraint_config = []
    for constraint_type, constraint_rules in constraints.items():
        constraint_class = import_module(
            f'constraints.{constraint_type}').Constraint
        constraint_config.append(
            {'title': constraint_class.name,
             'rules': constraint_rules,
             'addButton': constraint_class.is_configurable})

        return sanic.response.json(constraint_config)


def do_validate_constraint(constraint):
    return None


@app.post('/validateconstraint')
def validate_constraint(request):
    constraint = request.json
    validated = do_validate_constraint(constraint)
    if validated:
        return sanic.response.json({'status': 'error', 'errors': validated})
    return sanic.response.json({'status': 'ok'})


@app.post('/saveconstraints')
def save_constraints(request):
    all_constraints = request.json
    has_error = False
    validated_constraints = {}
    for (constraint_type, constraints_by_type) in all_constraints.items():
        validated_constraints[constraint_type] = {}
        for (constraint_id, constraint) in constraints_by_type.items():
            validated_constraints[constraint_type][constraint_id] = do_validate_constraint(
                constraint)
            if validated_constraints[constraint_type][constraint_id].get('error', None):
                has_error = True
    if not has_error:
        with open('constraints.json', 'w', encoding='utf-8') as constraint_file:
            json.dump(validated_constraints, constraint_file, indent=2)
            return sanic.response.json({'status': 'ok'})
    return sanic.response.json({'status': 'error', 'constraints': validated_constraints})


if __name__ == "__main__":
    print(os.path.join(os.getcwd(), 'static'))
    app.run(dev=True)
