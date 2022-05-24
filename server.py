import multiprocessing
import sys
import json
import asyncio
import os.path
import datetime

import sanic
from constants import Duties, Shifts, Staff
from solver import RotaSolver
from constraints.constraintmanager import get_constraint_config


app = sanic.Sanic('RotaSolver')


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

   

@app.post("/recalculate")
async def testserver(request):
    '''run query'''
    data = request.json
    if data.get('lastsaved',None):
        most_recent_filename = sorted(os.listdir('savedrotas'))[-1]
        response = await request.respond(content_type='text/eventstream')
        with open(os.path.join('savedrotas',most_recent_filename), 'r', encoding='utf-8') as savefile:
            for f in savefile:
                await response.send(f)
        await response.eof()
        return

    response = await request.respond(content_type="text/plain", headers={'x-accel-buffering': 'no'})

    localpipe, remotepipe = multiprocessing.Pipe()
    process = multiprocessing.Process(
        target=launch_solver, args=(remotepipe,))
    process.start()

    # remap data
    leavebook = {}

    for staff_str in data:
        staff = Staff[staff_str.upper()]
        for shift_str in data[staff_str]:
            shift = Shifts[shift_str.upper()]
            for day_str in data[staff_str][shift_str]:
                day = int(day_str)
                duty = data[staff_str][shift_str][day_str]
                if duty == 'DEFINITE_ICU':
                    leavebook[(staff, shift, day)]=Duties.ICU
                elif duty == 'LEAVE' or duty == 'NOC':
                    leavebook[(staff, shift, day)]=Duties.LEAVE

    with open('constraints.json', 'r', encoding='utf-8') as constraintsfile:
        constraints=json.load(constraintsfile)
        for (constraint,defs) in constraints.items():
            for (constraintid,constraintparams) in defs.items():
                if constraintparams.get('enabled'):
                    localpipe.send(dict(constraintparams, type='constraint',constraint=constraint,id=constraintid))
    localpipe.send({
        'type': 'constraint',
        'constraint': 'apply_leavebook',
        'id': 'x-leavebook',
        'leavebook': leavebook

    })
    
    localpipe.send({'type': 'solve'})
    try:
        with open(os.path.join('savedrotas',datetime.datetime.now().isoformat(timespec='seconds')),'w',encoding='utf-8') as savefile:
            for ((staff,shift,day),duty) in leavebook.items():
                data ={'type': 'duty',
                     'dutyType': 'DEFINITE_ICU' if duty.name=='ICU' else duty.name,
                     'day': day,
                     'shift': shift.name,
                     'name': staff.name}
                print (json.dumps(data),file=savefile)
            while True:
                if localpipe.poll():
                    data = localpipe.recv()
                    await response.send(json.dumps(data))
                    await response.send('\n')
                    print(json.dumps(data),file=savefile)
                    if data['type'] == 'eof':
                        print('exiting naturally')
                        localpipe.send({'type': 'exit'})
                        break
                else:
                    await asyncio.sleep(0.1)
    except EOFError:
        print('pipe was closed')

    print('done')
    await response.eof()



@app.get('/constraintdefs')
async def settings(request):
    """returns constraint definitions for form"""
    return sanic.response.json(get_constraint_config())


@app.get('/constraints')
async def get_constraints(request):
    """return list of current constraints"""
    with open('constraints.json') as constraint_file:
        constraints = json.load(constraint_file)
    return sanic.response.json(constraints)


@app.post('/constraints')
async def save_constraints(request):
    """save the constraints list from the ui"""
    data = request.json
    with open('constraints.json', 'w', encoding='utf-8') as constraint_file:
        json.dump(data, constraint_file,indent=2)
    return sanic.response.json({'status': 'OK'})


if __name__ == "__main__":
    app.run(debug=True)
    # asyncio.run(test())
