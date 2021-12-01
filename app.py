from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2

app = Flask(__name__)
CORS(app)


@app.route('/')
def hello_world():
    test = {"user": "debil"}
    return jsonify(test)


@app.route('/name', methods=['GET'])
def add_to_database():
    test = {"user": "debil"}
    return jsonify(test)


if __name__ == '__main__':
    app.run()
