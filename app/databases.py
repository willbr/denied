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
