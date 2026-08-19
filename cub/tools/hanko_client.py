"""Hanko FIDO2/WebAuthn backend (ADR 0007).

Wraps Hanko's Flow API for WebAuthn registration and authentication.
Replaces the custom Flask-RP in demo/app.py with a production-ready
FIDO2-certified platform.

Requires:
  HANKO_API_URL — Hanko backend URL (e.g. http://localhost:8000)
  HANKO_TENANT_ID — Hanko tenant ID (for cloud: <tenant>.hanko.io)

Falls back to MockFidoBackend when Hanko is unavailable (offline/labbet).
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass

import requests


HANKO_API_URL = os.environ.get("HANKO_API_URL", "")
HANKO_TENANT_ID = os.environ.get("HANKO_TENANT_ID", "")
HANKO_API_KEY = os.environ.get("HANKO_API_KEY", "")  # optional, for admin ops


class HankoClient:
    """Thin wrapper around Hanko Flow API for WebAuthn operations."""

    def __init__(self) -> None:
        self._base_url = HANKO_API_URL.rstrip("/")
        self._tenant_id = HANKO_TENANT_ID
        self._session = requests.Session()
        self._session.headers["Content-Type"] = "application/json"

        if HANKO_API_KEY:
            self._session.headers["Authorization"] = f"Bearer {HANKO_API_KEY}"

        # For cloud Hanko, base URL is https://<tenant>.hanko.io
        if self._tenant_id and not self._base_url:
            self._base_url = f"https://{self._tenant_id}.hanko.io"

    @property
    def available(self) -> bool:
        return bool(self._base_url)

    def register_begin(self, username: str, display_name: str = "") -> dict:
        """Initialize a registration flow with Hanko."""
        if not self.available:
            return {"error": "hanko not configured"}

        try:
            # Step 1: Initialize registration flow
            resp = self._session.post(
                f"{self._base_url}/registration",
                json={
                    "input_data": {
                        "username": username,
                    }
                },
                timeout=10,
            )
            resp.raise_for_status()
            flow = resp.json()

            # Step 2: Register client capabilities (WebAuthn available)
            actions = flow.get("actions", {})
            if "register_client_capabilities" in actions:
                cap_href = actions["register_client_capabilities"]["href"]
                resp = self._session.post(
                    f"{self._base_url}{cap_href}",
                    json={
                        "input_data": {
                            "webauthn_available": True,
                            "webauthn_conditional_mediation_available": False,
                            "webauthn_platform_authenticator_available": False,
                        }
                    },
                    timeout=10,
                )
                resp.raise_for_status()
                flow = resp.json()

            # Step 3: Get passkey creation options
            actions = flow.get("actions", {})
            if "webauthn_generate_creation_options" in actions:
                opt_href = actions["webauthn_generate_creation_options"]["href"]
                resp = self._session.post(
                    f"{self._base_url}{opt_href}",
                    timeout=10,
                )
                resp.raise_for_status()
                flow = resp.json()

            return {
                "flow_id": flow.get("id"),
                "csrf_token": flow.get("csrf_token"),
                "creation_options": flow.get("payload", {}).get("creation_options"),
                "state": flow.get("name"),
            }

        except Exception as exc:
            return {"error": str(exc)}

    def register_complete(self, flow_id: str, csrf_token: str, public_key: dict) -> dict:
        """Complete registration by verifying the attestation response."""
        if not self.available:
            return {"error": "hanko not configured"}

        try:
            resp = self._session.post(
                f"{self._base_url}/registration?action=webauthn_verify_attestation_response@{flow_id}",
                json={
                    "input_data": {"public_key": public_key},
                    "csrf_token": csrf_token,
                },
                timeout=10,
            )
            resp.raise_for_status()
            flow = resp.json()

            if flow.get("name") == "success":
                user = flow.get("payload", {}).get("user", {})
                return {
                    "status": "ok",
                    "user_id": user.get("user_id"),
                    "username": username_from_claims(flow),
                }
            return {"status": "pending", "state": flow.get("name")}

        except Exception as exc:
            return {"error": str(exc)}

    def login_begin(self, username: str = "") -> dict:
        """Initialize a login flow with Hanko."""
        if not self.available:
            return {"error": "hanko not configured"}

        try:
            # Initialize login flow
            payload = {}
            if username:
                payload["input_data"] = {"username": username}

            resp = self._session.post(
                f"{self._base_url}/login",
                json=payload,
                timeout=10,
            )
            resp.raise_for_status()
            flow = resp.json()

            # Get WebAuthn assertion options
            actions = flow.get("actions", {})
            if "webauthn_generate_assertion_options" in actions:
                opt_href = actions["webauthn_generate_assertion_options"]["href"]
                resp = self._session.post(
                    f"{self._base_url}{opt_href}",
                    timeout=10,
                )
                resp.raise_for_status()
                flow = resp.json()

            return {
                "flow_id": flow.get("id"),
                "csrf_token": flow.get("csrf_token"),
                "assertion_options": flow.get("payload", {}).get("assertion_options"),
                "state": flow.get("name"),
            }

        except Exception as exc:
            return {"error": str(exc)}

    def login_complete(self, flow_id: str, csrf_token: str, public_key: dict) -> dict:
        """Complete login by verifying the assertion response."""
        if not self.available:
            return {"error": "hanko not configured"}

        try:
            resp = self._session.post(
                f"{self._base_url}/login?action=webauthn_verify_assertion_response@{flow_id}",
                json={
                    "input_data": {"public_key": public_key},
                    "csrf_token": csrf_token,
                },
                timeout=10,
            )
            resp.raise_for_status()
            flow = resp.json()

            if flow.get("name") == "success":
                user = flow.get("payload", {}).get("user", {})
                return {
                    "status": "ok",
                    "user_id": user.get("user_id"),
                    "username": username_from_claims(flow),
                    "session_token": resp.headers.get("X-Auth-Token"),
                }
            return {"status": "pending", "state": flow.get("name")}

        except Exception as exc:
            return {"error": str(exc)}

    def healthcheck(self) -> dict:
        """Check Hanko API connectivity."""
        if not self.available:
            return {"status": "offline", "fallback": "mock"}
        try:
            resp = self._session.get(f"{self._base_url}/", timeout=5)
            resp.raise_for_status()
            return {"status": "online", "hanko_version": resp.headers.get("X-Hanko-Version", "unknown")}
        except Exception as exc:
            return {"status": "error", "error": str(exc), "fallback": "mock"}


def username_from_claims(flow: dict) -> str:
    """Extract username from Hanko flow success payload."""
    user = flow.get("payload", {}).get("user", {})
    emails = user.get("emails", [])
    if emails:
        return emails[0].get("address", "")
    return user.get("user_id", "unknown")


# --- Agent tool wrapper (for cub-agent FIDO CTAP tool) ---

@dataclass
class HankoFidoBackend:
    """Hanko-backed FIDO CTAP backend for cub-agent tool."""

    rp_id: str = "shallot.local"
    _client: HankoClient | None = None

    def __post_init__(self) -> None:
        if self._client is None:
            self._client = HankoClient()

    def register(self, username: str = "operator", operator_confirmed: bool = False) -> dict:
        """Register a new passkey via Hanko."""
        if not operator_confirmed:
            return {"ok": False, "reason": "register requires operator confirmation (HITL)"}

        result = self._client.register_begin(username)
        if "error" in result:
            return {"ok": False, "error": result["error"]}

        return {
            "ok": True,
            "result": "registration_started",
            "flow_id": result.get("flow_id"),
            "csrf_token": result.get("csrf_token"),
            "creation_options": result.get("creation_options"),
        }

    def assert_credential(self, username: str = "operator") -> dict:
        """Authenticate via passkey through Hanko."""
        result = self._client.login_begin(username)
        if "error" in result:
            return {"ok": False, "error": result["error"]}

        return {
            "ok": True,
            "result": "authentication_started",
            "flow_id": result.get("flow_id"),
            "csrf_token": result.get("csrf_token"),
            "assertion_options": result.get("assertion_options"),
        }


def demo() -> None:
    """Demo: check Hanko connectivity and show fallback behavior."""
    client = HankoClient()
    print("healthcheck:", client.healthcheck())

    backend = HankoFidoBackend()
    print("register (no HITL):", backend.register())
    print("register (HITL):", backend.register(operator_confirmed=True))
    print("assert:", backend.assert_credential())


if __name__ == "__main__":
    demo()
