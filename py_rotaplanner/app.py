from flask import Flask
from .database import db
import os

app=Flask(__name__)

db_path=os.path.join(os.getcwd(),'database.sqlite')
print(db_path)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
#app.config["SQLALCHEMY_ECHO"]=True
db.init_app(app)