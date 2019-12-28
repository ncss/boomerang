#!/usr/bin/python3

from flask import Flask, g, request, jsonify, redirect

from flask_swagger import swagger
from flask_swagger_ui import get_swaggerui_blueprint

import json
import sqlite3

app = Flask(__name__)
app.config['DATABASE'] = 'store.db'

# DB Helpers

def get_db():
  db = getattr(g, '_database', None)
  if db is None:
    db = g._database = sqlite3.connect(app.config['DATABASE'])
    db.row_factory = make_dicts
  return db

@app.teardown_appcontext
def close_connection(exception):
  db = getattr(g, '_database', None)
  if db is not None:
    db.close()

def make_dicts(cursor, row):
    return dict((cursor.description[idx][0], value)
                for idx, value in enumerate(row))

def db_init():
  with app.app_context():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS store
                 (key TEXT PRIMARY KEY, value TEXT, created DATEIME, updated DATETIME)''')
    conn.commit()

# DB Access

def db_store(key, value):
  value = json.dumps(value)
  conn = get_db()
  c = conn.cursor()
  try:
    c.execute('''INSERT INTO store
                 VALUES (?, ?, strftime('%Y-%m-%d %H:%M:%S', 'now'), strftime('%Y-%m-%d %H:%M:%S', 'now'))
              ''', (key, value))
  except sqlite3.IntegrityError:
    c.execute('''UPDATE store
                 SET value = ?, updated = strftime('%Y-%m-%d %H:%M:%S', 'now')
                 WHERE key = ?
               ''', (value, key))
  conn.commit()

def db_fetch(key):
  c = get_db().cursor()
  c.execute('SELECT * FROM store WHERE key = ? LIMIT 1', (key,))
  result = c.fetchone()
  if result:
    value = result['value']
    return json.loads(value)
  else:
    return None

def db_delete(key: str) -> bool:
  conn = get_db()
  c = conn.cursor()
  c.execute('DELETE FROM store WHERE key = ?', (key,))
  did_delete = c.rowcount > 0
  conn.commit()
  return did_delete

# Docs
SWAGGER_URL = '/docs/'
API_URL = '/api/spec'
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={'app_name': 'Storage API'},
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)


@app.route("/api/spec")
def spec():
    swag = swagger(app)
    swag['info']['version'] = '1.0'
    swag['info']['title'] = 'Storage API'
    return jsonify(swag)


@app.route("/")
def homepage():
  return redirect(SWAGGER_URL)

# Routes

def json_error(status_code, message):
  resp = jsonify({"status": status_code, "error": message})
  resp.status_code = status_code
  return resp

@app.errorhandler(400)
def bad_request(*_, message=None):
  return json_error(400, message or "bad request")

@app.errorhandler(404)
def not_found(*_, message=None):
  return json_error(404, message or "not found")

@app.errorhandler(500)
def internal_server_error(*_, message=None):
  return json_error(500, message or "internal server error")

@app.route('/<path:key>', methods=['POST'])
def store(key):
  '''
    Store a value
    ---
    tags:
      - store
    consumes:
      - application/json
    parameters:
      - in: path
        name: key
        type: string
        required: true
        default: 'group1/users/georgina'
        description: the key you want to store the value at
      - in: body
        name: value
        required: true
        description: A JSON object to store
        schema:
          type: object
          example:
            name: georgina
            food: marzipan
    responses:
      400:
        description: The given value was invalid.
      200:
        description: The key was successfully stored.
        schema:
          id: Value
  '''
  try:
    value = request.get_json()
  except:
    value = None
  if value is None:
    return bad_request(message="You need to supply JSON")

  try:
    db_store(key, value)
  except:
    return internal_server_error(message="Failed to store key")

  return jsonify({
    'key': key,
    'value': value,
  })

@app.route('/<path:key>', methods=['DELETE'])
def delete(key):
  '''
    Delete a key (if it exists)
    ---
    tags:
      - delete
    parameters:
      - in: path
        name: key
        type: string
        required: true
        default: 'group1/users/georgina'
        description: the key you want to delete
    responses:
      204:
        description: The key was successfully deleted
      404:
        description: The key did not exist
  '''

  if db_delete(key):
    return "", 204
  else:
    return not_found(message="No such key: %s" % (key,))

@app.route('/<path:key>', methods=['GET'])
def fetch(key):
  '''
    Retrieve a value
    ---
    tags:
      - fetch
    parameters:
      - in: path
        name: key
        type: string
        required: true
        default: 'group1/users/georgina'
        description: the key you want to fetch the value for
    responses:
      404:
        description: There was no JSON object stored at the key.
      200:
        description: The JSON object stored at the key was returned.
        schema:
          id: Value
          properties:
            key:
              type: string
              example: group1/users/georgina
            value:
              type: string
              example: {"name": "georgina", "food": "marzipan"}
  '''

  result = db_fetch(key)
  if result is None:
    return not_found(message="No such key: %s" % (key,))

  return jsonify(result)


if __name__ == '__main__':
  db_init()
  app.run(debug=True, port=3000)
