# Flask App Scaffold Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up a minimal Flask app skeleton for the `denied` SQLite editor — package-based layout with `create_app()` factory, single placeholder route, no SQLite logic.

**Architecture:** uv-managed Python project. `app/` package exposes `create_app()`, which registers a single `main` blueprint with one `GET /` route rendering a placeholder template. `run.py` at the repo root is the dev entrypoint.

**Tech Stack:** Python ≥3.11, Flask, Jinja2 (bundled with Flask), uv for dependency management.

**Note on TDD:** The spec explicitly lists "Tests for the placeholder route" as a non-goal. This plan therefore uses smoke testing (start the server, hit `/`, confirm 200 + expected content) instead of unit tests. Test infrastructure lands when there is real behavior to test.

---

## File Structure

Files this plan creates:

| File | Responsibility |
|------|----------------|
| `pyproject.toml` | uv project metadata, Python version constraint, runtime deps (Flask only) |
| `.python-version` | Python version pin (uv writes this) |
| `.gitignore` | Ignore caches, venvs, env files, and SQLite databases |
| `app/__init__.py` | `create_app(config=None)` factory; registers the `main` blueprint |
| `app/routes.py` | `main` Blueprint with one route: `GET /` → `index.html` |
| `app/templates/base.html` | Minimal HTML5 skeleton with a `content` block |
| `app/templates/index.html` | Extends `base.html`; placeholder content |
| `app/static/.gitkeep` | Empty file so the static directory exists in git |
| `run.py` | Dev entrypoint: `app = create_app(); app.run(debug=True)` |

Files this plan does NOT touch: `readme.md`, the existing design doc.

---

### Task 1: Initialize the uv project

**Files:**
- Create: `pyproject.toml`
- Create: `.python-version` (uv writes this)
- Create: `.gitignore`

- [ ] **Step 1: Initialize the uv project**

Run from the repo root:

```bash
uv init --name denied --package=false --no-readme --no-workspace --bare
```

Notes:
- `--name denied` — project name.
- `--package=false` — we're an application, not a library; uv won't create a `src/` layout.
- `--no-readme` — `readme.md` already exists; don't overwrite.
- `--no-workspace` — don't add this to a parent workspace if one exists.
- `--bare` — minimal scaffolding (no `main.py`, no sample code). We're providing our own structure.

Expected result: `pyproject.toml` and `.python-version` created. No `hello.py` or sample files.

- [ ] **Step 2: Verify pyproject.toml content**

Run: `cat pyproject.toml`

Expected: a `[project]` table with `name = "denied"`, a `version`, and a `requires-python` constraint. If `requires-python` is below `>=3.11`, edit it to `>=3.11`.

- [ ] **Step 3: Add Flask as a runtime dependency**

Run: `uv add flask`

Expected: Flask is added under `dependencies` in `pyproject.toml`, `uv.lock` is created, and a `.venv/` directory appears.

- [ ] **Step 4: Create `.gitignore`**

Create `.gitignore` with this exact content:

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class

# Virtual environments
.venv/
venv/

# Environment files
.env

# SQLite databases (user-supplied or scratch)
*.sqlite
*.sqlite3
*.db

# Editor / OS
.DS_Store
.idea/
.vscode/
```

- [ ] **Step 5: Verify `.venv/` is ignored**

Run: `git status --short`

Expected: `.venv/` does NOT appear in the output. `pyproject.toml`, `uv.lock`, `.python-version`, and `.gitignore` DO appear as untracked.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml uv.lock .python-version .gitignore
git commit -m "Initialize uv project with Flask dependency"
```

---

### Task 2: Create the application factory and blueprint

**Files:**
- Create: `app/__init__.py`
- Create: `app/routes.py`

- [ ] **Step 1: Create `app/__init__.py`**

```python
from flask import Flask


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)

    if config:
        app.config.update(config)

    from app.routes import main
    app.register_blueprint(main)

    return app
```

- [ ] **Step 2: Create `app/routes.py`**

```python
from flask import Blueprint, render_template

main = Blueprint("main", __name__)


@main.route("/")
def index():
    return render_template("index.html")
```

- [ ] **Step 3: Verify the package imports cleanly**

Run: `uv run python -c "from app import create_app; app = create_app(); print(app.url_map)"`

Expected: prints a URL map that includes a rule for `/` pointing to `main.index`. No import errors.

(The view will fail to *render* until templates exist — that's Task 3. Importing and instantiating the app is enough here.)

---

### Task 3: Create templates

**Files:**
- Create: `app/templates/base.html`
- Create: `app/templates/index.html`

- [ ] **Step 1: Create `app/templates/base.html`**

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{% block title %}denied{% endblock %}</title>
  </head>
  <body>
    {% block content %}{% endblock %}
  </body>
</html>
```

- [ ] **Step 2: Create `app/templates/index.html`**

```html
{% extends "base.html" %}

{% block title %}denied — sqlite editor{% endblock %}

{% block content %}
  <h1>denied</h1>
  <p>A web-based SQLite editor. Not yet built — this is a placeholder.</p>
{% endblock %}
```

- [ ] **Step 3: Verify the template renders**

Run:

```bash
uv run python -c "from app import create_app; app = create_app(); client = app.test_client(); r = client.get('/'); print(r.status_code); print(r.data.decode())"
```

Expected output:
- `200`
- HTML containing `<h1>denied</h1>` and the placeholder paragraph.

---

### Task 4: Create the static directory placeholder

**Files:**
- Create: `app/static/.gitkeep`

- [ ] **Step 1: Create the static directory with a `.gitkeep`**

```bash
mkdir -p app/static && touch app/static/.gitkeep
```

(Flask will auto-discover `app/static/` once it exists. The `.gitkeep` keeps the empty directory under version control.)

---

### Task 5: Create the dev entrypoint and smoke-test the running server

**Files:**
- Create: `run.py`

- [ ] **Step 1: Create `run.py`**

```python
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
```

- [ ] **Step 2: Start the dev server in the background**

```bash
uv run python run.py
```

Run this with `run_in_background: true` (or in a separate terminal). Expected log lines include `* Running on http://127.0.0.1:5000` and `* Debugger is active!`.

- [ ] **Step 3: Hit the route**

```bash
curl -sS -o /tmp/denied-index.html -w "%{http_code}\n" http://127.0.0.1:5000/
```

Expected output: `200`.

- [ ] **Step 4: Verify the response body**

```bash
grep -F "<h1>denied</h1>" /tmp/denied-index.html && grep -F "sqlite editor" /tmp/denied-index.html
```

Expected: both `grep` commands print their matched lines and exit 0.

- [ ] **Step 5: Stop the dev server**

Kill the background process (or Ctrl-C if it was foregrounded). Confirm with `lsof -i :5000` that nothing is still bound to the port.

- [ ] **Step 6: Commit everything from Tasks 2–5**

```bash
git add app/ run.py
git commit -m "Scaffold Flask app factory, blueprint, templates, and dev entrypoint"
```

- [ ] **Step 7: Final verification**

Run: `git status`

Expected: working tree clean. No untracked files (other than possibly `__pycache__/` directories, which `.gitignore` covers).
