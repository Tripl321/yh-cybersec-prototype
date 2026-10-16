"""Security tests for Cub ingress scrubber key handling."""

import pytest

from cub.config import CubConfig
from cub.scrubber import IngressScrubber


def test_scrypt_key_is_deterministic_and_separated():
    first = IngressScrubber._derive_key("correct-horse-battery-staple")
    second = IngressScrubber._derive_key("correct-horse-battery-staple")
    different = IngressScrubber._derive_key("different-secure-passphrase")
    assert len(first) == 64
    assert first == second
    assert first != different


def test_short_configured_passphrase_is_rejected():
    with pytest.raises(ValueError, match="at least 16"):
        IngressScrubber(CubConfig(scrubber_fpe_key="too-short"))


def test_missing_passphrase_uses_unique_process_local_keys():
    first = IngressScrubber(CubConfig(scrubber_fpe_key=None))
    second = IngressScrubber(CubConfig(scrubber_fpe_key=None))
    assert len(first._key) == 64
    assert len(second._key) == 64
    assert first._key != second._key


def test_scrubbing_remains_deterministic_within_instance():
    scrubber = IngressScrubber(
        CubConfig(scrubber_fpe_key="local-test-passphrase-1234")
    )
    first = scrubber.scrub("admin connected to node-17 at 10.0.0.5")
    second = scrubber.scrub("admin connected to node-17 at 10.0.0.5")
    assert first == second
    assert "admin" not in first.lower()
    assert "node-17" not in first.lower()
    assert "10.0.0.5" not in first
