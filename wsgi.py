from py_rotaplanner.app import app,db
import py_rotaplanner.templating.database
import py_rotaplanner.scheduling.database
from flask import Blueprint
from py_rotaplanner.scheduling.endpoints import blueprint as sched_blueprint
import datetime

@app.cli.command('initdb')
def create_db():
    db.create_all()

@app.cli.command('testdata')
def create_test_data():
    Activity=py_rotaplanner.scheduling.database.Activity

    for day in range(365):
      for a in ('A','B','C'):
        db.session.add(Activity(
            name=f'activ{a}',
            activity_start=datetime.datetime(2024,1,1,8,0)+datetime.timedelta(days=day),
            activity_finish=datetime.datetime(2024,1,1,17,0)+datetime.timedelta(days=day)))
    db.session.commit()

api_blueprint=Blueprint('api',__name__)

api_blueprint.register_blueprint(sched_blueprint,url_prefix='/scheduling')
app.register_blueprint(api_blueprint,url_prefix='/api')
if __name__=='__main__':    
    app.run()