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
