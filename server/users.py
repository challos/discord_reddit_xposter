#!/usr/bin/env python3
from flask import request, jsonify, make_response, Blueprint, current_app
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import jwt
import datetime
from functools import wraps


users_page = Blueprint("users_page", __name__)

with current_app.app_context():
    db = current_app.config["database"]


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    public_id = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    registered_on = db.Column(db.DateTime, nullable=False)
    admin = db.Column(db.Boolean, nullable=False, default=False)

    def __init__(self, username: str, password: str, admin=False):
        self.public_id = str(uuid.uuid4())
        self.username = username
        self.password = generate_password_hash(password, method="sha256")
        self.registered_on = datetime.datetime.now()
        self.admin = admin


def token_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if auth_header:
            token = auth_header.split(" ")[1]
        else:
            return make_response(
                "Please supply a username and password.",
            )

        try:
            data = jwt.decode(token, current_app.config["SECRET_KEY"], "HS256")
        except jwt.exceptions.DecodeError:
            return make_response("Error with token.", 400)
        current_user = User.query.filter_by(public_id=data["public_id"]).first()

        return f(current_user=current_user, *args, **kwargs)

    return decorator


@users_page.route("/register", methods=["GET", "POST"])
def signup_user():

    data = request.authorization
    if not data or "username" not in data or "password" not in data:
        return make_response("Needs authorization", 400)
    if data and User.query.filter_by(username=data["username"]).first():
        return make_response("User already exists!", 400)

    new_user = User(
        username=data["username"],
        password=data["password"],
        admin=False,
    )
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "registered successfully"})


@users_page.route("/login", methods=["GET", "POST"])
def login_user():
    auth = request.authorization

    if not auth or not auth.username or not auth.password:
        return make_response("could not verify", 401)

    user = User.query.filter_by(username=auth.username).first()

    if check_password_hash(user.password, auth.password):
        token = jwt.encode(
            {
                "username": user.username,
                "public_id": user.public_id,
                "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=30),
            },
            current_app.config["SECRET_KEY"],
        )
        return jsonify({"token": token})

    return make_response("could not verify", 401)


@users_page.delete("/remove_all")
@token_required
def remove_all_users(current_user):
    if current_user.admin:
        User.query.filter_by(admin=False).delete()
        return make_response("Really hope you meant to do that...", 200)
    else:
        return make_response("You're not an admin, stop trying.", 400)


@users_page.route("/author", methods=["POST", "GET"])
@token_required
def create_author(current_user):
    return make_response("wooo", 202)
