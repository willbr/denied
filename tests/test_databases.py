import sqlite3
from pathlib import Path

import pytest

from app.databases import list_databases, list_tables


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
