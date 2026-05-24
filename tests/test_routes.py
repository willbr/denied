import sqlite3

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


def test_database_route_lists_tables_for_valid_db(client):
    response = client.get("/db/alpha.sqlite/")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "alpha.sqlite" in body
    assert "users" in body
    assert "posts" in body
    # Tables should render in sorted order.
    assert body.index("posts") < body.index("users")


def test_database_route_shows_empty_state_when_db_has_no_tables(tmp_path):
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


def test_database_route_does_not_create_ghost_file_when_db_vanishes(client, monkeypatch, db_dir):
    # Simulate a race: list_databases returns a name whose file no longer exists.
    # Without the file-exists guard, sqlite3.connect would silently create a ghost
    # file in db_dir.
    from app import routes

    monkeypatch.setattr(routes, "list_databases", lambda _: ["ghost.sqlite"])

    response = client.get("/db/ghost.sqlite/")
    assert response.status_code == 404
    assert not (db_dir / "ghost.sqlite").exists()
