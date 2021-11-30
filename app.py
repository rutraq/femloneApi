from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


@app.route('/')
def hello_world():
    test = {"user": "debil"}
    return jsonify(test)


if __name__ == '__main__':
    app.run()
