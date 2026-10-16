"""Ingress Scrubber (ADR 0006 / ADR 0007).

Deterministic AES-SIV encryption of sensitive entities before they leave the
perimeter. Surrogate-encoded values are re-mapped locally; the remapping table
is excluded from the provenance log. Scrubbing runs regardless of sensitivity.

Configured passphrases are converted to 64-byte AES-SIV keys with scrypt. When
no passphrase is configured, a random process-local key is generated. That
preserves scrubbing and in-process determinism without relying on a shared
development key; surrogates intentionally change after restart.
"""
from __future__ import annotations

import base64
import re
import secrets

from cryptography.hazmat.primitives.ciphers.aead import AESSIV
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

from cub.config import CubConfig

_IP_PATTERN = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
_HOSTNAME_PATTERN = re.compile(r"\b[a-zA-Z0-9][-a-zA-Z0-9]*\.[a-zA-Z]{2,}\b")
_ASSET_TAG_PATTERN = re.compile(r"\b(?:SHALLOT|BRICKA|NODE)[-_]?\d+\b", re.IGNORECASE)
_USERNAME_PATTERN = re.compile(
    r"\b(?:admin|operator|technician|cub|mama_bear)\b", re.IGNORECASE
)

_KDF_SALT = b"SHALLOT-Cub-Scrubber-AES-SIV-v1"
_MIN_PASSPHRASE_LENGTH = 16


class IngressScrubber:
    """AES-SIV deterministic scrubber for sensitive entities.

    A configured passphrase provides stable surrogates across restarts. Without
    one, a random process-local key keeps scrubbing fail-safe while avoiding a
    repository-wide default secret.
    """

    def __init__(self, cfg: CubConfig) -> None:
        self.cfg = cfg
        if cfg.scrubber_fpe_key:
            self._key = self._derive_key(cfg.scrubber_fpe_key)
        else:
            self._key = secrets.token_bytes(64)
        self._cipher = AESSIV(self._key)
        self._remap: dict[str, str] = {}

    @staticmethod
    def _derive_key(passphrase: str) -> bytes:
        """Derive a 64-byte AES-SIV key with a memory-hard password KDF."""
        if len(passphrase) < _MIN_PASSPHRASE_LENGTH:
            raise ValueError("CUB_SCRUBBER_KEY must contain at least 16 characters")
        kdf = Scrypt(salt=_KDF_SALT, length=64, n=2**15, r=8, p=1)
        return kdf.derive(passphrase.encode("utf-8"))

    def _surrogate(self, entity: str) -> str:
        """Generate deterministic surrogate for an entity."""
        if entity in self._remap:
            return self._remap[entity]

        ciphertext = self._cipher.encrypt(entity.encode(), [b"entity"])
        surrogate = "SUR-" + base64url_encode(ciphertext[:12])
        self._remap[entity] = surrogate
        return surrogate

    def scrub(self, text: str) -> str:
        """Scrub all detected entities in text."""
        result = text

        for match in _IP_PATTERN.finditer(text):
            original = match.group()
            result = result.replace(original, self._surrogate(original))

        for match in _HOSTNAME_PATTERN.finditer(text):
            original = match.group()
            if not original.startswith("SUR-"):
                result = result.replace(original, self._surrogate(original))

        for match in _ASSET_TAG_PATTERN.finditer(text):
            original = match.group()
            result = result.replace(original, self._surrogate(original))

        for match in _USERNAME_PATTERN.finditer(text):
            original = match.group()
            result = result.replace(original, self._surrogate(original))

        return result

    def desurrogate(self, surrogate: str) -> str | None:
        """Reverse a surrogate to original entity in the current process."""
        for original, mapped in self._remap.items():
            if mapped == surrogate:
                return original
        return None

    def remap_table(self) -> dict[str, str]:
        """Return copy of remapping table (excluded from provenance log)."""
        return dict(self._remap)


def base64url_encode(data: bytes) -> str:
    """URL-safe base64 encoding without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()
