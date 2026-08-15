"""FIDO2 / CTAP 2.2 tool stub (ticket #43)."""
from __future__ import annotations


def check_presence(credential_id: str) -> dict:
    # TODO (#43): query SHALLOT / FIDO2 authenticator state.
    raise NotImplementedError
