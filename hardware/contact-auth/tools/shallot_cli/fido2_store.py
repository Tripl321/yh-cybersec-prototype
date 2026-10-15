"""Simulerad lokal datalagring för FIDO2-spåret (proof of concept).

Sparar endast sanerad credential-metadata. Lagring tillåts enbart under
SHALLOT:s lokala datakatalog eller en isolerad systemtempkatalog för tester.
Privata nycklar och hemligt råmaterial avvisas.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

STORE_ENV = "SHALLOT_FIDO2_STORE"
SHALLOT_DATA_ROOT = Path.home() / ".local" / "share" / "shallot"
DEFAULT_ROOT = SHALLOT_DATA_ROOT / "fido2-test"
TEMP_ROOT = Path(tempfile.gettempdir()).resolve()

CREDENTIALS_FILE = "credentials.json"
AUDIT_FILE = "audit.jsonl"
ALLOWED_FILES = (CREDENTIALS_FILE, AUDIT_FILE)

STATUS_ACTIVE = "active"
STATUS_REVOKED = "revoked"

FORBIDDEN_FIELDS = (
    "private_key",
    "secret",
    "seed",
    "attestation_raw",
    "cbor",
    "authenticator_data_raw",
)


def _is_within(path: Path, base: Path) -> bool:
    return path == base or base in path.parents


def _validated_root(root: Path | None = None) -> Path:
    raw = Path(root) if root is not None else Path(os.environ.get(STORE_ENV, DEFAULT_ROOT))
    try:
        candidate = raw.expanduser().resolve(strict=False)
        data_root = SHALLOT_DATA_ROOT.expanduser().resolve(strict=False)
    except OSError as exc:
        raise ValueError("kan inte normalisera lagringssökvägen") from exc

    allowed_data = _is_within(candidate, data_root)
    allowed_test = candidate != TEMP_ROOT and _is_within(candidate, TEMP_ROOT)
    if not (allowed_data or allowed_test):
        raise ValueError("lagringssökvägen ligger utanför tillåtet SHALLOT- eller testområde")
    return candidate


def _safe_path(root: Path | None, filename: str) -> tuple[Path, Path]:
    if filename not in ALLOWED_FILES:
        raise ValueError("otillåtet lagringsfilnamn")
    base = _validated_root(root)
    path = (base / filename).resolve(strict=False)
    if path.parent != base:
        raise ValueError("lagringssökvägen lämnar vald rot")
    return base, path


def _prepare_root(base: Path) -> None:
    try:
        base.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(base, 0o700)
    except OSError as exc:
        raise RuntimeError("kan inte skapa säker lagringskatalog") from exc


def _open_flags(*, append: bool = False) -> int:
    flags = os.O_WRONLY | os.O_CREAT
    flags |= os.O_APPEND if append else os.O_TRUNC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    return flags


def store_root() -> Path:
    return _validated_root()


def utcnow() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read_json(root: Path | None, filename: str, default):
    _, path = _safe_path(root, filename)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default
    except (OSError, ValueError) as exc:
        raise RuntimeError("kan inte läsa säker lokal lagring") from exc


def load_credentials(root: Path | None = None) -> dict:
    """Returnerar {credential_id: metadata}. Tom dict om ingen lagring finns."""
    data = _read_json(root, CREDENTIALS_FILE, {})
    if not isinstance(data, dict):
        raise RuntimeError("credential-lagringen är korrupt (väntar objekt)")
    return data


def _write_json(root: Path | None, filename: str, data: dict) -> None:
    base, path = _safe_path(root, filename)
    try:
        _prepare_root(base)
        descriptor = os.open(path, _open_flags(), 0o600)
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(data, indent=2) + "\n")
    except OSError as exc:
        raise RuntimeError("kan inte skriva säker lokal lagring") from exc


def save_credential(metadata: dict, root: Path | None = None) -> None:
    """Spara credential-metadata. Avvisar förbjudna fält och dubbletter."""
    for field in FORBIDDEN_FIELDS:
        if field in metadata:
            raise ValueError("förbjudet fält i metadata: %s (nycklar sparas aldrig)" % field)
    for required in ("credential_id", "user_id", "created", "status", "policy"):
        if required not in metadata:
            raise ValueError("saknar obligatoriskt fält: %s" % required)
    creds = load_credentials(root)
    if metadata["credential_id"] in creds:
        raise ValueError("credential-ID finns redan: registrera inte om")
    creds[metadata["credential_id"]] = metadata
    _write_json(root, CREDENTIALS_FILE, creds)


def set_status(credential_id: str, status: str, root: Path | None = None) -> dict:
    """Byt status (active|revoked). Returnerar uppdaterad metadata."""
    if status not in (STATUS_ACTIVE, STATUS_REVOKED):
        raise ValueError("okänd status: %r" % (status,))
    creds = load_credentials(root)
    if credential_id not in creds:
        raise KeyError("okänd credential: %s" % credential_id)
    creds[credential_id]["status"] = status
    _write_json(root, CREDENTIALS_FILE, creds)
    return creds[credential_id]


def update_sign_count(credential_id: str, sign_count: int, root: Path | None = None) -> dict:
    """Spara ny sign-counter (HW-klondetektion). Returnerar uppdaterad metadata."""
    if not isinstance(sign_count, int) or sign_count < 0:
        raise ValueError("ogiltig sign_count: %r" % (sign_count,))
    creds = load_credentials(root)
    if credential_id not in creds:
        raise KeyError("okänd credential: %s" % credential_id)
    creds[credential_id]["sign_count"] = sign_count
    _write_json(root, CREDENTIALS_FILE, creds)
    return creds[credential_id]


def update_policy(credential_id: str, policy_updates: dict, root: Path | None = None) -> dict:
    """Slå samman policyfält. Returnerar uppdaterad metadata."""
    if not isinstance(policy_updates, dict) or not policy_updates:
        raise ValueError("policy_updates måste vara en icke-tom dict")
    creds = load_credentials(root)
    if credential_id not in creds:
        raise KeyError("okänd credential: %s" % credential_id)
    policy = creds[credential_id].get("policy", {})
    if not isinstance(policy, dict):
        raise RuntimeError("korrupt policy för credential: %s" % credential_id)
    policy.update(policy_updates)
    creds[credential_id]["policy"] = policy
    _write_json(root, CREDENTIALS_FILE, creds)
    return creds[credential_id]


def audit(action: str, details: dict, root: Path | None = None) -> None:
    """Lägg till en auditpost. Aldrig hemligheter i details."""
    for field in FORBIDDEN_FIELDS:
        if field in details:
            raise ValueError("förbjudet fält i auditpost: %s" % field)
    base, path = _safe_path(root, AUDIT_FILE)
    line = json.dumps({"ts": utcnow(), "action": action, "details": details})
    try:
        _prepare_root(base)
        descriptor = os.open(path, _open_flags(append=True), 0o600)
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "a", encoding="utf-8") as handle:
            handle.write(line + "\n")
    except OSError as exc:
        raise RuntimeError("kan inte skriva auditlogg") from exc


def read_audit(root: Path | None = None, limit: int = 50) -> list:
    """Läs de senaste auditposterna (nyast sist)."""
    _, path = _safe_path(root, AUDIT_FILE)
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return []
    except OSError as exc:
        raise RuntimeError("kan inte läsa auditlogg") from exc
    output = []
    for line in lines[-limit:]:
        try:
            output.append(json.loads(line))
        except ValueError:
            continue
    return output
