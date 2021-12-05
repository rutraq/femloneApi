import python_jwt as jwt
from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from flask_pymongo import PyMongo
from werkzeug.security import check_password_hash
import jwt
import datetime

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
        if check_password_hash(user["password"], request.args.get("password")):
            return jwt_generate(user['login'], request.args.get("password"), user["password"])
        else:
            return jsonify(message="bad")
    else:
        return jsonify(message="bad")


# def jwt_test(name, password):
#     key = jwk.JWK.generate(kty='RSA', size=2048)
#     print(key)
#     payload = {
#         'login': name,
#         'password': password}
#     token = jwt.generate_jwt(payload, key.export_private(), 'RS256', datetime.timedelta(minutes=60))
#     try:
#         jwt.verify_jwt(token, key.export_public(), ['RS256'])
#     except InvalidJWSSignature:
#         print("Что ты за токен отправил еблан?")
#     response = make_response(jsonify(message="good"))
#     response.headers["token"] = token
#     return response

def jwt_generate(name, password, password_key):
    payload = {
        "login": name,
        "password": password,
        "exp": datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(minutes=30)
    }
    token = jwt.encode(payload, password_key, algorithm="HS256")
    response = make_response(jsonify(message="good"))
    response.set_cookie("token", token)
    return response


@app.route("/check")
def ch():
    return jsonify(check=jwt_check(request.cookies.get("token"), ))


def jwt_check(token, password_key):
    try:
        jwt.decode(token, password_key, algorithms=["HS256"])
        return True
    except jwt.exceptions.InvalidSignatureError:
        return False


if __name__ == '__main__':
    app.run()
