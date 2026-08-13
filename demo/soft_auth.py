"""Software FIDO2 authenticator for end-to-end testing of the SHALLOT RP.

Generates valid WebAuthn registration/authentication responses (EC P-256,
none attestation) using only `cryptography` + `cbor2`, so the relying-party
verification can be exercised headlessly — no browser or hardware key.
"""
from __future__ import annotations

import base64
import hashlib
import struct
from dataclasses import dataclass, field

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from webauthn.helpers import bytes_to_base64url, base64url_to_bytes

import cbor2


def _b64url(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode("ascii")


@dataclass
class SoftAuthenticator:
    rp_id: str = "localhost"
    origin: str = "http://localhost:8000"
    credential_id: bytes = field(default_factory=lambda: b"soft-cred-" + bytes(8))
    _private_key: ec.EllipticCurvePrivateKey = field(
        default_factory=lambda: ec.generate_private_key(ec.SECP256R1())
    )
    sign_count: int = 0

    def _cose_public_key(self) -> bytes:
        pub = self._private_key.public_key()
        nums = pub.public_numbers()
        x = nums.x.to_bytes(32, "big")
        y = nums.y.to_bytes(32, "big")
        return cbor2.dumps({1: 2, 3: -7, -1: 1, -2: x, -3: y})

    def _sign(self, data: bytes) -> bytes:
        # cryptography's EC verify (used by py-webauthn) expects DER-encoded
        # ECDSA signatures, not the raw R||S CTAP format.
        return self._private_key.sign(data, ec.ECDSA(hashes.SHA256()))
        rp_hash = hashlib.sha256(self.rp_id.encode()).digest()
        flags = 0x01  # user present
        if include_attested:
            flags |= 0x40  # attested credential data included
        body = rp_hash + struct.pack(">B", flags) + struct.pack(">I", sign_count)
        if include_attested:
            aaguid = b"\x00" * 16
            cid = self.credential_id
            body += aaguid + struct.pack(">H", len(cid)) + cid + self._cose_public_key()
        return body

    def _client_data(self, typ: str, challenge_b64: str) -> bytes:
        import json
        return json.dumps(
            {"type": typ, "challenge": challenge_b64, "origin": self.origin},
            separators=(",", ":"),
        ).encode()

    def _auth_data(self, include_attested: bool, sign_count: int) -> bytes:
        rp_hash = hashlib.sha256(self.rp_id.encode()).digest()
        flags = 0x01  # user present
        if include_attested:
            flags |= 0x40  # attested credential data included
        body = rp_hash + struct.pack(">B", flags) + struct.pack(">I", sign_count)
        if include_attested:
            aaguid = b"\x00" * 16
            cid = self.credential_id
            body += aaguid + struct.pack(">H", len(cid)) + cid + self._cose_public_key()
        return body

    def register(self, options: dict) -> dict:
        challenge = options["challenge"]
        client_data = self._client_data("webauthn.create", challenge)
        auth_data = self._auth_data(include_attested=True, sign_count=self.sign_count)
        to_sign = auth_data + hashlib.sha256(client_data).digest()
        sig = self._sign(to_sign)
        attestation_object = cbor2.dumps(
            {"fmt": "none", "authData": auth_data, "attStmt": {}}
        )
        return {
            "id": _b64url(self.credential_id),
            "rawId": _b64url(self.credential_id),
            "type": "public-key",
            "response": {
                "clientDataJSON": _b64url(client_data),
                "attestationObject": _b64url(attestation_object),
                "transports": ["internal", "hybrid"],
            },
        }

    def authenticate(self, options: dict, user_handle: bytes | None = None) -> dict:
        challenge = options["challenge"]
        client_data = self._client_data("webauthn.get", challenge)
        self.sign_count += 1
        auth_data = self._auth_data(include_attested=False, sign_count=self.sign_count)
        to_sign = auth_data + hashlib.sha256(client_data).digest()
        sig = self._sign(to_sign)
        return {
            "id": _b64url(self.credential_id),
            "rawId": _b64url(self.credential_id),
            "type": "public-key",
            "response": {
                "clientDataJSON": _b64url(client_data),
                "authenticatorData": _b64url(auth_data),
                "signature": _b64url(sig),
                "userHandle": _b64url(user_handle) if user_handle else None,
            },
        }
