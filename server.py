import multiprocessing
import sys
import json
import asyncio
import os.path
import datetime
import socketio

import sanic
from tinydb import TinyDB,Query, where
from constants import Duties, Shifts, Staff
from solver import RotaSolver
from constraints.constraintmanager import get_constraint_config
import pusher

pusher_client = pusher.Pusher(
    app_id='1418967',
    key='d5b9dd3a90ae13c7c36f',
    secret='ff0a2177dc2d9e0ffec2',
    cluster='eu',
    ssl=True
)

app = sanic.Sanic('RotaSolver')
app.ctx.db=TinyDB('datafile.json')

def launch_solver(pipe):
    """Launches solver task"""

    rota = RotaSolver(rota_cycles=4,
                      slots_on_rota=9, people_on_rota=8, startdate='2022-05-02', pipe=pipe)
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


@app.post('/log')
async def logfile(request):
    print(request.json)
    return sanic.response.json({'response': 'OK'})

async def recalculate(data,queue):
    """Run recalculation as background task"""
    localpipe, remotepipe = multiprocessing.Pipe()
    process = multiprocessing.Process(
        target=launch_solver, args=(remotepipe,))
    process.start()

    # remap data

    with open('constraints.json', 'r', encoding='utf-8') as constraintsfile:
        constraints = json.load(constraintsfile)
        for (constraint, defs) in constraints.items():
            for (constraintid, constraintparams) in defs.items():
                if constraintparams.get('enabled'):
                    localpipe.send(dict(
                        constraintparams, type='constraint', constraint=constraint, id=constraintid))
    localpipe.send({
        'type': 'constraint',
        'constraint': 'apply_leavebook',
        'id': 'x-leavebook',
        'current_rota': data
    })

    localpipe.send({'type': 'solve'})
    try:
        while True:
            if localpipe.poll():
                data = localpipe.recv()
                await queue.put(data)
                if data['type'] == 'eof':
                    await queue.put('EOF')
                    localpipe.send({'type': 'exit'})
                    break
            else:
                await asyncio.sleep(0.1)
    except EOFError:
        print('pipe was closed')

@app.post("backend/recalculate")
async def testserver(request):
    '''run query'''
    data=request.app.ctx.db.all()
    response = await request.respond(content_type="text/plain", headers={'x-accel-buffering': 'no'})
    queue=asyncio.Queue()
    request.app.add_task(recalculate(data,queue))
    while True:
        chunk=await queue.get()
        if chunk=='EOF':
            break
        elif isinstance(chunk,dict):
            actiontype=chunk.pop('type',None)
            if actiontype=='result':
                request.app.ctx.db.upsert(
                    {
                        'name':chunk['name'],
                        'shift':chunk['shift'],
                        'day':chunk['day'],
                        'duty':chunk['duty']
                    },
                    (where('name')==chunk['name'])&
                    (where('shift')==chunk['shift'])&
                    (where('day')==chunk['day']))
            else:
                pusher_client.trigger('my-channel', 'my-event',
                                  chunk)
            
    pusher_client.trigger('my-channel','my-event',{'status':'done'})
    await response.eof()



@app.get('backend/constraintdefs')
async def settings(request):
    """returns constraint definitions for form"""
    return sanic.response.json(get_constraint_config())


@app.get('backend/constraints')
async def get_constraints(request):
    """return list of current constraints"""
    with open('constraints.json') as constraint_file:
        constraints = json.load(constraint_file)
    return sanic.response.json(constraints)


@app.post('backend/constraints')
async def save_constraints(request):
    """save the constraints list from the ui"""
    data = request.json
    with open('constraints.json', 'w', encoding='utf-8') as constraint_file:
        json.dump(data, constraint_file,indent=2)
    return sanic.response.json({'status': 'OK'})

@app.get('backend/getduties/<day:int>')
async def get_day(request,day):
    """Get duties for day"""
    db=request.app.ctx.db
    return sanic.response.json({
        'result': {f"{duty['name']}-{duty['shift']}": duty['duty']
            for duty in db.search(where('day') == day)}})

@app.post('backend/setduty')
async def set_duty(request):
    """Update duty for shift"""
    json_request=request.json
    db = request.app.ctx.db
    Duty=Query()
    shift=json_request['shift']
    name=json_request['name']
    day=json_request['day']
    duty=json_request['duty']
    if duty in ['DEFINITE_ICU','DEFINITE_LOCUM_ICU']:
        db.update({'duty':None},(
            Duty.day==day
            )&(
            Duty.shift==shift
            )&(
            Duty.duty.one_of([
                'DEFINITE_ICU',
                'ICU',
                'LOCUM_ICU',
                'DEFINITE_LOCUM_ICU'
                ])))
    db.upsert({
        'shift':shift,
        'name':name,
        'day':day,
        'duty':duty
        },
        (Duty.shift==shift)&(Duty.day==day)&(Duty.name==name)
        )
    return sanic.response.json(
        {'result':{f"{duty['name']}-{duty['shift']}":duty['duty'] 
            for duty in db.search(where('day') == day)}})

@app.websocket('/backend/feed')
async def feed(request, ws):
    print('websocket connected')
    while True:
        data = "hello!"
        await ws.send(data)
        await asyncio.sleep(3)

app.static('/', os.path.join(os.getcwd(), 'rotaplanner', 'out','index.html'))
app.static('/',os.path.join(os.getcwd(),'rotaplanner','out'))

if __name__ == "__main__":
    app.run(dev=True)
    # asyncio.run(test())
