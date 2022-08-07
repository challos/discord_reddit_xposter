#!/usr/bin/env python3
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import configparser
import os

CONFIG_FILE = os.path.expanduser("~/.config/config.ini")
DATABASE_FOLDER = "/database_folder/"

config = configparser.ConfigParser()
config.read(CONFIG_FILE)

app = Flask(__name__)
if "SQLALCHEMY_DATABASE_URI" not in config["database"]:
    print(
        "Please supply the SQLALCHEMY_DATABASE_URI config in the server's config.ini."
    )
    exit()

app.config["SQLALCHEMY_DATABASE_URI"] = (
    "sqlite:///" + DATABASE_FOLDER + config["database"]["SQLALCHEMY_DATABASE_URI"]
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = config["database"].getboolean(
    "SQLALCHEMY_TRACK_MODIFICATIONS", False
)
app.config["SECRET_KEY"] = config["database"]["SECRET_KEY"]

db = SQLAlchemy(app)
app.config["database"] = db
app.config["allow_registration"] = config["xposter"].getboolean(
    "allow_registration", False
)

with app.app_context():
    from .user import users_page, User
    from .post import posts_page, Post

    app.register_blueprint(users_page, url_prefix="/users")
    app.register_blueprint(posts_page, url_prefix="/posts")
    db.create_all()
