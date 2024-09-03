from flask_sqlalchemy import SQLAlchemy
from sqlmodel import SQLModel

db = SQLAlchemy(model_class=SQLModel)