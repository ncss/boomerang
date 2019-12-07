from flask import Flask, g, request, jsonify

from flask_swagger import swagger
from flask_swagger_ui import get_swaggerui_blueprint

import json
import sqlite3

app = Flask(__name__)

DATABASE = 'store.db'

# DB Helpers 

def get_db():
  db = getattr(g, '_database', None)
  if db is None:
    db = g._database = sqlite3.connect(DATABASE)
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
    return True

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
    c.execute('''UPDATE store WHERE key=? SET
                 value = ?,
                 updated = strftime('%Y-%m-%d %H:%M:%S', 'now')
               ''', (key, value))
  conn.commit()
  return True 

def db_fetch(key):
  c = get_db().cursor()
  c.execute('SELECT * FROM store WHERE key=? LIMIT 1', (key,))
  result = c.fetchone()
  if result:
    value = result['value']
    return json.loads(value)
  else:
    return None

# Docs
SWAGGER_URL = '/docs'
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

# Routes

@app.route('/<path:key>', methods=['POST'])
def store(key):
  '''
    Store a value
    ---
    tags:
      - store
    parameters:
      - in: path
        name: key
        schema:
          type: string
          example: 'group1/users/georgina'
        description: the key you want to fetch the value for
      - in: body
        description: A JSON object to store
        content:
          text/json:
            schema:
              type: object
            example:
              name: georgina
              food: marzipan
    responses:
      200:
        description: Returns a JSON object describing what was stored
        schema:
          id: Value
  '''
  try:
    value = request.get_json()
  except:
    abort(400, 'You need to supply JSON')
  result = db_store(key, value)
  
  return jsonify({
    'key': key,
    'value': value,
    'stored': result
  })

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
        schema:
          type: string
          example: 'group1/users/georgina'
        description: the key you want to fetch the value for
    responses:
      200:
        description: Returns a JSON object describing what was stored
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
  
  if result:
    return jsonify(result)
  else:
    return jsonify({
      'key': key,
      'value': None,
    }), 404


if __name__ == '__main__':
  db_init()
  app.run(debug=True, port=3000)
