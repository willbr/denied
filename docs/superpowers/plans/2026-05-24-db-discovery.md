# Database Discovery and Table Listing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first slice of real SQLite behavior on top of the existing Flask scaffold — discover SQLite databases in a configured directory, list them on `/`, and on `/db/<name>/` show the database's table names.

**Architecture:** A `config` module resolves `DENIED_DB_DIR` (env var, defaulting to `<repo>/databases/`) into `app.config["DB_DIR"]`. A `databases` module exposes two pure functions (`list_databases`, `list_tables`) that own filesystem + `sqlite3` access. Two routes in the existing `main` blueprint render two templates. A new `tests/` package using `pytest` exercises the pure functions and the routes against a `tmp_path`-backed fixture directory.

**Tech Stack:** Python ≥3.11, Flask, stdlib `sqlite3`, `pytest` (new dev dependency), `uv` for dep management.

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `pyproject.toml` | modify | Add `pytest` to `dependency-groups.dev`. |
| `databases/.gitkeep` | create | Make the default DB dir exist on a fresh clone. |
| `app/config.py` | create | `get_db_dir()` — resolves env var or default. |
| `app/databases.py` | create | `list_databases(db_dir)` and `list_tables(db_path)`. |
| `app/__init__.py` | modify | Wire `DB_DIR` into `app.config`. |
| `app/routes.py` | modify | Rewrite `index`; add `database` view. |
| `app/templates/index.html` | rewrite | Render the DB list (or empty state). |
| `app/templates/database.html` | create | Render the table list (or error/empty state). |
| `tests/__init__.py` | create | Make `tests/` a package. |
| `tests/conftest.py` | create | `db_dir`, `app`, and `client` pytest fixtures. |
| `tests/test_config.py` | create | Tests for `get_db_dir`. |
| `tests/test_databases.py` | create | Tests for `list_databases` and `list_tables`. |
| `tests/test_routes.py` | create | Tests for `/` and `/db/<name>/`. |

---

### Task 1: Add pytest and create the default databases directory

**Files:**
- Modify: `pyproject.toml`
- Create: `databases/.gitkeep`

- [ ] **Step 1: Add pytest as a dev dependency**

Run from the repo root:

```bash
uv add --dev pytest
```

Expected: `uv.lock` updates; `pyproject.toml` gains either a `[dependency-groups]` table with `dev = ["pytest>=..."]` or a `[tool.uv]` dev-dependencies entry (depends on uv version — accept whichever uv writes).

- [ ] **Step 2: Verify pytest runs**

Run: `uv run pytest --version`

Expected: prints a `pytest X.Y.Z` line and exits 0.

- [ ] **Step 3: Create the default databases directory with a `.gitkeep`**

```bash
mkdir -p databases && touch databases/.gitkeep
```

- [ ] **Step 4: Confirm `*.db` ignore does not swallow `.gitkeep`**

Run: `git status --short databases/`

Expected: `?? databases/.gitkeep` appears (the `.gitkeep` is tracked-as-untracked, not ignored). If anything looks off, re-check `.gitignore` — only `*.sqlite`, `*.sqlite3`, `*.db` should be ignored, none of which match `.gitkeep`.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml uv.lock databases/.gitkeep
git commit -m "Add pytest dev dep and default databases/ directory"
```

---

### Task 2: Build the config module (TDD)

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/test_config.py`
- Create: `app/config.py`

- [ ] **Step 1: Create the empty `tests/__init__.py`**

```bash
mkdir -p tests && touch tests/__init__.py
```

- [ ] **Step 2: Write the failing tests for `get_db_dir`**

Create `tests/test_config.py`:

```python
from pathlib import Path

from app.config import DEFAULT_DB_DIR, get_db_dir


def test_get_db_dir_returns_default_when_env_unset(monkeypatch):
    monkeypatch.delenv("DENIED_DB_DIR", raising=False)
    assert get_db_dir() == DEFAULT_DB_DIR


def test_get_db_dir_returns_env_value_when_set(monkeypatch, tmp_path):
    monkeypatch.setenv("DENIED_DB_DIR", str(tmp_path))
    assert get_db_dir() == tmp_path


def test_default_db_dir_points_at_repo_databases_dir():
    # DEFAULT_DB_DIR should be <repo>/databases/, i.e. sibling of the app package.
    assert DEFAULT_DB_DIR.name == "databases"
    assert DEFAULT_DB_DIR.parent == Path(__file__).resolve().parent.parent
```

- [ ] **Step 3: Run the test to verify it fails**

Run: `uv run pytest tests/test_config.py -v`

Expected: collection error / ImportError — `app.config` module does not exist yet.

- [ ] **Step 4: Implement `app/config.py`**

Create `app/config.py`:

```python
import os
from pathlib import Path

DEFAULT_DB_DIR = Path(__file__).resolve().parent.parent / "databases"


def get_db_dir() -> Path:
    return Path(os.environ.get("DENIED_DB_DIR", DEFAULT_DB_DIR))
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `uv run pytest tests/test_config.py -v`

Expected: 3 passed.

- [ ] **Step 6: Commit**

```bash
git add app/config.py tests/__init__.py tests/test_config.py
git commit -m "Add config.get_db_dir for resolving DENIED_DB_DIR"
```

---

### Task 3: Implement `list_databases` (TDD)

**Files:**
- Create: `app/databases.py`
- Create: `tests/test_databases.py`

This task introduces the `databases` module with only `list_databases`. `list_tables` lands in the next task — keeping them separate keeps each test set focused.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_databases.py`:

```python
import sqlite3
from pathlib import Path

import pytest

from app.databases import list_databases


def _make_sqlite_file(path: Path) -> None:
    """Create a minimal but valid SQLite file at path."""
    conn = sqlite3.connect(path)
    try:
        conn.execute("CREATE TABLE t (x INTEGER)")
    finally:
        conn.close()


def test_list_databases_returns_matching_files_sorted(tmp_path):
    _make_sqlite_file(tmp_path / "b.sqlite")
    _make_sqlite_file(tmp_path / "a.db")
    _make_sqlite_file(tmp_path / "c.sqlite3")

    assert list_databases(tmp_path) == ["a.db", "b.sqlite", "c.sqlite3"]


def test_list_databases_filters_non_matching_extensions(tmp_path):
    _make_sqlite_file(tmp_path / "real.sqlite")
    (tmp_path / "notes.txt").write_text("hello")
    (tmp_path / "README").write_text("hi")

    assert list_databases(tmp_path) == ["real.sqlite"]


def test_list_databases_ignores_subdirectories(tmp_path):
    _make_sqlite_file(tmp_path / "top.sqlite")
    sub = tmp_path / "nested"
    sub.mkdir()
    _make_sqlite_file(sub / "inside.sqlite")

    assert list_databases(tmp_path) == ["top.sqlite"]


def test_list_databases_extension_match_is_case_insensitive(tmp_path):
    _make_sqlite_file(tmp_path / "UPPER.SQLITE")
    assert list_databases(tmp_path) == ["UPPER.SQLITE"]


def test_list_databases_returns_empty_for_missing_directory(tmp_path):
    missing = tmp_path / "does-not-exist"
    assert list_databases(missing) == []


def test_list_databases_returns_empty_when_path_is_a_file(tmp_path):
    f = tmp_path / "a-file.sqlite"
    _make_sqlite_file(f)
    assert list_databases(f) == []
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_databases.py -v`

Expected: ImportError — `app.databases` does not exist yet.

- [ ] **Step 3: Implement `app/databases.py` with `list_databases`**

Create `app/databases.py`:

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
```

(The `import sqlite3` is unused for now; `list_tables` in the next task uses it. Leaving it in keeps the diff there tighter, but if your linter complains, remove it now and re-add in Task 4.)

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_databases.py -v`

Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add app/databases.py tests/test_databases.py
git commit -m "Add databases.list_databases for discovering SQLite files"
```

---

### Task 4: Implement `list_tables` (TDD)

**Files:**
- Modify: `app/databases.py`
- Modify: `tests/test_databases.py`

- [ ] **Step 1: Add failing tests for `list_tables`**

Append to `tests/test_databases.py`:

```python
from app.databases import list_tables  # add to the existing imports at the top of the file


def test_list_tables_returns_user_tables_sorted(tmp_path):
    db = tmp_path / "data.sqlite"
    conn = sqlite3.connect(db)
    try:
        conn.execute("CREATE TABLE zebra (id INTEGER)")
        conn.execute("CREATE TABLE apple (id INTEGER)")
        conn.execute("CREATE TABLE mango (id INTEGER)")
    finally:
        conn.close()

    assert list_tables(db) == ["apple", "mango", "zebra"]


def test_list_tables_returns_empty_for_database_with_no_tables(tmp_path):
    db = tmp_path / "empty.sqlite"
    # Touch a connection so the file becomes a valid (empty) SQLite db.
    conn = sqlite3.connect(db)
    conn.close()

    assert list_tables(db) == []


def test_list_tables_raises_database_error_on_corrupt_file(tmp_path):
    db = tmp_path / "corrupt.db"
    db.write_bytes(b"not a database")

    with pytest.raises(sqlite3.DatabaseError):
        list_tables(db)
```

Move the `from app.databases import list_tables` up next to the existing `from app.databases import list_databases` (a single combined import line is cleaner: `from app.databases import list_databases, list_tables`).

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest tests/test_databases.py -v`

Expected: ImportError on `list_tables`.

- [ ] **Step 3: Implement `list_tables` in `app/databases.py`**

Append to `app/databases.py`:

```python
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

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest tests/test_databases.py -v`

Expected: 9 passed (6 from Task 3 + 3 new).

- [ ] **Step 5: Commit**

```bash
git add app/databases.py tests/test_databases.py
git commit -m "Add databases.list_tables for reading user tables from a SQLite file"
```

---

### Task 5: Wire DB_DIR into create_app and add shared test fixtures

**Files:**
- Modify: `app/__init__.py`
- Create: `tests/conftest.py`

The fixture and the factory change land together because the fixture is what proves the factory wiring works.

- [ ] **Step 1: Modify `app/__init__.py` to populate `app.config["DB_DIR"]`**

Replace the existing contents of `app/__init__.py` with:

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

Order matters: the env-derived default is set first, then any explicit `config` argument overrides it. Tests use the override path; production gets the env-derived default.

- [ ] **Step 2: Create `tests/conftest.py` with shared fixtures**

Create `tests/conftest.py`:

```python
import sqlite3
from pathlib import Path

import pytest

from app import create_app


@pytest.fixture
def db_dir(tmp_path: Path) -> Path:
    """A directory pre-populated with realistic test data.

    Contents:
      - alpha.sqlite — has tables `users` and `posts`
      - beta.db      — has table `items`
      - corrupt.db   — matching extension, bogus contents
      - notes.txt    — non-matching extension (should be ignored)
    """
    alpha = tmp_path / "alpha.sqlite"
    conn = sqlite3.connect(alpha)
    try:
        conn.execute("CREATE TABLE users (id INTEGER)")
        conn.execute("CREATE TABLE posts (id INTEGER)")
    finally:
        conn.close()

    beta = tmp_path / "beta.db"
    conn = sqlite3.connect(beta)
    try:
        conn.execute("CREATE TABLE items (id INTEGER)")
    finally:
        conn.close()

    (tmp_path / "corrupt.db").write_bytes(b"not a database")
    (tmp_path / "notes.txt").write_text("ignore me")

    return tmp_path


@pytest.fixture
def app(db_dir: Path):
    application = create_app({"DB_DIR": db_dir, "TESTING": True})
    return application


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def empty_db_dir(tmp_path: Path) -> Path:
    """A real but empty directory — for empty-state tests."""
    sub = tmp_path / "empty"
    sub.mkdir()
    return sub


@pytest.fixture
def missing_db_dir(tmp_path: Path) -> Path:
    """A path that does not exist on disk — for missing-dir tests."""
    return tmp_path / "does-not-exist"
```

- [ ] **Step 3: Smoke-test the factory wiring**

Add a small test to confirm the factory respects both paths. Append to `tests/test_config.py`:

```python
from app import create_app


def test_create_app_uses_env_default_when_no_override(monkeypatch, tmp_path):
    monkeypatch.setenv("DENIED_DB_DIR", str(tmp_path))
    app = create_app()
    assert app.config["DB_DIR"] == tmp_path


def test_create_app_config_argument_overrides_env(monkeypatch, tmp_path):
    monkeypatch.setenv("DENIED_DB_DIR", "/should/be/overridden")
    app = create_app({"DB_DIR": tmp_path})
    assert app.config["DB_DIR"] == tmp_path
```

- [ ] **Step 4: Run all tests to verify they pass**

Run: `uv run pytest -v`

Expected: 5 config tests + 9 databases tests = 14 passed.

- [ ] **Step 5: Commit**

```bash
git add app/__init__.py tests/conftest.py tests/test_config.py
git commit -m "Wire DB_DIR into create_app and add shared test fixtures"
```

---

### Task 6: Rewrite the `/` index route to render the database list

**Files:**
- Rewrite: `app/templates/index.html`
- Modify: `app/routes.py`
- Create: `tests/test_routes.py`

Templates land in this task too — the route test would 500 on missing template otherwise.

- [ ] **Step 1: Rewrite `app/templates/index.html`**

Replace the entire contents of `app/templates/index.html` with:

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

The `url_for('main.database', ...)` reference compiles fine even before the route exists, because Jinja resolves it at render time. The route lands in this same task before the tests run.

- [ ] **Step 2: Write failing tests for `/`**

Create `tests/test_routes.py`:

```python
from app import create_app


def test_index_lists_discovered_databases(client):
    response = client.get("/")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "alpha.sqlite" in body
    assert "beta.db" in body
    assert "corrupt.db" in body  # corrupt files still appear in the list
    assert "notes.txt" not in body  # non-matching extension


def test_index_links_each_database(client):
    response = client.get("/")
    body = response.get_data(as_text=True)
    assert 'href="/db/alpha.sqlite/"' in body
    assert 'href="/db/beta.db/"' in body


def test_index_empty_state_for_empty_directory(empty_db_dir):
    app = create_app({"DB_DIR": empty_db_dir, "TESTING": True})
    response = app.test_client().get("/")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "No databases found" in body
    assert str(empty_db_dir) in body


def test_index_empty_state_for_missing_directory(missing_db_dir):
    app = create_app({"DB_DIR": missing_db_dir, "TESTING": True})
    response = app.test_client().get("/")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "No databases found" in body
    assert str(missing_db_dir) in body
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `uv run pytest tests/test_routes.py -v`

Expected: tests fail — the existing `/` route still renders the placeholder content from the scaffold and doesn't pass `databases` to the template.

- [ ] **Step 4: Rewrite `app/routes.py` with the new index view plus a stub `database` view**

The template references `url_for('main.database', name=...)`, which raises `BuildError` if the endpoint doesn't exist. So this task adds a `database` *stub* now (returning 501) and Task 7 replaces it with the real implementation. This keeps each task's tests green on their own.

Replace the entire contents of `app/routes.py` with:

```python
from flask import Blueprint, abort, current_app, render_template

from app.databases import list_databases

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
    # Stub — real implementation lands in Task 7.
    abort(501)
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `uv run pytest tests/test_routes.py -v`

Expected: 4 passed (the four `test_index_*` tests).

- [ ] **Step 6: Run the full suite**

Run: `uv run pytest -v`

Expected: all green (14 from earlier + 4 new = 18 passed).

- [ ] **Step 7: Commit**

```bash
git add app/routes.py app/templates/index.html tests/test_routes.py
git commit -m "Render database list on / with empty-state fallback"
```

---

### Task 7: Implement the `/db/<name>/` route and database template

**Files:**
- Modify: `app/routes.py`
- Create: `app/templates/database.html`
- Modify: `tests/test_routes.py`

- [ ] **Step 1: Create `app/templates/database.html`**

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

- [ ] **Step 2: Add failing tests for `/db/<name>/`**

Append to `tests/test_routes.py`:

```python
def test_database_route_lists_tables_for_valid_db(client):
    response = client.get("/db/alpha.sqlite/")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "alpha.sqlite" in body
    assert "users" in body
    assert "posts" in body


def test_database_route_shows_empty_state_when_db_has_no_tables(tmp_path):
    import sqlite3
    db_path = tmp_path / "empty.sqlite"
    sqlite3.connect(db_path).close()

    app = create_app({"DB_DIR": tmp_path, "TESTING": True})
    response = app.test_client().get("/db/empty.sqlite/")
    assert response.status_code == 200
    assert "This database has no tables." in response.get_data(as_text=True)


def test_database_route_returns_404_for_unknown_name(client):
    response = client.get("/db/does-not-exist.sqlite/")
    assert response.status_code == 404


def test_database_route_returns_404_for_path_traversal_attempt(client):
    # %2F decodes to /, so this attempts to escape the DB dir.
    response = client.get("/db/..%2Fsecret.sqlite/")
    assert response.status_code == 404


def test_database_route_returns_404_for_non_sqlite_file_in_dir(client):
    # notes.txt exists in db_dir but doesn't have a SQLite extension,
    # so it is not in list_databases() and the route should 404.
    response = client.get("/db/notes.txt/")
    assert response.status_code == 404


def test_database_route_renders_error_for_corrupt_db(client):
    response = client.get("/db/corrupt.db/")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "Could not read this database" in body
    assert "corrupt.db" in body
```

- [ ] **Step 3: Run the new tests to verify they fail**

Run: `uv run pytest tests/test_routes.py -v -k database_route`

Expected: most fail with either 501 (the placeholder) or template-not-found errors.

- [ ] **Step 4: Replace the placeholder `database` view with the real one**

In `app/routes.py`, replace the placeholder body so the file reads in full:

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

- [ ] **Step 5: Run the full suite**

Run: `uv run pytest -v`

Expected: 24 passed (18 + 6 new). All green.

- [ ] **Step 6: Commit**

```bash
git add app/routes.py app/templates/database.html tests/test_routes.py
git commit -m "Add /db/<name>/ route showing table list with 404 and error states"
```

---

### Task 8: Manual smoke test against the running dev server

This is the end-to-end sanity check. It uses real disk, real templates, real Flask.

**Files:** none modified.

- [ ] **Step 1: Put a real SQLite database in `databases/`**

```bash
uv run python -c "import sqlite3; c = sqlite3.connect('databases/scratch.sqlite'); c.execute('CREATE TABLE notes (id INTEGER, body TEXT)'); c.execute('CREATE TABLE tags (id INTEGER, label TEXT)'); c.close()"
```

(Listing it in `databases/`: the file will be ignored by git because `*.sqlite` is in `.gitignore` — that's intentional.)

- [ ] **Step 2: Start the dev server in the background**

```bash
uv run python run.py
```

Run this with `run_in_background: true` (or in a separate terminal). Expected log lines include `* Running on http://127.0.0.1:5000` and `* Debugger is active!`.

- [ ] **Step 3: Hit `/` and confirm the database list**

```bash
curl -sS http://127.0.0.1:5000/ | tee /tmp/denied-index.html | grep -F "scratch.sqlite"
```

Expected: the grep prints a line containing `scratch.sqlite`. Inspect `/tmp/denied-index.html` to confirm the link's `href` is `/db/scratch.sqlite/`.

- [ ] **Step 4: Hit `/db/scratch.sqlite/` and confirm the table list**

```bash
curl -sS http://127.0.0.1:5000/db/scratch.sqlite/ | tee /tmp/denied-scratch.html | grep -E "notes|tags"
```

Expected: both `notes` and `tags` appear in the output.

- [ ] **Step 5: Hit a bogus DB name and confirm 404**

```bash
curl -sS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:5000/db/nope.sqlite/
```

Expected: `404`.

- [ ] **Step 6: Make a corrupt file and confirm the error page**

```bash
printf 'garbage' > databases/broken.db
curl -sS http://127.0.0.1:5000/db/broken.db/ | grep -F "Could not read this database"
```

Expected: the grep finds the error message. Status is 200 (not 500).

- [ ] **Step 7: Clean up the smoke-test artifacts**

```bash
rm -f databases/scratch.sqlite databases/broken.db
```

- [ ] **Step 8: Stop the dev server**

Kill the background process (or Ctrl-C if foregrounded). Confirm with `lsof -i :5000` that nothing is still bound.

- [ ] **Step 9: Final verification**

Run: `git status`

Expected: working tree clean. No untracked files except possibly `__pycache__/` and `.pytest_cache/`, both covered by `.gitignore` (`.pytest_cache/` may need to be added — if it appears, add a line `.pytest_cache/` to `.gitignore` and commit it as a separate one-line "ignore pytest cache" commit).
