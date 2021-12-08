import python_jwt as jwt
from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from flask_pymongo import PyMongo
from werkzeug.security import check_password_hash
import jwt
import datetime
import string
import random

app = Flask(__name__)
CORS(app)
app.config[
    "key"] = "WnZr4u7x!A%D*G-KaNdRgUkXp2s5v8y/B?E(H+MbQeShVmYq3t6w9z$C&F)J@NcRfUjWnZr4u7x!A%D*G-KaPdSgVkYp2s5v8y/B?E(H+MbQeThWmZq4t6w9z$C&F)J@NcRfUjXn2r5u8x!A%D*G-KaPdSgVkYp3s6v9y$B?E(H+MbQeThWmZq4t7w!z%C*F)J@NcRfUjXn2r5u8x/A?D(G+KaPdSgVkYp3s6v9y$B&E)H@McQeThWmZq4t7w!z%"


@app.route('/get-text')
def get_from_database():
    mongodb_client = PyMongo(app, uri="mongodb://localhost:27017/text")
    db = mongodb_client.db
    if request.args.get("page") == "about":
        texts = db.about.find()
    elif request.args.get("page") == "home":
        texts = db.home.find()
    else:
        texts = db.about.find()
    data = {}
    for text in texts:
        data[text['id']] = text['text']
    return jsonify(data)


@app.route('/admin')
def login():
    mongodb_client = PyMongo(app, uri="mongodb://localhost:27017/admin")
    db = mongodb_client.db
    user = db.users.find_one({"login": request.args.get("login")})
    if user is not None:
        if check_password_hash(user["password"], request.args.get("password")):
            return tokens_generate(user['login'], "administrator")
        else:
            return jsonify(message="bad")
    else:
        return jsonify(message="bad")


def tokens_generate(name, role):
    payload_access = {
        "login": name,
        "role": role,
        "exp": datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(minutes=15)
    }
    access_token = jwt.encode(payload_access, app.config["key"], algorithm="HS256")
    response = make_response(jsonify(message="true"))
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.set_cookie("access_token", access_token, httponly=True)
    response.set_cookie("refresh_token", refresh_token_generate(name, role), httponly=True)
    return response


def refresh_token_generate(name, role):
    mongodb_client = PyMongo(app, uri="mongodb://localhost:27017/admin")
    db = mongodb_client.db

    sessions = list_from_db(db.sessions.find({"name": name}))
    if len(sessions) >= 5:
        db.sessions.delete_many({"name": name})

    refresh_token = ''.join(random.choices(string.ascii_uppercase + string.digits + string.ascii_lowercase, k=512))
    db.sessions.insert_one({
        "name": name,
        "role": role,
        "refresh_token": refresh_token,
        "exp": (datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(seconds=30)).timestamp()
    })
    return refresh_token


@app.route("/refresh-token")
def tokens_update():
    token = request.cookies.get("refresh_token")

    mongodb_client = PyMongo(app, uri="mongodb://localhost:27017/admin")
    db = mongodb_client.db

    db.sessions.delete_many({"exp": {"$lt": datetime.datetime.now(tz=datetime.timezone.utc).timestamp()}})

    user = db.sessions.find_one({"refresh_token": token})
    if user is not None:
        if user["exp"] > datetime.datetime.now(tz=datetime.timezone.utc).timestamp():
            db.sessions.delete_one({"refresh_token": token})
            return tokens_generate(user["name"], user["role"])
        else:
            response = make_response(jsonify(message="expired refresh token"))
            response.headers["Access-Control-Allow-Credentials"] = "true"
            return response
    else:
        response = make_response(jsonify(message="no such token"))
        response.headers["Access-Control-Allow-Credentials"] = "true"
        return response


def list_from_db(cursor):
    arr = []
    for data in cursor:
        arr.append(data)
    return arr


@app.route("/change-text", methods=["POST"])
def ch():
    checked = jwt_check(request.cookies.get("access_token"), app.config["key"])
    if checked[0]:
        mongodb_client = PyMongo(app, uri="mongodb://localhost:27017/text")
        db = mongodb_client.db
        page = request.args.get("page")
        text_id = request.args.get("id")
        if page == "about":
            db.about.upade_one({'id': text_id}, {'$set': {'text': request.headers.get("text")}})
        response = make_response(jsonify(message="updated"))
    elif checked[1] == "invalid signature":
        response = make_response(jsonify(message="invalid signature"))
    else:
        response = make_response(jsonify(message="expired signature"))
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response


def jwt_check(token, password_key):
    try:
        jwt.decode(token, password_key, algorithms=["HS256"])
        return [True, "okay"]
    except jwt.exceptions.InvalidSignatureError:
        return [False, "invalid signature"]
    except jwt.exceptions.ExpiredSignatureError:
        return [False, "expired signature"]


if __name__ == '__main__':
    app.run()
