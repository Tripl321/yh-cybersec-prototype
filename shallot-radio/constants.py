"""SHALLOT radio protocol constants.

All LoRa communication uses raw bytes. No JSON. No text parsing.
Byte order: little-endian (<) for cross-board consistency.
"""

import struct

# ── Message types ──────────────────────────────────────────────
MSG_BEACON = 0x01
MSG_AUTH = 0x02

# ── Beacon payload: 13 bytes ──────────────────────────────────
# <B4sII
#   B  = msg_type      (1 byte)   — always 0x01
#   4s = node_id       (4 bytes)  — e.g. b'FN01'
#   I  = timestamp     (4 bytes)  — epoch seconds
#   I  = nonce         (4 bytes)  — random per beacon
BEACON_FMT = "<B4sII"
BEACON_SIZE = struct.calcsize(BEACON_FMT)  # 13

# ── Auth Request payload: 45 bytes ────────────────────────────
# <B4sII32s
#   B   = msg_type     (1 byte)   — always 0x02
#   4s  = badge_id     (4 bytes)  — e.g. b'PAW1'
#   I   = nonce        (4 bytes)  — same nonce as beacon
#   I   = day          (4 bytes)  — current day for epoch check
#   32s = signature    (32 bytes) — HMAC-SHA256 over (badge_id + nonce + day)
AUTH_FMT = "<B4sII32s"
AUTH_SIZE = struct.calcsize(AUTH_FMT)  # 45

# ── Timing (ms) ────────────────────────────────────────────────
BEACON_INTERVAL_MS = 1000
HEARTBEAT_TIMEOUT_MS = 5000
RSSI_THRESHOLD_DBM = -70

# ── LoRa radio config ──────────────────────────────────────────
LORA_FREQUENCY_MHZ = 868.0
LORA_TX_POWER_DBM = 14
LORA_SPREAD_FACTOR = 7
LORA_BANDWIDTH_HZ = 125000
LORA_CODING_RATE = 5

# ── Helpers ────────────────────────────────────────────────────

def pack_beacon(node_id: bytes, timestamp: int, nonce: int) -> bytes:
    """Encode a beacon frame. node_id must be exactly 4 bytes."""
    return struct.pack(BEACON_FMT, MSG_BEACON, node_id, timestamp, nonce)


def unpack_beacon(data: bytes) -> dict:
    """Decode a beacon frame. Returns dict with node_id, timestamp, nonce."""
    if len(data) != BEACON_SIZE:
        raise ValueError(f"beacon: expected {BEACON_SIZE} bytes, got {len(data)}")
    _type, node_id, timestamp, nonce = struct.unpack(BEACON_FMT, data)
    return {"node_id": node_id, "timestamp": timestamp, "nonce": nonce}


def pack_auth(badge_id: bytes, nonce: int, day: int, signature: bytes) -> bytes:
    """Encode an auth request frame. signature must be exactly 32 bytes.

    Signature covers: badge_id + nonce + day (12 bytes).
    """
    return struct.pack(AUTH_FMT, MSG_AUTH, badge_id, nonce, day, signature)


def unpack_auth(data: bytes) -> dict:
    """Decode an auth request frame.

    Returns dict with badge_id, nonce, day, signature.
    """
    if len(data) != AUTH_SIZE:
        raise ValueError(f"auth: expected {AUTH_SIZE} bytes, got {len(data)}")
    _type, badge_id, nonce, day, signature = struct.unpack(AUTH_FMT, data)
    return {"badge_id": badge_id, "nonce": nonce, "day": day, "signature": signature}
