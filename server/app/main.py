#!/usr/bin/env python3
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import configparser
import os

CONFIG_FILE = "config.ini"

config = configparser.ConfigParser()
config.read(CONFIG_FILE)

app = Flask(__name__)

for setting in ["SECRET_KEY", "SQLALCHEMY_DATABASE_URI", "SQLALCHEMY_TRACK_MODIFICATIONS"]:
    app.config[setting] = config["database"][setting]

db = SQLAlchemy(app)
app.config["database"] = db
db.create_all()

with app.app_context():
    from .user import users_page, User
    from .post import posts_page, Post

    app.register_blueprint(users_page, url_prefix="/users")
    app.register_blueprint(posts_page, url_prefix="/posts")
