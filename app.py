from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2

app = Flask(__name__)
CORS(app)


@app.route('/')
def hello_world():
    test = {"user": "debil"}
    return jsonify(test)


@app.route('/get-text')
def get_from_database():
    conn = psycopg2.connect(
        "dbname='slihduor' user='slihduor' host='rajje.db.elephantsql.com' password='Z3kDd9k-Hzri0TsNeXOEKYkb7jo9wClC'")
    cur = conn.cursor()
    cur.execute("SELECT * FROM website_text WHERE page='{0}'".format(request.args.get("page")))
    row = cur.fetchall()
    text = {}
    for r in row:
        text[r[0]] = r[2]
    return jsonify(text)


if __name__ == '__main__':
    app.run()
