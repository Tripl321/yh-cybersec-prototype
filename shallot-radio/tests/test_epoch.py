"""Tests for epoch.py — HMAC signing and verification.

Uses RFC 4231 test vectors. Tests verify behavior through public interface,
not implementation details.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from epoch import sign_hmac, verify_hmac


# RFC 4231 Test Case 2 — HMAC-SHA-256
KEY_2 = b"\x0b" * 20
MSG_2 = b"Hi There"
EXPECTED_2 = bytes.fromhex(
    "b0344c61d8db38535ca8afceaf0bf12b"
    "881dc200c9833da726e9376c2e32cff7"
)

# RFC 4231 Test Case 4 — empty message
KEY_4 = b"\x0a" * 13
MSG_4 = b""
EXPECTED_4 = bytes.fromhex(
    "f8d916be8db95945bb65544c2f4bcbdb"
    "d0acbede3ebc4ffafd96e866c8541d23"
)

class TestSignHmac:
    """Tests for sign_hmac function."""

    def test_rfc4231_case2(self):
        """sign_hmac returns correct HMAC-SHA256 for known input."""
        result = sign_hmac(KEY_2, MSG_2)
        assert result == EXPECTED_2

    def test_rfc4231_case4_empty_message(self):
        """sign_hmac works with empty message."""
        result = sign_hmac(KEY_4, MSG_4)
        assert result == EXPECTED_4

    def test_returns_32_bytes(self):
        """sign_hmac always returns 32-byte signature."""
        result = sign_hmac(b"key", b"msg")
        assert len(result) == 32

    def test_deterministic(self):
        """Same input produces same output."""
        r1 = sign_hmac(b"key", b"msg")
        r2 = sign_hmac(b"key", b"msg")
        assert r1 == r2

    def test_different_keys_differ(self):
        """Different keys produce different signatures."""
        r1 = sign_hmac(b"key1", b"msg")
        r2 = sign_hmac(b"key2", b"msg")
        assert r1 != r2

    def test_different_messages_differ(self):
        """Different messages produce different signatures."""
        r1 = sign_hmac(b"key", b"msg1")
        r2 = sign_hmac(b"key", b"msg2")
        assert r1 != r2


class TestVerifyHmac:
    """Tests for verify_hmac function."""

    def test_valid_signature(self):
        """verify_hmac returns True for correct signature."""
        sig = sign_hmac(KEY_2, MSG_2)
        assert verify_hmac(KEY_2, MSG_2, sig) is True

    def test_invalid_signature_wrong_key(self):
        """verify_hmac returns False when key is wrong."""
        sig = sign_hmac(KEY_2, MSG_2)
        assert verify_hmac(b"wrong_key", MSG_2, sig) is False

    def test_invalid_signature_wrong_message(self):
        """verify_hmac returns False when message is wrong."""
        sig = sign_hmac(KEY_2, MSG_2)
        assert verify_hmac(KEY_2, b"wrong_msg", sig) is False

    def test_invalid_signature_tampered(self):
        """verify_hmac returns False when signature is tampered."""
        sig = sign_hmac(KEY_2, MSG_2)
        tampered = bytearray(sig)
        tampered[0] ^= 0xFF
        assert verify_hmac(KEY_2, MSG_2, bytes(tampered)) is False

    def test_empty_signature(self):
        """verify_hmac returns False for empty signature."""
        assert verify_hmac(KEY_2, MSG_2, b"") is False

    def test_short_signature(self):
        """verify_hmac returns False for short signature."""
        assert verify_hmac(KEY_2, MSG_2, b"\x00" * 16) is False

    def test_empty_key_and_message(self):
        """verify_hmac works with empty key and message."""
        sig = sign_hmac(b"", b"")
        assert verify_hmac(b"", b"", sig) is True
