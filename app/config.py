import os
from pathlib import Path

DEFAULT_DB_DIR = Path(__file__).resolve().parent.parent / "databases"


def get_db_dir() -> Path:
    return Path(os.environ.get("DENIED_DB_DIR", DEFAULT_DB_DIR))
