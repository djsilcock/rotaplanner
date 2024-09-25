from flask import Flask
from .database import db
from flask_unpoly import FlaskUnpoly

app=Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.sqlite"
#app.config["SQLALCHEMY_ECHO"]=True
FlaskUnpoly().init_app(app)
db.init_app(app)
