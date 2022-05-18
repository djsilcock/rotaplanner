import multiprocessing
import sys
import json
import asyncio

import sanic
from solver import RotaSolver,get_constraint_config



app = sanic.Sanic('RotaSolver')


def launch_solver(pipe):
    """Launches solver task"""

    rota = RotaSolver(rota_cycles=4,
                      slots_on_rota=9, people_on_rota=8, startdate='2022-04-04', pipe=pipe)
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

@app.post('/backend/log')
async def logfile(request):
    print (request.json)
    return sanic.response.json({'response':'OK'})
    
@app.post("/api/examplefeed")
async def testserver(request):
    '''run query'''
    data = request.json
    response = await request.respond(content_type="text/plain")

    localpipe, remotepipe = multiprocessing.Pipe()
    process = multiprocessing.Process(
        target=launch_solver, args=(remotepipe,))
    process.start()

    for constraint in data['constraints']:
        localpipe.send(dict(json.loads(constraint), type='constraint'))
    localpipe.send({'type': 'solve'})
    try:
        while True:
            if localpipe.poll():
                data = localpipe.recv()
                await response.send(json.dumps(data))
                await response.send('\n')
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

    # with open('solvedrota5.json', 'w', encoding='utf-8') as f:
    #    json.dump(result, f)


@app.get('/constraintdefs')
async def settings(request):
    """returns constraint definitions for form"""
    return sanic.response.json(get_constraint_config())


@app.get('/constraints')
async def get_constraints(request):
    """return list of current constraints"""
    with open('constraintlist.txt') as f:
        constraints = [json.loads(line) for line in f]
    return sanic.response.json(constraints)


@app.post('/constraints')
async def save_constraints(request):
    """save the constraints list from the ui"""
    data = request.json
    with open('constraintlist.txt', 'w', encoding='utf-8') as f:
        for (k, v) in data.items():
            json.dump(dict({'id': k}, **v), f)
            f.write('\n')
    return sanic.response.json({'status': 'OK'})
#app.static("/", os.path.join(os.path.dirname(__file__),
#           "frontend", "build", "index.html"))
#app.static("/", os.path.join(os.path.dirname(__file__), "frontend", "build"))


if __name__ == "__main__":
    app.run(debug=True)
    # asyncio.run(test())
