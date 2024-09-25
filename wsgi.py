from py_rotaplanner.app import app,db
import py_rotaplanner.activities.models
from flask import Blueprint,render_template,current_app
from py_rotaplanner.activities.endpoints import blueprint as sched_blueprint
import datetime
import sys

@app.cli.command('initdb')
def create_db():
    db.create_all()

@app.cli.command('templates')
def templates():
   app.jinja_env.compile_templates('compiled',zip=None)

@app.cli.command('testdata')
def create_test_data():
    Activity=py_rotaplanner.activities.models.Activity
    for day in range(365):
      for a in ('A','B','C'):
        db.session.add(Activity(
            name=f'activ{a}',
            activity_start=datetime.datetime(2024,1,1,8,0)+datetime.timedelta(days=day),
            activity_finish=datetime.datetime(2024,1,1,17,0)+datetime.timedelta(days=day)))
    db.session.commit()


app.register_blueprint(sched_blueprint,url_prefix='/activities',)

@app.get('/shutdown')
def quit():
   raise KeyboardInterrupt

@app.get('/sidebar.html')
def home():
   return render_template('sidebar.html',name='world')
if __name__=='__main__':    
    app.run(debug=True)