"""Unit tests for SHALLOT radio protocol encoding/decoding.

Run with: python -m pytest tests/test_radio.py
No hardware required — tests struct.pack/unpack and state machine logic only.
"""

import struct
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from constants import (
    MSG_BEACON, MSG_AUTH,
    BEACON_FMT, BEACON_SIZE,
    AUTH_FMT, AUTH_SIZE,
    pack_beacon, unpack_beacon,
    pack_auth, unpack_auth,
)


# ── Beacon encoding ────────────────────────────────────────────

class TestBeacon:
    def test_pack_size(self):
        packet = pack_beacon(b"FN01", 1724058000, 0xDEADBEEF)
        assert len(packet) == BEACON_SIZE == 13

    def test_pack_format(self):
        packet = pack_beacon(b"FN01", 1724058000, 42)
        assert packet[0] == MSG_BEACON
        assert packet[1:5] == b"FN01"
        ts_bytes = struct.unpack_from("<I", packet, 5)[0]
        assert ts_bytes == 1724058000
        nonce_bytes = struct.unpack_from("<I", packet, 9)[0]
        assert nonce_bytes == 42

    def test_roundtrip(self):
        node_id = b"FN01"
        timestamp = 1724058000
        nonce = 12345678
        packet = pack_beacon(node_id, timestamp, nonce)
        data = unpack_beacon(packet)
        assert data["node_id"] == node_id
        assert data["timestamp"] == timestamp
        assert data["nonce"] == nonce

    def test_different_node_ids(self):
        for nid in [b"FN01", b"FN02", b"PLC1", b"TEST"]:
            packet = pack_beacon(nid, 1000, 1)
            data = unpack_beacon(packet)
            assert data["node_id"] == nid

    def test_zero_nonce(self):
        packet = pack_beacon(b"FN01", 1000, 0)
        data = unpack_beacon(packet)
        assert data["nonce"] == 0

    def test_max_nonce(self):
        packet = pack_beacon(b"FN01", 1000, 0xFFFFFFFF)
        data = unpack_beacon(packet)
        assert data["nonce"] == 0xFFFFFFFF


# ── Auth encoding ──────────────────────────────────────────────

class TestAuth:
    def test_pack_size(self):
        sig = bytes(range(32))
        packet = pack_auth(b"PAW1", 42, 1, sig)
        assert len(packet) == AUTH_SIZE == 45

    def test_pack_format(self):
        sig = bytes(range(32))
        packet = pack_auth(b"PAW1", 42, 7, sig)
        assert packet[0] == MSG_AUTH
        assert packet[1:5] == b"PAW1"
        nonce_bytes = struct.unpack_from("<I", packet, 5)[0]
        assert nonce_bytes == 42
        day_bytes = struct.unpack_from("<I", packet, 9)[0]
        assert day_bytes == 7
        assert packet[13:45] == sig

    def test_roundtrip(self):
        badge_id = b"PAW1"
        nonce = 9999
        day = 42
        sig = bytes(range(32))
        packet = pack_auth(badge_id, nonce, day, sig)
        data = unpack_auth(packet)
        assert data["badge_id"] == badge_id
        assert data["nonce"] == nonce
        assert data["day"] == day
        assert data["signature"] == sig

    def test_signature_all_zeros(self):
        sig = b"\x00" * 32
        packet = pack_auth(b"PAW1", 0, 1, sig)
        data = unpack_auth(packet)
        assert data["signature"] == sig

    def test_signature_all_ff(self):
        sig = b"\xff" * 32
        packet = pack_auth(b"PAW2", 42, 99, sig)
        data = unpack_auth(packet)
        assert data["signature"] == sig


# ── Cross-format isolation ─────────────────────────────────────

class TestCrossFormat:
    def test_beacon_and_auth_different_sizes(self):
        b = pack_beacon(b"FN01", 100, 1)
        a = pack_auth(b"PAW1", 1, 1, b"\x00" * 32)
        assert len(b) == 13
        assert len(a) == 45
        assert b != a

    def test_type_bytes_differ(self):
        b = pack_beacon(b"FN01", 100, 1)
        a = pack_auth(b"PAW1", 1, 1, b"\x00" * 32)
        assert b[0] == MSG_BEACON
        assert a[0] == MSG_AUTH
        assert MSG_BEACON != MSG_AUTH

    def test_wrong_size_rejected(self):
        try:
            unpack_beacon(b"\x01" * 10)
            assert False, "should have raised ValueError"
        except ValueError:
            pass

        try:
            unpack_auth(b"\x02" * 20)
            assert False, "should have raised ValueError"
        except ValueError:
            pass
