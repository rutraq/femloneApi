import os
from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from flask_pymongo import PyMongo
from werkzeug.security import check_password_hash
import jwt
import datetime
import string
import random
import re

app = Flask(__name__)
CORS(app)
app.config[
    "key"] = "WnZr4u7x!A%D*G-KaNdRgUkXp2s5v8y/B?E(H+MbQeShVmYq3t6w9z$C&F)J@NcRfUjWnZr4u7x!A%D*G-KaPdSgVkYp2s5v8y/B?E(H+MbQeThWmZq4t6w9z$C&F)J@NcRfUjXn2r5u8x!A%D*G-KaPdSgVkYp3s6v9y$B?E(H+MbQeThWmZq4t7w!z%C*F)J@NcRfUjXn2r5u8x/A?D(G+KaPdSgVkYp3s6v9y$B&E)H@McQeThWmZq4t7w!z%"
# app.config["path"] = "C:\Projects_HTML\BeautyWebSite\photos"  # laptop
app.config["path"] = "M:\HTML_Projects\BeautyWebSite\photos"  # PC
app.config["url"] = "photos\\"


@app.route('/get-text')
def get_from_database_text():
    mongodb_client = PyMongo(app, uri="mongodb://localhost:27017/text")
    db = mongodb_client.db[request.args.get("page")]
    texts = db.find()
    data = {}
    for text in texts:
        data[text['id']] = text['text']
    return jsonify(data)


@app.route("/get-photo")
def get_from_database_photo():
    mongodb_client = PyMongo(app, uri="mongodb://localhost:27017/photos")
    db = mongodb_client.db[request.args.get("page")]
    photos = db.find()
    data = {}
    for photo in photos:
        data[photo["id"]] = photo["url"]
    return jsonify(data)


@app.route('/login')
def login():
    mongodb_client = PyMongo(app, uri="mongodb://localhost:27017/admin")
    db = mongodb_client.db
    user = db.users.find_one({"login": request.args.get("login")})
    if user is not None:
        if check_password_hash(user["password"], request.args.get("password")):
            return tokens_generate(user['login'], "administrator")
        else:
            response = make_response(jsonify(message="wrong password"))
            response.headers["Access-Control-Allow-Credentials"] = "true"
            return response
    else:
        response = make_response(jsonify(message="wrong user"))
        response.headers["Access-Control-Allow-Credentials"] = "true"
        return response


def tokens_generate(name, role):
    payload_access = {
        "login": name,
        "role": role,
        "exp": datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(minutes=15)
    }
    access_token = jwt.encode(payload_access, app.config["key"], algorithm="HS256")
    response = make_response(jsonify(message="logged in"))
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.set_cookie("access_token", access_token, httponly=True)
    response.set_cookie("refresh_token", refresh_token_generate(name, role), httponly=True)
    return response


def refresh_token_generate(name, role):
    mongodb_client = PyMongo(app, uri="mongodb://localhost:27017/admin")
    db = mongodb_client.db["sessions"]

    sessions = list_from_db(db.find({"name": name}))
    if len(sessions) >= 5:
        db.delete_many({"name": name})

    refresh_token = ''.join(random.choices(string.ascii_uppercase + string.digits + string.ascii_lowercase, k=512))
    db.insert_one({
        "name": name,
        "role": role,
        "refresh_token": refresh_token,
        "exp": (datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(days=30)).timestamp()
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
def change_text():
    checked = jwt_check(request.cookies.get("access_token"), app.config["key"])
    if checked[0]:
        db = request.args.get("db")
        page = request.args.get("page")
        text_id = request.args.get("id")
        text = request.args.get("text")
        update_database_info(db, page, text_id, text)
        response = make_response(jsonify(message="updated"))
    elif checked[1] == "invalid signature":
        response = make_response(jsonify(message="invalid signature"))
    else:
        response = make_response(jsonify(message="expired signature"))
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response


@app.route("/change-photo", methods=["POST"])
def change_photo():
    checked = jwt_check(request.cookies.get("access_token"), app.config["key"])
    if checked[0]:
        file = request.files['img']
        url = str(app.config["url"] + file.filename)
        file.save(os.path.join(app.config["path"], file.filename))
        mongodb_client = PyMongo(app, uri="mongodb://localhost:27017/photos")
        db = mongodb_client.db[request.args.get('page')]
        db.insert_one({"id": request.args.get("id"), "url": url})
        # db.update_one({"id": request.args.get("id")}, {"$set": {"url": url}})
        response = make_response(jsonify(message="uploaded"))
    elif checked[1] == "invalid signature":
        response = make_response(jsonify(message="invalid signature"))
    else:
        response = make_response(jsonify(message="expired signature"))
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response


@app.route("/upload-url")
def upload():
    file = request.args.get("src")
    file = re.search("photos.+", file)[0].replace('/', '\\')
    mongodb_client = PyMongo(app, uri="mongodb://localhost:27017/photos")
    db = mongodb_client.db[request.args.get('page')]
    db.insert_one({"id": request.args.get("id"), "url": file})
    response = make_response(jsonify(message="uploaded"))
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response


def update_database_info(db, collection, text_id, text):
    mongodb_client = PyMongo(app, uri="mongodb://localhost:27017/{0}".format(db))
    db = mongodb_client.db[collection]
    db.update_one({"id": text_id}, {"$set": {"text": text}})


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
