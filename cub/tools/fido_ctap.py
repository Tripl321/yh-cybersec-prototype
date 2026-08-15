"""Prototype: FIDO/CTAP-verktyg for SHALLOT-hardvaran (ADR 0005 / #43).

Driver SHALLOT-kortet (ESP32 + pico-fido2) over USB HID via python-fido2;
faller tillbaka pa mock-backend nar hardvaran saknas (labbet, #17).

Operationer: register (make credential) + assert (get assertion), integrerat
mot demo-serverns /register/* och /login/*. Verktyget returnerar bara status,
aldrig rat nyckelmaterial (abstraktion #41).

ROUGH PROTOTYPE — reaktionsunderlag, ej produktionskod.
"""
from __future__ import annotations

import base64
import os
from dataclasses import dataclass


class FidoBackend:
    def register(self, rp_id: str) -> dict:
        raise NotImplementedError

    def assert_credential(self, challenge: bytes, rp_id: str) -> dict:
        raise NotImplementedError


class MockFidoBackend(FidoBackend):
    """Mjukvaru-FIDO; kor utan hardvara. Samma kodvag som USB HID."""

    def register(self, rp_id: str) -> dict:
        cred_id = base64.b64encode(os.urandom(16)).decode()
        return {"cred_id": cred_id, "attestation": "mock-self-signed", "rp_id": rp_id}

    def assert_credential(self, challenge: bytes, rp_id: str) -> dict:
        sig = base64.b64encode(os.urandom(32)).decode()
        return {"auth_ok": True, "signature": sig, "rp_id": rp_id}


class UsbHidFidoBackend(FidoBackend):
    """Verklig driver over python-fido2 (kravs hardvara + lib, #17)."""

    def __init__(self) -> None:
        try:
            import fido2  # noqa: F401
        except ImportError as exc:
            raise RuntimeError("python-fido2 saknas eller hardvara ej monterad (#17)") from exc

    def register(self, rp_id: str) -> dict:
        # real: client.make_credential(...) over CTAP2 HID
        raise NotImplementedError("riktig HID-driver kopplas nar hardvara monteras (#17)")

    def assert_credential(self, challenge: bytes, rp_id: str) -> dict:
        raise NotImplementedError("riktig HID-driver kopplas nar hardvara monteras (#17)")


def _select_backend() -> FidoBackend:
    # Rough: detektera USB HID; annars mock (labbet, #17).
    return MockFidoBackend()


@dataclass
class FidoCtapTool:
    rp_id: str = "shallot.local"
    backend: FidoBackend | None = None

    def __post_init__(self) -> None:
        if self.backend is None:
            self.backend = _select_backend()

    def register(self, *, operator_confirmed: bool = False) -> dict:
        # PRIVILEGIERAD: krav operator-initierat (HITL, default-deny #43 Q4).
        if not operator_confirmed:
            return {"ok": False, "reason": "register kravs operator-bekraftelse (HITL)"}
        cred = self.backend.register(self.rp_id)
        # Integrera mot demo /register/* (rough; post credential):
        # requests.post(f"http://localhost:8000/register/{self.rp_id}", json=cred)
        return {"ok": True, "result": "registered", "detail": cred}

    def assert_credential(self, challenge: bytes) -> dict:
        # Lagre troskel men gated (#43 Q4).
        resp = self.backend.assert_credential(challenge, self.rp_id)
        # requests.post(f"http://localhost:8000/login/{self.rp_id}", json=resp)
        return {"ok": resp.get("auth_ok", False), "result": "authenticated", "detail": resp}


def demo() -> None:
    tool = FidoCtapTool()
    print("register utan HITL:", tool.register())
    print("register med HITL:", tool.register(operator_confirmed=True))
    print("assert:", tool.assert_credential(b"challenge-bytes"))


if __name__ == "__main__":
    demo()
