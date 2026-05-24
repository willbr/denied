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
