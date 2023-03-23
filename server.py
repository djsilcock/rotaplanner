"""Webserver module"""


import asyncio
import datetime
import threading
import uuid

import subprocess
import sys
import json
import os
import webbrowser
import pathlib

import sanic
import sanic.response
from sanic_ext import render,Config
from sanic.signals import Event
from database import get_sessionmaker
from solver import solve
"""from config import Shifts,Staff
from solver import RotaSolver
from database import (
    get_tallies_from_db,
    get_constraints_from_db,
    update_duties,
    update_constraint,
    set_duty_in_db,
    get_duties_from_db,
    get_single_constraint_from_db)""
from constraints import get_constraint_class""
from constraints.constraint_store import get_all_template_folders"""

def get_all_template_folders():
    return []

app = sanic.Sanic('RotaSolver')
app.config.WTF_CSRF_ENABLED=False
app.extend(config=Config(templating_path_to_templates=[
    pathlib.Path(__file__).with_name('templates'),
    *get_all_template_folders()]))

app.ctx.sessionmaker=get_sessionmaker()

@app.get('/gettallies/<finishdate:ymd>')
def show_tallies(_,finishdate):
    """Generate tallies for staff"""
    tallies=get_tallies_from_db(finishdate)
    names=set(k[0] for k in tallies)
    oncall_types = ["wddt", "wedt", "wdoc", "weoc"]
    totals={shift_type:sum(tally for (key,tally) in tallies.items() if key[1]==shift_type) 
                for shift_type in oncall_types }
    rows = [dict(name='Target',**{duty:totals[duty]//9
                           for duty in oncall_types})]
    rows.extend([dict(name=name,**{duty:tallies.get((name,duty),0) for duty in oncall_types})
        for name in names])
    return sanic.response.json(rows)


message_queue=asyncio.Queue()

async def do_recalculate(startdate,db):
    """Run recalculation as background task"""
    async def callback(payload):
        await app.dispatch(f"solver.message.{payload.get('type')}",context=payload)
    await solve(
        slots_on_rota=9,
        people_on_rota=8,
        startdate=startdate,
        callback=callback,
        get_db_session=db

        )

@app.post('/recalculate')
def recalculate(request:sanic.Request):
    '''run query'''
    try:
        assert request.form is not None
        start_date = request.form.get('startdate')
        if start_date is None:
            raise ValueError()
        datetime.date.fromisoformat(start_date)
    except ValueError:
        return sanic.response.json({'error': 'start date is invalid'}, status=400)
    app.add_task(do_recalculate(start_date,request.app.ctx.db))


status = {1: False}




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
def shutdown(app,loop):
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
    days_array = [(startdate+datetime.timedelta(days=daydelta)).isoformat()
                  for daydelta in range(days_to_show)]
    staff = sorted([e.name for e in Staff])
    duties = {}
    for duty in get_duties_from_db(startdate, days_to_show):
        duties.setdefault(duty.date, {}).setdefault(
            duty.shift, {})[duty.name] = duty.duty
    return sanic.response.json({'days': days_array, 'names': staff, 'duties': duties})


@app.post('/setduty')
def set_duty(request):
    """Update duty for shift"""
    args = request.json
    try:
        duty=args['duty']
        if duty not in ['ICU',
        'LOCUM_ICU',
        'DEFINITE_ICU',
        'DEFINITE_LOCUM_ICU',
        'ICU_MAYBE_LOCUM',
        'LEAVE',
        'NOC']:
            raise KeyError(args['duty'])
                   
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


@app.route('/config/<constraint_type:str>/<constraint_id:str>',methods=('get','post'))
async def get_single_config(req,constraint_type,constraint_id):
    "Configuration dialog for a single constraint instance"
    constraint_class = get_constraint_class(constraint_type)
    constraint_config={} if constraint_id=='NEW' else get_single_constraint_from_db(
        constraint_type,constraint_id)
    config_form=constraint_class.config_form
    form_template=constraint_class.form_template
    form=config_form(req,data=constraint_config)
    http_status=200
    if req.method=='POST':
        try:
            if form.validate():
                if constraint_id=='NEW':
                    constraint_id=str(uuid.uuid4())
                update_constraint(constraint_class(config=constraint_config))
                return sanic.response.redirect('/config')
        except ValueError:
            pass
        http_status=400
    return await render(form_template,context={'form':form,'constraint_type':constraint_type,'constraint_id':constraint_id},status=http_status)

@app.get('/config')
@app.ext.template('constraint_settings.j2')
def constraint_settings(req):
    constraints=filter(None,[
        get_constraint_from_spec(spec.type,spec.id,spec.config) 
        for spec in get_constraints_from_db()])
    return {'constraints':constraints}

if __name__ == "__main__":
    print(os.path.join(os.getcwd(), 'static'))
    app.run(dev=True)