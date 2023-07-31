
import os
from typing import cast
from aiohttp import web
import asyncio
from datetime import date, timedelta,datetime
from io import TextIOWrapper
import json
import subprocess
from contextlib import contextmanager

from solver import async_solver_ctx
from datastore import DataStore



    
datastore=DataStore()
datastore.load_data()
pubhols={date(2022, 1, 1)}


datastore.pubhols.update(pubhols)
dutytypes = {}
editsession = {}
routes=web.RouteTableDef()

@routes.get('/data')
async def get_data(request):
    return web.json_response(datastore.as_dict())

@routes.get('/gridconfig')
async def get_grid_config(request):
    return web.json_response(datastore.get_config())

@routes.post('/click')
async def duty_click(request:web.Request):
    data=await request.json()
    match data:
        case {'name':name,'date':d,'session':sess,'duty':duty}:
            datastore.setduty(name,d,sess,duty)
            return web.json_response({'response':'ok'})
        case _:
            return web.json_response({'error':f'wrong data shape: received {data}'},status=400)
        
@routes.post('/handle_clw')
async def handle_clw(request:web.Request):
    try:
        data = await request.post()
        clw = cast(web.FileField,data['clw'])
        csvfile = TextIOWrapper(clw.file)
        datastore.import_clw_csv(csvfile)
        return web.json_response({'response':'ok'})
    except Exception as e:
        return web.json_response({'error':str(e)},status=400)
    
@routes.post('/solve')
async def solve_rota(request):
    "launch solver in background thread"
    def callback(result):
        datastore.update_data(result, overwrite=True)
    ftr = solve(datastore, {}, callback)
    ftr.add_done_callback(lambda f: f.result())
    return web.json_response({'status':'ok'})
    
#TODO: implement menu items
        
@routes.post('/setlocum')
async def setlocum(request:web.Request):
    "Set duty as determined by menu"
    match await request.json():
        case {'name':name,'date':d,'session':session,'locumtype':locumtype}:
            datastore.setlocum(name,d,session,locumtype)
            return web.json_response({'status':'ok'})
        case _:
            return web.json_response({'error':'bad request format'},status=400)

@routes.post('/setlock')
async def setlock(request):
    "Set lock as determined by menu"
    match await request.json():
        case {'name':name,'date':d,'session':session,'locktype':locktype}:
            datastore.setlocum(name,d,session,locktype)
            return web.json_response({'status':'ok'})
        case _:
            return web.json_response({'error':'bad request format'},status=400)

@routes.post('/setph')
async def setph(request):
        "Menu command to toggle day as public holiday"
        match await request.json:
            case {'date':d,'value':True}:
                datastore.pubhols.add(d)
                return web.json_response({'status':'ok'})
            case {'date':d,'value':False}:
                if d in datastore.pubhols:
                    datastore.pubhols.remove(d)
                return web.json_response({'status':'ok'})
            case _:
                return web.json_response({'error':'setph must be a boolean or None'},status=400)
            
@routes.get('/test')
async def testroute(request:web.Request):
    if request.if_modified_since:
        print(request.if_modified_since)
        raise web.HTTPNotModified()
    r= web.json_response(list(request.headers.items()))
    r.last_modified=datetime.today()
    return r

@routes.get('/')
async def index(request):
    return web.Response(content_type="text/html",body="""<html><head></head><body><div id=root></div><script src="static/jsfile.js"></script></body></html>""")
@routes.post('/abort')
async def abort(request:web.Request):
    request.app['abort'].set()
    return web.Response(text='bye')
async def main():
    app = web.Application()
    app['abort']=asyncio.Event()
    app.add_routes(routes)
    app.router.add_static('/static',os.path.join(os.getcwd(),'..','web'))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 8080)
    await site.start()
    await app['abort'].wait()
    await runner.cleanup()

asyncio.run(main())