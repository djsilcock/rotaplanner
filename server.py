"""Webserver module"""

from datetime import date, timedelta
import multiprocessing
import shelve
import sys
import json
import asyncio
import os
import socketio

import sanic

from solver import RotaSolver
from constraints.constraintmanager import get_constraint_config


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


@sio.event
async def connect(sid, environ, auth):
    print('connect ', sid)


@sio.event
async def echo(sid, data):
    print('echo')
    await sio.emit('greeting', {'message': data}, to=sid)

@sio.event
async def show_tallies(sid,datestring):
    """Generate tallies for staff"""
    tallies={}
    names=set()
    with shelve.open('datafile') as db:
        for key in db:
            duty_weekday = date.fromisoformat(key).weekday()
            oncall_type = 'wdoc' if duty_weekday < 4 else 'weoc'
            day_type = 'wddt' if duty_weekday < 5 else 'wedt'
            if key<=datestring:
                tallies[('tot', day_type)] = tallies.get(
                    ('tot', day_type), 0)+1
                tallies[('tot', oncall_type)] = tallies.get(
                    ('tot', oncall_type), 0)+1
                for name,duty in db[key].get('DAYTIME',{}).items():
                    names.add(name)
                    if duty in ['DEFINITE_ICU','ICU']:
                        tallies[(name,day_type)]=tallies.get((name,day_type),0)+1
                        
                for name, duty in db[key].get('ONCALL', {}).items():
                        if duty in ['DEFINITE_ICU', 'ICU']:
                            tallies[(name, oncall_type)] = tallies.get(
                                (name, oncall_type), 0)+1
                            

    rows = [f'|{name}|{"|".join([str(tallies.get((name,duty),0)) for duty in ["wddt","wedt","wdoc","weoc"]])}|' for name in names]
    targets = f'|Targets|{"|".join([str(tallies.get(("tot",duty),0)//9) for duty in ["wddt","wedt","wdoc","weoc"]])}|'

    message="\n".join([
        '| |Wkday day|Wkend day|Wkday oc|Wkend oc|',
        '|---|---|---|---|---|',
        targets,
        "\n".join(rows),
        ""])
    await sio.emit('report', {'message': f"""Tallies for:{datestring} \n\n{message}"""})


async def recalculate(data):
    """Run recalculation as background task"""
    await sio.emit('message', {'message': 'recalculating...'})
    localpipe, remotepipe = multiprocessing.Pipe()
    startdate = min(*data.keys())
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
    await sio.emit('reload', {})
    print('sent reload signal')


@app.post("backend/recalculate")
async def testserver(request):
    '''run query'''
    with shelve.open('datafile') as database:
        data = {}
        data.update(database)
    request.app.add_task(recalculate(data))
    return sanic.response.json({'status': 'accepted'}, status=202)


@app.get('backend/constraintdefs')
async def settings(request):
    """returns constraint definitions for form"""
    return sanic.response.json(get_constraint_config())


@app.get('backend/constraints')
async def get_constraints(request):
    """return list of current constraints"""
    with open('constraints.json', encoding='utf-8') as constraint_file:
        constraints = json.load(constraint_file)
    return sanic.response.json(constraints)


@app.post('backend/constraints')
async def save_constraints(request):
    """save the constraints list from the ui"""
    data = request.json
    with open('constraints.json', 'w', encoding='utf-8') as constraint_file:
        json.dump(data, constraint_file, indent=2)
    return sanic.response.json({'status': 'OK'})


@app.get('backend/getduties/<day:str>')
async def get_day(request, day):
    """Get duties for day"""
    with shelve.open('datafile') as db:
        day_data = db.get(day, {})
    # print(f"{day}:{repr(day_data)}")
    return sanic.response.json({
        'result': day_data})


@app.post('backend/setduty')
async def set_duty(request):
    """Update duty for shift"""
    json_request = request.json
    shift = json_request['shift']
    name = json_request['name']
    day = json_request['day']
    duty = json_request['duty']
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
        shift_allocs[name] = duty
        day_data = {}
        day_data.update(day_allocs)
    return sanic.response.json(
        {'result': day_data})

app.static('/', os.path.join(os.getcwd(), 'rotaplanner', 'out','index.html')) 
app.static('/_next',os.path.join(os.getcwd(),'rotaplanner','out','_next'))

if __name__ == "__main__":
    app.run(auto_reload=True)
