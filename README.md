# Boomerang

Boomerang is a dead-simple key-value store: put a key-value pair in, and it comes back!


# Interface

There are a few URLs reserved by the server, such as `/docs` endpoint for the Swagger generated docs.
Every other path is interpreted as a key, which may have an associated JSON value.

- `POST /my/key` with a JSON payload to store.
- `GET /my/key` to retrieve the value stored at the key.
- `DELETE /my/key` to remove the key.

See the auto-generated API docs for more details.


# Installation and deployment.

Install the environment using [Poetry](https://python-poetry.org/), this will ensure you get exactly the same versions of packages that we were using last time.

```
$ poetry env use python3.10
$ poetry install --no-root
$ poetry run python server_test.py
$ poetry run python server.py
```

The server will write to a local Sqlite3 database called `store.db`.

To run in production, use `gunicorn` instead with some access logging set up:

```
$ poetry run gunicorn --forwarded-allow-ips '*' --bind 0.0.0.0:6280 --access-logfile - server:app
```
