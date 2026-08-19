"""SHALLOT WebAuthn auth server (Mama Bear / Cub).

A minimal Flask relying party that demonstrates FIDO2/WebAuthn-based
presence access control for OT environments.

Run:
    flask --app app run --port 5000
or
    python app.py
"""
from __future__ import annotations

import logging
import os
import secrets

from flask import (
    Flask,
    Response,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    options_to_json,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers import bytes_to_base64url, base64url_to_bytes
from webauthn.helpers.structs import (
    AttestationConveyancePreference,
    AuthenticatorAttachment,
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    PublicKeyCredentialType,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

import db

RP_ID = os.environ.get("SHALLOT_RP_ID")  # None => derive from request Host
RP_NAME = os.environ.get("SHALLOT_RP_NAME", "SHALLOT")
PORT = int(os.environ.get("SHALLOT_PORT", "8000"))
ORIGIN = os.environ.get("SHALLOT_ORIGIN")  # None => derive from request Host
SECRET = os.environ.get("SHALLOT_SECRET", "dev-secret-change-me")


def _host() -> str:
    """Bare host (no port) from the incoming request, e.g. 'localhost' / '127.0.0.1'."""
    return request.host.split(":")[0]


def _rp_id() -> str:
    return RP_ID or _host()


def _origin() -> str:
    return ORIGIN or f"{request.scheme}://{request.host}"


log = logging.getLogger(__name__)


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = SECRET
    db.init_db()

    @app.route("/")
    def index():
        return render_template("index.html", user=_current_user(), rp_id=_rp_id())

    @app.route("/register", methods=["GET"])
    def register_get():
        return render_template("register.html", user=_current_user())

    @app.route("/login", methods=["GET"])
    def login_get():
        return render_template("login.html", user=_current_user())

    @app.route("/register/begin", methods=["POST"])
    def register_begin():
        data = request.get_json(force=True, silent=True) or {}
        username = (data.get("username") or "").strip()
        display_name = (data.get("display_name") or username).strip()
        role = data.get("role", "cub")
        attestation_pref = data.get("attestation", "direct")
        if attestation_pref not in ("direct", "none"):
            return jsonify({"error": "invalid attestation preference"}), 400
        if not username:
            return jsonify({"error": "username required"}), 400
        if role not in ("mama_bear", "cub"):
            return jsonify({"error": "invalid role"}), 400
        if db.get_user_by_username(username):
            return jsonify({"error": "username already registered"}), 409

        user_handle = secrets.token_bytes(32)
        existing = []  # first credential for this (new) user
        options = generate_registration_options(
            rp_id=_rp_id(),
            rp_name=RP_NAME,
            user_name=username,
            user_id=user_handle,
            user_display_name=display_name or username,
            attestation=AttestationConveyancePreference.DIRECT
            if attestation_pref == "direct"
            else AttestationConveyancePreference.NONE,
            authenticator_selection=AuthenticatorSelectionCriteria(
                resident_key=ResidentKeyRequirement.PREFERRED,
                user_verification=UserVerificationRequirement.PREFERRED,
                authenticator_attachment=AuthenticatorAttachment.CROSS_PLATFORM,
            ),
            exclude_credentials=existing,
        )
        session["reg_challenge"] = bytes_to_base64url(options.challenge)
        session["reg_user"] = {
            "username": username,
            "display_name": display_name or username,
            "role": role,
            "attestation": attestation_pref,
            "handle": bytes_to_base64url(user_handle),
        }
        return Response(options_to_json(options), mimetype="application/json")

    @app.route("/register/complete", methods=["POST"])
    def register_complete():
        pending = session.get("reg_user")
        challenge_b64 = session.get("reg_challenge")
        if not pending or not challenge_b64:
            return jsonify({"error": "no registration in progress"}), 400

        credential = request.get_json(force=True)
        try:
            verified = verify_registration_response(
                credential=credential,
                expected_challenge=base64url_to_bytes(challenge_b64),
                expected_rp_id=_rp_id(),
                expected_origin=_origin(),
                require_user_verification=False,
            )
        except Exception:
            log.exception("registration verification failed")
            return jsonify({"error": "verification failed"}), 400

        expected_attestation = (pending or {}).get("attestation", "direct")
        if expected_attestation == "direct" and str(verified.fmt).lower() == "none":
            session.pop("reg_challenge", None)
            session.pop("reg_user", None)
            return jsonify({
                "error": "attestation required: authenticator returned none; register a "
                         "FIDO2 device that supports attestation, or use attestation=none "
                         "for software keys"
            }), 400

        user = db.get_user_by_username(pending["username"])
        if not user:
            user = db.create_user(
                pending["username"], pending["display_name"], pending["role"],
                base64url_to_bytes(pending["handle"]),
            )
        db.add_credential(
            user_id=user.id,
            credential_id=verified.credential_id,
            public_key=verified.credential_public_key,
            sign_count=verified.sign_count,
            transports=(credential.get("response", {})
                         .get("transports", []) or []) if isinstance(credential, dict) else [],
            aaguid=verified.aaguid,
            fmt=verified.fmt,
            device_type=verified.credential_device_type,
            backed_up=verified.credential_backed_up,
        )
        session.pop("reg_challenge", None)
        session.pop("reg_user", None)
        session["user_handle"] = user.handle
        return jsonify({
            "status": "ok",
            "username": user.username,
            "role": user.role,
            "credential_id": bytes_to_base64url(verified.credential_id),
            "device_type": str(verified.credential_device_type),
            "backed_up": bool(verified.credential_backed_up),
            "user_verified": bool(verified.user_verified),
            "fmt": str(verified.fmt),
        })

    @app.route("/login/begin", methods=["POST"])
    def login_begin():
        data = request.get_json(force=True, silent=True) or {}
        username = (data.get("username") or "").strip()
        user = db.get_user_by_username(username) if username else None
        if username and not user:
            return jsonify({"error": "unknown user"}), 404

        if user:
            creds = db.get_credentials_for_user(user.id)
            allow = [c.credential_id for c in creds]
        else:
            # usernameless / discoverable flow: allow any credential
            with _conn() as conn:
                rows = conn.execute("SELECT credential_id FROM credentials").fetchall()
            allow = [r["credential_id"] for r in rows]

        allow_credentials = [
            PublicKeyCredentialDescriptor(
                id=base64url_to_bytes(cid), type=PublicKeyCredentialType.PUBLIC_KEY
            )
            for cid in allow
        ]
        options = generate_authentication_options(
            rp_id=_rp_id(),
            allow_credentials=allow_credentials,
            user_verification=UserVerificationRequirement.PREFERRED,
        )
        session["auth_challenge"] = bytes_to_base64url(options.challenge)
        return Response(options_to_json(options), mimetype="application/json")

    @app.route("/login/complete", methods=["POST"])
    def login_complete():
        challenge_b64 = session.get("auth_challenge")
        if not challenge_b64:
            return jsonify({"error": "no login in progress"}), 400

        credential = request.get_json(force=True)
        cid = credential["id"] if isinstance(credential, dict) else None
        stored = db.get_credential_by_id(cid) if cid else None
        if not stored:
            return jsonify({"error": "unknown credential"}), 404

        try:
            verified = verify_authentication_response(
                credential=credential,
                expected_challenge=base64url_to_bytes(challenge_b64),
                expected_rp_id=_rp_id(),
                expected_origin=_origin(),
                credential_public_key=db.public_key_bytes(stored),
                credential_current_sign_count=stored.sign_count,
                require_user_verification=False,
            )
        except Exception:
            log.exception("authentication verification failed")
            return jsonify({"error": "verification failed"}), 400

        db.update_sign_count(stored.credential_id, verified.new_sign_count)
        user = db.get_user_by_handle(_handle_for_credential(stored))
        session.pop("auth_challenge", None)
        if user:
            session["user_handle"] = user.handle
            return jsonify({"status": "ok", "username": user.username, "role": user.role})
        return jsonify({"status": "ok"})

    @app.route("/dashboard")
    def dashboard():
        user = _current_user()
        if not user:
            return redirect(url_for("login_get"))
        creds = db.get_credentials_for_user(user.id)
        return render_template("dashboard.html", user=user, creds=creds)

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("index"))

    return app


def _conn():
    import sqlite3
    conn = sqlite3.connect(db.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _handle_for_credential(stored: db.Credential) -> str:
    with _conn() as conn:
        row = conn.execute(
            "SELECT u.handle FROM users u JOIN credentials c ON c.user_id = u.id WHERE c.id = ?",
            (stored.id,),
        ).fetchone()
    return row["handle"] if row else ""


def _current_user() -> db.User | None:
    handle = session.get("user_handle")
    if not handle:
        return None
    return db.get_user_by_handle(handle)


app = create_app()


if __name__ == "__main__":
    # host="::" binds both IPv4 and IPv6 so "localhost" (::1) reaches the
    # server even when macOS Control Center grabs ports like 5000.
    app.run(host="::", port=PORT, debug=os.environ.get("FLASK_DEBUG", "0") == "1")
