from flask import Flask
from .database import db

app=Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.sqlite"
#app.config["SQLALCHEMY_ECHO"]=True
db.init_app(app)
