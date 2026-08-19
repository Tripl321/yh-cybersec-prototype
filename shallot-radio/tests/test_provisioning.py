"""Tests for provisioning.py — serial command parser.

Tests verify behavior through public interface.
"""

import sys
import os
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from provisioning import parse_command, handle_enroll, handle_revoke
from storage import Storage


class TestParseCommand:
    """Tests for parse_command function."""

    def test_parse_enroll(self):
        """Parses valid ENROLL command."""
        line = '{"cmd": "ENROLL", "badge_id": "PAW1", "pubkey": "aabbccdd"}'
        result = parse_command(line)
        assert result is not None
        assert result["cmd"] == "ENROLL"
        assert result["badge_id"] == "PAW1"
        assert result["pubkey"] == "aabbccdd"

    def test_parse_revoke(self):
        """Parses valid REVOKE command."""
        line = '{"cmd": "REVOKE", "badge_id": "PAW1"}'
        result = parse_command(line)
        assert result is not None
        assert result["cmd"] == "REVOKE"
        assert result["badge_id"] == "PAW1"

    def test_parse_invalid_json(self):
        """Returns None for invalid JSON."""
        result = parse_command("not json")
        assert result is None

    def test_parse_missing_cmd(self):
        """Returns None when cmd field is missing."""
        result = parse_command('{"badge_id": "PAW1"}')
        assert result is None

    def test_parse_unknown_cmd(self):
        """Returns None for unknown command."""
        result = parse_command('{"cmd": "DELETE"}')
        assert result is None

    def test_parse_enroll_missing_badge_id(self):
        """Returns None when ENROLL is missing badge_id."""
        result = parse_command('{"cmd": "ENROLL", "pubkey": "aabb"}')
        assert result is None

    def test_parse_enroll_missing_pubkey(self):
        """Returns None when ENROLL is missing pubkey."""
        result = parse_command('{"cmd": "ENROLL", "badge_id": "PAW1"}')
        assert result is None

    def test_parse_revoke_missing_badge_id(self):
        """Returns None when REVOKE is missing badge_id."""
        result = parse_command('{"cmd": "REVOKE"}')
        assert result is None

    def test_parse_empty_string(self):
        """Returns None for empty string."""
        result = parse_command("")
        assert result is None

    def test_parse_with_extra_whitespace(self):
        """Parses command with extra whitespace."""
        line = '  {"cmd": "REVOKE", "badge_id": "PAW1"}  '
        result = parse_command(line)
        assert result is not None
        assert result["cmd"] == "REVOKE"


class TestHandleEnroll:
    """Tests for handle_enroll function."""

    def test_enroll_adds_badge(self):
        """Enrolling a badge adds it to storage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = Storage(tmpdir)
            cmd = {"cmd": "ENROLL", "badge_id": "PAW1", "pubkey": "aabbccdd"}
            result = handle_enroll(cmd, store)
            assert result == "OK"
            enrolled = store.load_enrolled()
            assert "PAW1" in enrolled
            assert enrolled["PAW1"]["pubkey"] == "aabbccdd"

    def test_enroll_replaces_existing(self):
        """Enrolling same badge_id replaces existing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = Storage(tmpdir)
            store.save_enrolled({"PAW1": {"pubkey": "old", "epoch_secret": "x", "valid_until": 10}})
            cmd = {"cmd": "ENROLL", "badge_id": "PAW1", "pubkey": "new"}
            result = handle_enroll(cmd, store)
            assert result == "OK"
            enrolled = store.load_enrolled()
            assert enrolled["PAW1"]["pubkey"] == "new"

    def test_enroll_caps_at_16(self):
        """Enrolling 17th badge returns error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = Storage(tmpdir)
            # Fill with 16 badges
            data = {f"PAW{i:02d}": {"pubkey": f"key{i}", "epoch_secret": "s", "valid_until": 30} for i in range(16)}
            store.save_enrolled(data)
            cmd = {"cmd": "ENROLL", "badge_id": "PAW16", "pubkey": "overflow"}
            result = handle_enroll(cmd, store)
            assert "ERROR" in result


class TestHandleRevoke:
    """Tests for handle_revoke function."""

    def test_revoke_removes_badge(self):
        """Revoking a badge removes it from storage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = Storage(tmpdir)
            store.save_enrolled({"PAW1": {"pubkey": "aabb", "epoch_secret": "x", "valid_until": 10}})
            cmd = {"cmd": "REVOKE", "badge_id": "PAW1"}
            result = handle_revoke(cmd, store)
            assert result == "OK"
            enrolled = store.load_enrolled()
            assert "PAW1" not in enrolled

    def test_revoke_nonexistent_badge(self):
        """Revoking a badge that doesn't exist returns OK (idempotent)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = Storage(tmpdir)
            cmd = {"cmd": "REVOKE", "badge_id": "PAW99"}
            result = handle_revoke(cmd, store)
            assert result == "OK"
