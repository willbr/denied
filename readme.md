# denied

A web-based SQLite editor. Python + Flask. Early-stage — currently browse-only.

## Run

```sh
uv sync
uv run python run.py
```

Then open <http://127.0.0.1:5000/>.

## Configure

Databases live on the server filesystem. By default, the app scans `./databases/` (top level only, files matching `*.sqlite`, `*.sqlite3`, `*.db`). Override with:

```sh
DENIED_DB_DIR=/path/to/your/dbs uv run python run.py
```

## What works today

- `/` — lists discovered databases.
- `/db/<name>/` — lists the user tables in one database (internal `sqlite_*` tables are hidden).

Clicking a table to browse rows, editing, querying — not yet built.

## Tests

```sh
uv run pytest
```
