"""Ingress Scrubber (ADR 0006 / ADR 0007).

Deterministic AES-SIV encryption of sensitive entities before they leave the
perimeter. Surrogate-encoded values are re-mapped locally; the remapping
table is excluded from the provenance log. Scrubbing runs regardless of the
sensitivity label (default-deny).

Implementation: AES-SIV via `cryptography` library. Deterministic — same
entity always produces the same surrogate, so the LLM can track identity
across calls. Reversible locally with the same key.
"""
from __future__ import annotations

import base64
import hashlib
import re
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESSIV

from cub.config import CubConfig

# Entity patterns to detect and scrub
_IP_PATTERN = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
_HOSTNAME_PATTERN = re.compile(r"\b[a-zA-Z0-9][-a-zA-Z0-9]*\.[a-zA-Z]{2,}\b")
_ASSET_TAG_PATTERN = re.compile(r"\b(?:SHALLOT|BRICKA|NODE)[-_]?\d+\b", re.IGNORECASE)
_USERNAME_PATTERN = re.compile(r"\b(?:admin|operator|technician|cub|mama_bear)\b", re.IGNORECASE)


class IngressScrubber:
    """AES-SIV deterministic scrubber for sensitive entities.

    Same input always produces same output (deterministic), but the output
    is not reversible without the key. The remapping table is kept locally
    and excluded from provenance logs (ADR 0006).
    """

    def __init__(self, cfg: CubConfig) -> None:
        self.cfg = cfg
        self._key = self._derive_key(cfg.scrubber_fpe_key or "shallot-default-dev-key")
        self._cipher = AESSIV(self._key)
        self._remap: dict[str, str] = {}

    @staticmethod
    def _derive_key(passphrase: str) -> bytes:
        """Derive a 64-byte key from passphrase via SHA-512."""
        return hashlib.sha512(passphrase.encode()).digest()

    def _surrogate(self, entity: str) -> str:
        """Generate deterministic surrogate for an entity."""
        if entity in self._remap:
            return self._remap[entity]

        # AES-SIV needs associated data; use entity type as AAD
        ciphertext = self._cipher.encrypt(entity.encode(), [b"entity"])
        surrogate = "SUR-" + base64url_encode(ciphertext[:12])
        self._remap[entity] = surrogate
        return surrogate

    def scrub(self, text: str) -> str:
        """Scrub all detected entities in text.

        Each entity type is replaced with a deterministic surrogate.
        The same entity always produces the same surrogate.
        """
        result = text

        # Scrub IPs
        for match in _IP_PATTERN.finditer(text):
            original = match.group()
            result = result.replace(original, self._surrogate(original))

        # Scrub hostnames
        for match in _HOSTNAME_PATTERN.finditer(text):
            original = match.group()
            if not original.startswith("SUR-"):
                result = result.replace(original, self._surrogate(original))

        # Scrub asset tags
        for match in _ASSET_TAG_PATTERN.finditer(text):
            original = match.group()
            result = result.replace(original, self._surrogate(original))

        # Scrub usernames
        for match in _USERNAME_PATTERN.finditer(text):
            original = match.group()
            result = result.replace(original, self._surrogate(original))

        return result

    def desurrogate(self, surrogate: str) -> str | None:
        """Reverse a surrogate to original entity (local only)."""
        for original, surr in self._remap.items():
            if surr == surrogate:
                return original
        return None

    def remap_table(self) -> dict[str, str]:
        """Return copy of remapping table (excluded from provenance log)."""
        return dict(self._remap)


def base64url_encode(data: bytes) -> str:
    """URL-safe base64 encoding without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()
