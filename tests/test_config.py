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


def test_create_app_uses_env_default_when_no_override(monkeypatch, tmp_path):
    monkeypatch.setenv("DENIED_DB_DIR", str(tmp_path))
    from app import create_app
    app = create_app()
    assert app.config["DB_DIR"] == tmp_path


def test_create_app_config_argument_overrides_env(monkeypatch, tmp_path):
    monkeypatch.setenv("DENIED_DB_DIR", "/should/be/overridden")
    from app import create_app
    app = create_app({"DB_DIR": tmp_path})
    assert app.config["DB_DIR"] == tmp_path
