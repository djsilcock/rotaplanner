from flask import Flask
from .database import db
from flask_unpoly import FlaskUnpoly
from flask_wtf import CSRFProtect
from flask_cors import CORS
import pathlib

app = Flask(
    __name__,
    static_url_path="/assets",
    static_folder=pathlib.Path(__file__).parent.joinpath("static", "assets"),
)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.sqlite"
app.config["SECRET_KEY"] = "qwertyuiopasdfghjkl"
# app.config["SQLALCHEMY_ECHO"] = True
FlaskUnpoly().init_app(app)
# csrf = CSRFProtect(app)
# cors = CORS(app)
db.init_app(app)
