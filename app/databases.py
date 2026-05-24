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
