"""Serial command parser for ENROLL/REVOKE provisioning.

Parses JSON lines from USB-serial (Mama Bear → Field Node).
Only active when provisioning GPIO is LOW.
"""

import json
from storage import Storage, MAX_ENROLLED


def parse_command(line: str) -> dict | None:
    """Parse a JSON command line from Mama Bear.

    Args:
        line: Raw string from serial (e.g. '{"cmd": "ENROLL", ...}').

    Returns:
        Parsed dict with "cmd" field, or None if invalid.
    """
    line = line.strip()
    if not line:
        return None

    try:
        data = json.loads(line)
    except json.JSONDecodeError:
        return None

    if "cmd" not in data:
        return None

    cmd = data["cmd"]

    if cmd == "ENROLL":
        if "badge_id" not in data or "pubkey" not in data:
            return None
        return data

    if cmd == "REVOKE":
        if "badge_id" not in data:
            return None
        return data

    return None


def handle_enroll(cmd: dict, store: Storage) -> str:
    """Handle an ENROLL command.

    Args:
        cmd: Parsed command dict with "badge_id" and "pubkey".
        store: Storage instance for persistence.

    Returns:
        "OK" on success, "ERROR <reason>" on failure.
    """
    badge_id = cmd["badge_id"]
    pubkey = cmd["pubkey"]

    enrolled = store.load_enrolled()

    if len(enrolled) >= MAX_ENROLLED and badge_id not in enrolled:
        return f"ERROR max capacity ({MAX_ENROLLED}) reached"

    enrolled[badge_id] = {
        "pubkey": pubkey,
        "epoch_secret": "",
        "valid_until": 0,
    }
    store.save_enrolled(enrolled)
    return "OK"


def handle_revoke(cmd: dict, store: Storage) -> str:
    """Handle a REVOKE command.

    Args:
        cmd: Parsed command dict with "badge_id".
        store: Storage instance for persistence.

    Returns:
        Always "OK" (idempotent).
    """
    badge_id = cmd["badge_id"]

    enrolled = store.load_enrolled()
    enrolled.pop(badge_id, None)
    store.save_enrolled(enrolled)
    return "OK"
