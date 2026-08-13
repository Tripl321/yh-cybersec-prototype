"""SQLite store for SHALLOT users and WebAuthn credentials.

Roles model the SHALLOT access-control split:
  - mama_bear: admin / gateway access point (separate PicoFIDO)
  - cub:       field node / ID-bricka holder
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from webauthn.helpers import bytes_to_base64url, base64url_to_bytes

DB_PATH = Path(__file__).parent / "shallot.db"


@dataclass
class User:
    id: int
    username: str
    display_name: str
    role: str
    handle: str  # base64url user handle (random, stable)


@dataclass
class Credential:
    id: int
    user_id: int
    credential_id: str  # base64url
    public_key: str  # base64url DER
    sign_count: int
    transports: str
    aaguid: str
    fmt: str
    device_type: str
    backed_up: bool


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT UNIQUE NOT NULL,
                display_name  TEXT NOT NULL,
                role          TEXT NOT NULL CHECK (role IN ('mama_bear', 'cub')),
                handle        TEXT NOT NULL UNIQUE
            );
            CREATE TABLE IF NOT EXISTS credentials (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                credential_id   TEXT NOT NULL UNIQUE,
                public_key      TEXT NOT NULL,
                sign_count      INTEGER NOT NULL DEFAULT 0,
                transports      TEXT NOT NULL DEFAULT '',
                aaguid          TEXT NOT NULL DEFAULT '',
                fmt             TEXT NOT NULL DEFAULT '',
                device_type     TEXT NOT NULL DEFAULT '',
                backed_up       INTEGER NOT NULL DEFAULT 0
            );
            """
        )


def get_user_by_username(username: str) -> User | None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    return User(**row) if row else None


def get_user_by_handle(handle: str) -> User | None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE handle = ?", (handle,)).fetchone()
    return User(**row) if row else None


def create_user(username: str, display_name: str, role: str, handle: bytes) -> User:
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO users (username, display_name, role, handle) VALUES (?, ?, ?, ?)",
            (username, display_name, role, bytes_to_base64url(handle)),
        )
        uid = cur.lastrowid
    return User(id=uid, username=username, display_name=display_name, role=role,
                handle=bytes_to_base64url(handle))


def get_credentials_for_user(user_id: int) -> list[Credential]:
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM credentials WHERE user_id = ?", (user_id,)).fetchall()
    return [Credential(**r) for r in rows]


def get_credential_by_id(credential_id_b64: str) -> Credential | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM credentials WHERE credential_id = ?", (credential_id_b64,)
        ).fetchone()
    return Credential(**row) if row else None


def add_credential(
    user_id: int,
    credential_id: bytes,
    public_key: bytes,
    sign_count: int,
    transports: list[str],
    aaguid: str,
    fmt: str,
    device_type: str,
    backed_up: bool,
) -> None:
    with _connect() as conn:
        conn.execute(
            """INSERT INTO credentials
               (user_id, credential_id, public_key, sign_count, transports, aaguid, fmt, device_type, backed_up)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                user_id,
                bytes_to_base64url(credential_id),
                bytes_to_base64url(public_key),
                sign_count,
                ",".join(transports),
                aaguid,  # already a UUID string from py-webauthn
                fmt,
                device_type,
                int(backed_up),
            ),
        )


def update_sign_count(credential_id_b64: str, sign_count: int) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE credentials SET sign_count = ? WHERE credential_id = ?",
            (sign_count, credential_id_b64),
        )


def credential_id_bytes(cred: Credential) -> bytes:
    return base64url_to_bytes(cred.credential_id)


def public_key_bytes(cred: Credential) -> bytes:
    return base64url_to_bytes(cred.public_key)
