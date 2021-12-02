from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_pymongo import PyMongo

app = Flask(__name__)
CORS(app)


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
        if request.args.get("password") == user['password']:
            return jsonify(message="good")
        else:
            return jsonify(message="bad")
    else:
        return jsonify(message="bad")


if __name__ == '__main__':
    app.run()
