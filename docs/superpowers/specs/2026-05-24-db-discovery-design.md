# Database Discovery and Table Listing

**Date:** 2026-05-24
**Status:** Approved

## Goal

First slice of real SQLite behavior on top of the Flask scaffold: discover SQLite databases in a configured directory, list them on `/`, and on selection show the database's table names.

## Non-Goals

- Browsing rows in a table (next slice).
- Views, indexes, or triggers in the table listing.
- Recursive subdirectory scan.
- Showing DB size, mtime, or any other metadata in the list.
- Any write/edit functionality.
- Authentication, sessions, CSRF.
- Upload flow — databases live on the server filesystem.

## Architecture

Two new modules in the `app` package, plus a small touch to `create_app()`:

- `app/config.py` — resolves the database directory from `DENIED_DB_DIR` (env var), falling back to `<repo>/databases/`. Exposes `get_db_dir() -> Path`. `create_app()` calls it once and stores the result on `app.config["DB_DIR"]`.
- `app/databases.py` — pure functions over the filesystem and `sqlite3`. No Flask imports.
- `app/routes.py` — gains a `database` view; `index` is rewritten to render the DB list.
- Templates: `base.html` is unchanged. `index.html` is rewritten as the DB list; `database.html` is new and renders the table list (with an error state).

## Components

### `app/config.py`

```python
import os
from pathlib import Path

DEFAULT_DB_DIR = Path(__file__).resolve().parent.parent / "databases"


def get_db_dir() -> Path:
    return Path(os.environ.get("DENIED_DB_DIR", DEFAULT_DB_DIR))
```

The path is *not* required to exist; missing-directory handling lives in `list_databases`.

### `app/databases.py`

Two pure functions:

```python
import sqlite3
from pathlib import Path

SQLITE_EXTENSIONS = (".sqlite", ".sqlite3", ".db")


def list_databases(db_dir: Path) -> list[str]:
    """Return sorted filenames of SQLite databases in db_dir (top level only).

    Returns [] if db_dir does not exist or is not a directory.
    """
    if not db_dir.is_dir():
        return []
    return sorted(
        entry.name
        for entry in db_dir.iterdir()
        if entry.is_file() and entry.suffix.lower() in SQLITE_EXTENSIONS
    )


def list_tables(db_path: Path) -> list[str]:
    """Return sorted user table names in db_path.

    Hides internal sqlite_* tables. Raises sqlite3.DatabaseError if the file
    isn't a valid SQLite database. The caller is responsible for ensuring
    db_path is a real file inside the configured DB_DIR.
    """
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%' "
            "ORDER BY name"
        ).fetchall()
    finally:
        conn.close()
    return [row[0] for row in rows]
```

No Flask imports, no globals, no caching. A fresh connection per call — simple and avoids stale-schema foot-guns. The `try/finally` is needed because `sqlite3.connect` as a context manager only handles transactions, not closing.

### `app/__init__.py` (modified)

```python
from flask import Flask

from app.config import get_db_dir


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config["DB_DIR"] = get_db_dir()

    if config:
        app.config.update(config)

    from app.routes import main
    app.register_blueprint(main)

    return app
```

Test overrides flow through the existing `config` argument (e.g. `create_app({"DB_DIR": tmp_path})`).

### `app/routes.py` (rewritten)

```python
import sqlite3

from flask import Blueprint, abort, current_app, render_template

from app.databases import list_databases, list_tables

main = Blueprint("main", __name__)


@main.route("/")
def index():
    db_dir = current_app.config["DB_DIR"]
    return render_template(
        "index.html",
        databases=list_databases(db_dir),
        db_dir=db_dir,
    )


@main.route("/db/<name>/")
def database(name: str):
    db_dir = current_app.config["DB_DIR"]
    if name not in list_databases(db_dir):
        abort(404)

    try:
        tables = list_tables(db_dir / name)
    except sqlite3.DatabaseError as exc:
        return render_template("database.html", name=name, error=str(exc))

    return render_template("database.html", name=name, tables=tables)
```

The membership check in `/db/<name>/` is the path-traversal guard: any name not produced by `list_databases` (which only ever yields top-level filenames) is rejected as 404. No string scrubbing needed.

### Templates

`base.html` — unchanged.

`index.html` (rewritten):

```html
{% extends "base.html" %}
{% block title %}denied — databases{% endblock %}
{% block content %}
  <h1>databases</h1>
  {% if databases %}
    <ul>
      {% for name in databases %}
        <li><a href="{{ url_for('main.database', name=name) }}">{{ name }}</a></li>
      {% endfor %}
    </ul>
  {% else %}
    <p>No databases found in <code>{{ db_dir }}</code>.</p>
  {% endif %}
{% endblock %}
```

`database.html` (new):

```html
{% extends "base.html" %}
{% block title %}denied — {{ name }}{% endblock %}
{% block content %}
  <h1>{{ name }}</h1>
  {% if error %}
    <p>Could not read this database: {{ error }}</p>
  {% elif tables %}
    <ul>
      {% for table in tables %}
        <li>{{ table }}</li>
      {% endfor %}
    </ul>
  {% else %}
    <p>This database has no tables.</p>
  {% endif %}
  <p><a href="{{ url_for('main.index') }}">← all databases</a></p>
{% endblock %}
```

Table names aren't links yet — clicking through to row browsing is the next slice.

### `databases/.gitkeep`

The default DB dir is project-relative, so an empty `databases/` directory is committed via a `.gitkeep` so a fresh clone has somewhere for the app to look.

## Data Flow

```
GET /
  └─► routes.index
        └─► list_databases(DB_DIR)
              └─► filesystem iterdir → filter extensions → sort
        └─► render index.html (links to /db/<name>/)

GET /db/<name>/
  └─► routes.database
        ├─ name in list_databases(DB_DIR)? no → 404
        └─ list_tables(DB_DIR / name)
              ├─ ok            → render database.html with tables
              └─ DatabaseError → render database.html with error
```

## Error Handling

| Condition | Behavior |
|-----------|----------|
| `DB_DIR` does not exist or is not a directory | `list_databases` returns `[]`; `/` shows empty-state with the resolved path. |
| `DB_DIR` exists but contains no matching files | Same empty-state message. |
| Requested DB name not in the discovered list (incl. path-traversal attempts) | 404. |
| Requested DB file exists but is empty or corrupt | `list_tables` raises `sqlite3.DatabaseError`; `/db/<name>/` renders with the error message instead of 500. |
| DB file is readable and has no tables | `/db/<name>/` renders "This database has no tables." |

## Testing

Adopting `pytest` as the first dev dependency.

- `uv add --dev pytest`
- `tests/conftest.py` — a `db_dir` fixture that builds a `tmp_path`-backed directory containing:
  - two real SQLite files created via `sqlite3.connect(...)`, each with a handful of user tables. (Testing the `sqlite_*` filter would require `PRAGMA writable_schema` shenanigans to create such a table; skipped — the `NOT LIKE 'sqlite_%'` clause is obviously correct by inspection.)
  - one non-SQLite file with a matching extension (e.g. `corrupt.db` containing the bytes `b"not a database"`) for the error path.
  - one junk file with a non-matching extension (e.g. `notes.txt`) to confirm filtering.
  - Yields the path.
- `tests/test_databases.py`:
  - `list_databases` returns sorted filenames, filters non-matching extensions, returns `[]` for a missing dir.
  - `list_tables` returns user tables, hides `sqlite_*`, raises `DatabaseError` for the corrupt file.
- `tests/test_routes.py`:
  - `/` lists databases when present; shows empty-state when not.
  - `/db/<name>/` returns 200 with table names for a valid DB.
  - `/db/<name>/` returns 404 for an unknown name and for traversal attempts (e.g. `/db/..%2Fsecret/`).
  - `/db/<name>/` returns 200 with the error message for the corrupt DB.

Tests wire `DB_DIR` into the app via `create_app({"DB_DIR": db_dir})`.

## Trade-offs and Rationale

- **Project-relative default with env var override.** Zero-config for tinkering; explicit for deployment. Costs us one committed `databases/.gitkeep`.
- **Fresh connection per request.** A pool would buy nothing at this scale and would invite stale-schema bugs the moment we add write operations.
- **Membership check as path-traversal guard.** Better than string scrubbing because the rule ("must be a file we already enumerated") matches the actual security property we want, rather than approximating it via blacklists.
- **Two pure functions instead of a `DatabaseRepository` class.** No state to carry between calls, so a class would be ceremony. If connection pooling or caching ever lands, that's the moment to introduce one.
- **Adopting `pytest` now.** The scaffold deferred tests because there was no behavior. Discovery, filtering, error handling, and routing are all behavior worth pinning.
