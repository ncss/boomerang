from flask import Flask, g, request, jsonify

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
  conn = get_db()
  c = conn.cursor()
  c.execute('''INSERT INTO store
               VALUES (?, ?, strftime('%Y-%m-%d %H:%M:%S', 'now'), strftime('%Y-%m-%d %H:%M:%S', 'now'))
               ON CONFLICT (key) DO UPDATE SET
                 key = ?,
                 value = ?,
                 updated = strftime('%Y-%m-%d %H:%M:%S', 'now')
               ''', (key, value, key, value))
  conn.commit()
  return True 

def db_fetch(key):
  c = get_db().cursor()
  c.execute('SELECT * FROM store WHERE key=? LIMIT 1', (key,))
  return c.fetchone()

# Routes

@app.route('/<path:key>', methods=['POST'])
def store(key):
  value = request.args.get('value')
  result = db_store(key, value)
  
  return jsonify({
    'key': key,
    'value': value,
    'stored': result
  })

@app.route('/<path:key>', methods=['GET'])
def fetch(key):
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
