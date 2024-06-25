
import os
from typing import cast

import asyncio
from datetime import date, datetime
from io import TextIOWrapper
import subprocess
import random
import string
from json import JSONEncoder
import datetime
from dataclasses import is_dataclass,asdict

from aiohttp import web
import humps

from logger import log_queue,log
from solver import async_solver_ctx
from datastore import DataStore

import templating

from aiohttp_sse import sse_response


datastore = DataStore()
datastore.load_data()
pubhols = {date(2022, 1, 1)}
datastore.pubhols.update(pubhols)
dutytypes = {}
editsession = {}
apiroutes = web.RouteTableDef()

class DateJSONEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o,datetime.date):
            return o.isoformat()
        if is_dataclass(o):
            return asdict(o)
        return super().default(o)

@apiroutes.get('/logging')
async def hello(request: web.Request) -> web.StreamResponse:
    async with sse_response(request) as resp:
        while resp.is_connected():
            await resp.send(await log_queue.get())
    return resp


@apiroutes.get('/by_name')
async def get_data(_):
    "get all data"
    return web.json_response(datastore.as_dict_by_name())


@apiroutes.get('/by_location')
async def get_data_location(_):
    "get data by location"
    return web.json_response(datastore.as_dict_by_location())

@apiroutes.post('/update_duty')
async def set_data(request:web.Request):
    data=await request.json()
    log(data)
    name=data['name']
    dutydate=data['dutydate']
    session_start=data['sessionStart']
    session_finish=data['sessionFinish']
    duty=data['duty']
    datastore.setduty(name,dutydate,session_start,session_finish,duty)
    return web.json_response({'response':'OK'})

templates=[]
demand_templates=[]

staff=['fred','barney','wilma','betty','pebbles','bambam']
@apiroutes.get('/getTemplates')
async def get_templates(request):
    return web.json_response(
        humps.camelize({'default':{'id':None,
        'name':'Untitled',
        'appliesToStaff':{k:False for k in staff},
        'templates': [''.join([random.choice(string.ascii_letters) for x in range(7)]) for y in range(7)],
        'templateContent':{},
        'rules':{ 'root': { 'ruleId': 'root', 'ruleType': 'group', 'groupType': 'and', 'rules': [] } }
        },'templates':templates}))

@apiroutes.get('/getDemandTemplates')
async def get_demand_templates(request):
    return web.json_response(humps.camelize(
        {'default':{'id':None,
        'name':'Untitled',
        'start':8,
        'finish':17,
        'activity':None,
        'rules':{ 'root': { 'ruleId': 'root', 'ruleType': 'group', 'groupType': 'and', 'rules': [] } }
        },'templates':list(templating.get_demand_templates(asdict=True))}),dumps=DateJSONEncoder().encode)

@apiroutes.get('/getDemandTemplatesForWeek')
async def get_demand_templates_for_day(request):
    date=datetime.date.fromisoformat(request.query['date'])
    return web.json_response(
        humps.camelize([list(templating.get_templates_for_day(date+datetime.timedelta(days=i),asdict=True)) for i in range(7)]),dumps=DateJSONEncoder().encode)


@apiroutes.post('/updateDemandTemplates')
async def update_templates(request):
    data=humps.decamelize(await request.json())
    templating.update_demand_template(data)
    return await get_demand_templates(request)

@apiroutes.get('/gridconfig')
async def get_grid_config(_):
    "get configuration for grid layout"
    return web.json_response(datastore.get_config())



@apiroutes.post('/handle_clw')
async def handle_clw(request: web.Request):
    "for uploading csv from clwrota"
    try:
        data = await request.post()
        clw = cast(web.FileField, data['clw'])
        csvfile = TextIOWrapper(clw.file)
        datastore.import_clw_csv(csvfile)
        return web.json_response({'response': 'ok'})
    except Exception as exc:
        return web.json_response({'error': str(exc)}, status=500)


@apiroutes.post('/solve')
async def solve_rota(request:web.Request):
    "launch solver in background thread"
    def callback(result):
        datastore.update_data(result, overwrite=True)
    ftr = request.app['solve'](datastore, {}, callback)
    ftr.add_done_callback(lambda f: f.result())
    return web.json_response({'status': 'ok'})

# TODO: implement menu items


@apiroutes.post('/setlocum')
async def setlocum(request: web.Request):
    "Set duty as determined by menu"
    match await request.json():
        case {'name': name, 'date': dutydate, 'session': session, 'locumtype': locumtype}:
            datastore.setflag(name, dutydate, session, locumtype)
            return web.json_response({'status': 'ok'})
        case _:
            return web.json_response({'error': 'bad request format'}, status=400)


@apiroutes.post('/setlock')
async def setlock(request):
    "Set lock as determined by menu"
    match await request.json():
        case {'name': name, 'date': dutydate, 'session': session, 'locktype': locktype}:
            datastore.setflag(name, dutydate, session, locktype)
            return web.json_response({'status': 'ok'})
        case _:
            return web.json_response({'error': 'bad request format'}, status=400)


@apiroutes.post('/setph')
async def setph(request):
    "Menu command to toggle day as public holiday"
    match await request.json:
        case {'date': dutydate, 'value': True}:
            datastore.pubhols.add(dutydate)
            return web.json_response({'status': 'ok'})
        case {'date': dutydate, 'value': False}:
            if dutydate in datastore.pubhols:
                datastore.pubhols.remove(dutydate)
            return web.json_response({'status': 'ok'})
        case _:
            return web.json_response({'error': 'setph must be a boolean or None'}, status=400)



@apiroutes.get('/')
async def index(_):
    "base route"
    return web.Response(content_type="text/html",
                        body="""<html>
        <head>
        <link href="static/jsfile.css" rel="stylesheet">
        </head>
        <body><div id=root></div><script src="static/jsfile.js"></script></body>
        </html>""")


@apiroutes.post('/abort')
async def abort(request: web.Request):
    await request.app['cancel']()
    return web.Response(text='bye')

@apiroutes.get('/quit')
async def quit(request:web.Request):
    close_event:asyncio.Event=request.app['abort']
    close_event.set()
    return web.Response(text='bye')

async def yarn_runner(app):
    try:
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
    except AttributeError:
        creationflags=0
    process=await asyncio.create_subprocess_shell(
        'yarn dev --open',
        stdin=subprocess.PIPE,
        creationflags=creationflags,
        cwd=os.path.join(os.getcwd(),'..','frontend'),
        )
    yield
    print ('attempting to shut down dev server')
    process.terminate()
    await process.wait()



async def main():
    app = web.Application()
    api = web.Application()
    api['abort'] = asyncio.Event()
    api.add_routes(apiroutes)
    api.cleanup_ctx.append(async_solver_ctx)
    #api.cleanup_ctx.append(yarn_runner)
    app.add_subapp('/api',api)
    app.router.add_static('/static', os.path.join(os.getcwd(), '..', 'frontend','dist'))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 8080)
    await site.start()
    print('wait for exit signal')
    await api['abort'].wait()
    print('exit signal received')
    await runner.cleanup()

asyncio.run(main())
