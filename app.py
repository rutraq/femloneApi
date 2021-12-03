from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from flask_pymongo import PyMongo
import python_jwt
from jwcrypto.jws import InvalidJWSSignature
from werkzeug.security import generate_password_hash, check_password_hash
import python_jwt as jwt, jwcrypto.jwk as jwk, datetime

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
            return jwt_test(user["login"], user["password"])
        else:
            return jsonify(message="bad")
    else:
        return jsonify(message="bad")


def jwt_test(name, password):
    key = jwk.JWK.generate(kty='RSA', size=2048)
    key2 = jwk.JWK.generate(kty='RSA', size=1024)
    payload = {
        'login': name,
        'password': password}
    token = jwt.generate_jwt(payload, key, 'PS256', datetime.timedelta(minutes=60))
    token2 = jwt.generate_jwt(payload, key2, 'PS256', datetime.timedelta(minutes=60))
    try:
        jwt.verify_jwt(token2, key, ['PS256'])
    except InvalidJWSSignature:
        print("Что ты за токен отправил еблан?")
    response = make_response(jsonify(message="good"))
    response.headers["token"] = token
    return response


if __name__ == '__main__':
    app.run()
