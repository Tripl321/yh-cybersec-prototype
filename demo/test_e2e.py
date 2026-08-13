"""End-to-end WebAuthn test using a software authenticator.

Proves that registration actually verifies a real attestation and stores a
usable credential, and that the stored credential can later authenticate.
No browser or hardware key required.
"""
import os
import tempfile
from pathlib import Path

import pytest

os.environ.setdefault("SHALLOT_SECRET", "test-secret")


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setattr("db.DB_PATH", Path(tempfile.mkdtemp()) / "shallot_e2e.db")
    from app import app, db as app_db

    app_db.init_db()
    app.testing = True
    return app.test_client()


def _register(client, auth, username, role):
    h = {"Host": "localhost:8000"}
    r = client.post(
        "/register/begin",
        json={"username": username, "display_name": username, "role": role},
        headers=h,
    )
    assert r.status_code == 200, r.get_data(as_text=True)
    body = auth.register(r.get_json())
    r = client.post("/register/complete", json=body, headers=h)
    assert r.status_code == 200, r.get_data(as_text=True)
    return r.get_json()


def _login(client, auth, username):
    h = {"Host": "localhost:8000"}
    r = client.post("/login/begin", json={"username": username}, headers=h)
    assert r.status_code == 200, r.get_data(as_text=True)
    body = auth.authenticate(r.get_json())
    return client.post("/login/complete", json=body, headers=h)


def test_full_flow_mama_bear(client):
    from app import db
    from soft_auth import SoftAuthenticator

    auth = SoftAuthenticator()
    out = _register(client, auth, "mama", "mama_bear")
    assert out["status"] == "ok" and out["role"] == "mama_bear"

    user = db.get_user_by_username("mama")
    creds = db.get_credentials_for_user(user.id)
    assert len(creds) == 1, "credential must be stored after registration"
    print("\n[mama_bear] stored credential:", creds[0].credential_id[:24], "fmt=", creds[0].fmt)

    r = _login(client, auth, "mama")
    assert r.status_code == 200, r.get_data(as_text=True)
    assert r.get_json()["status"] == "ok"


def test_full_flow_cub(client):
    from app import db
    from soft_auth import SoftAuthenticator

    auth = SoftAuthenticator()
    out = _register(client, auth, "cub", "cub")
    assert out["status"] == "ok" and out["role"] == "cub"

    user = db.get_user_by_username("cub")
    creds = db.get_credentials_for_user(user.id)
    assert len(creds) == 1

    r = _login(client, auth, "cub")
    assert r.status_code == 200, r.get_data(as_text=True)
