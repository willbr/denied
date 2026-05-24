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
