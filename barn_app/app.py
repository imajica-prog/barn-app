from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")

database_url = os.getenv("DATABASE_URL", "postgresql://neondb_owner:npg_PF6oH8baDmlK@ep-restless-sea-am72oev5-pooler.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True, "pool_recycle": 300}
app.config["REMEMBER_COOKIE_DURATION"] = timedelta(days=30)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

class User(UserMixin):
    id = 1
    def get_id(self):
        return "1"

@login_manager.user_loader
def load_user(user_id):
    if user_id == "1":
        return User()
    return None

class Horse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    breed = db.Column(db.String(100))
    age = db.Column(db.Integer)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    horse_id = db.Column(db.Integer, nullable=False)
    service = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=False)

class HealthRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    horse_id = db.Column(db.Integer, nullable=False)
    note = db.Column(db.String(200), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class Record(db.Model):
    id = db.Column(db.Integer, primary_key=True)
