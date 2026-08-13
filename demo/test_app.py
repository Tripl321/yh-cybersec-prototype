"""Smoke tests for the SHALLOT WebAuthn auth server.

These exercise the relying-party routes and storage without a real
authenticator. End-to-end registration/login requires a browser with a
FIDO2 passkey (or a virtual authenticator in devtools).
"""
import os
import tempfile
from pathlib import Path

import pytest

# point the store at a temp db before importing the app
_tmp = tempfile.mkdtemp()
os.environ.setdefault("SHALLOT_SECRET", "test-secret")


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr("db.DB_PATH", tmp_path / "shallot_test.db")
    from app import app, db as app_db

    app_db.init_db()
    app.testing = True
    return app.test_client()


def test_index(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "SHALLOT" in r.get_data(as_text=True)


def test_register_begin_returns_options(client):
    r = client.post(
        "/register/begin",
        json={"username": "alice", "display_name": "Alice", "role": "cub"},
    )
    assert r.status_code == 200
    opts = r.get_json()
    assert opts["rp"]["id"] == "localhost"
    assert opts["user"]["name"] == "alice"
    assert opts["challenge"]


def test_register_begin_rejects_bad_role(client):
    r = client.post("/register/begin", json={"username": "bob", "role": "hacker"})
    assert r.status_code == 400


def test_register_begin_requires_username(client):
    r = client.post("/register/begin", json={"role": "cub"})
    assert r.status_code == 400


def test_login_begin_nameless_with_no_credentials(client):
    r = client.post("/login/begin", json={})
    assert r.status_code == 200
    assert r.get_json()["allowCredentials"] == []


def test_dashboard_redirects_when_anonymous(client):
    r = client.get("/dashboard")
    assert r.status_code == 302
