# Flask App Scaffold

**Date:** 2026-05-24
**Status:** Approved

## Goal

Stand up a minimal Flask project skeleton for the `denied` SQLite editor. This scaffold contains no SQLite logic — it establishes the project layout, dependency management, and a single placeholder route so that subsequent work (DB connection, table browsing, editing) has a clear home.

## Non-Goals

- SQLite connection or file handling
- File upload, table listing, row browsing, editing
- Authentication, sessions, CSRF
- Styling beyond a bare HTML page
- Production deployment configuration (gunicorn, Docker, etc.)
- Tests for the placeholder route

These are deferred to later specs.

## Architecture

A package-based Flask app using the application factory pattern, managed by `uv`.

```
denied/
├── app/
│   ├── __init__.py        # create_app() factory
│   ├── routes.py          # `main` blueprint, GET /
│   ├── templates/
│   │   ├── base.html
│   │   └── index.html
│   └── static/
│       └── .gitkeep
├── run.py                 # dev entrypoint
├── pyproject.toml         # uv project metadata + deps
├── .python-version        # uv-managed
├── .gitignore
└── readme.md              # existing
```

## Components

### `app/__init__.py` — application factory

Exposes `create_app(config: dict | None = None) -> Flask`. The factory:

1. Instantiates `Flask(__name__)`.
2. Applies optional config overrides from the `config` argument (no defaults beyond Flask's own for now).
3. Imports the `main` blueprint from `app.routes` and registers it.
4. Returns the app.

The factory takes an optional config dict purely to keep future testability easy; no config keys are defined yet.

### `app/routes.py` — main blueprint

Defines `main = Blueprint("main", __name__)` and a single route:

- `GET /` → renders `index.html`.

No other routes.

### Templates

- `base.html`: minimal HTML5 skeleton with `<title>` and a `{% block content %}{% endblock %}`. No CSS, no JS.
- `index.html`: extends `base.html`, fills `content` with a placeholder heading like "denied — sqlite editor" and a short note that the editor is not yet built.

### `run.py` — dev entrypoint

```python
from app import create_app
app = create_app()
if __name__ == "__main__":
    app.run(debug=True)
```

Allows both `uv run python run.py` and `uv run flask --app app run --debug` (the latter works because the factory is named `create_app` and the package is named `app`).

### `pyproject.toml`

- `name = "denied"`, version `0.1.0`.
- `requires-python = ">=3.11"`.
- Dependencies: `flask` only (no upper pin; let uv resolve).
- No dev dependencies yet (tests come later).

### `.gitignore`

Covers:
- `__pycache__/`, `*.pyc`, `*.pyo`
- `.venv/`, `venv/`
- `.env`
- `*.sqlite`, `*.sqlite3`, `*.db` — preemptive, so future user-supplied databases don't get committed.

### `.python-version`

Created by `uv` (e.g. `3.13` or the latest stable). Not authored by hand.

## How It Runs

After cloning:

```
uv sync
uv run python run.py
```

Visiting `http://127.0.0.1:5000/` shows the placeholder page.

## Trade-offs and Rationale

- **App factory over single-file `app.py`**: chosen for growth. The SQLite editor will need at least a separate "connection" concern and probably multiple route groups (browse, edit, query). Starting with a blueprint avoids a refactor in the very next step.
- **Only `flask` as a dependency**: no SQLAlchemy because the project goal is a SQLite *editor*, which works most naturally with the stdlib `sqlite3` module — there is no ORM-shaped problem here. No `python-dotenv` because there's nothing to configure.
- **`*.sqlite` / `*.db` in `.gitignore` now**: cheap insurance against a user accidentally committing a working database when they start using the editor.
