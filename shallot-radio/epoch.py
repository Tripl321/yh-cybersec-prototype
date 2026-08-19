"""HMAC signing and verification for SHALLOT.

Pure functions. No hardware dependencies.
Used by both Field Node (verify) and PAW (sign).
"""

import hmac
import hashlib


def sign_hmac(key: bytes, msg: bytes) -> bytes:
    """Sign a message with HMAC-SHA256.

    Args:
        key: The shared secret (epoch_secret).
        msg: The message to sign (nonce + day or other fields).

    Returns:
        32-byte HMAC signature.
    """
    return hmac.new(key, msg, hashlib.sha256).digest()


def verify_hmac(key: bytes, msg: bytes, expected: bytes) -> bool:
    """Verify an HMAC signature using constant-time comparison.

    Args:
        key: The shared secret (epoch_secret).
        msg: The message that was signed.
        expected: The signature to verify against.

    Returns:
        True if signature is valid, False otherwise.
    """
    if not expected or len(expected) != 32:
        return False
    computed = hmac.new(key, msg, hashlib.sha256).digest()
    return hmac.compare_digest(computed, expected)
