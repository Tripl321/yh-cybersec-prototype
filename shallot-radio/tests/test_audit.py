"""Tests for audit.py — access decision logging.

Tests verify behavior through public interface.
Uses temp directory instead of real flash.
"""

import sys
import os
import tempfile
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audit import AuditLog


class TestAuditLog:
    """Tests for AuditLog class."""

    def test_log_access(self):
        """Log an access decision and retrieve it."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log = AuditLog(tmpdir)
            log.log_access("PAW1", "FN01", "GRANTED", -45, 1000000)
            entries = log.get_logs()
            assert len(entries) == 1
            assert entries[0]["badge_id"] == "PAW1"
            assert entries[0]["node_id"] == "FN01"
            assert entries[0]["decision"] == "GRANTED"
            assert entries[0]["rssi"] == -45

    def test_multiple_logs(self):
        """Multiple log entries are appended."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log = AuditLog(tmpdir)
            log.log_access("PAW1", "FN01", "GRANTED", -45, 1000000)
            log.log_access("PAW2", "FN01", "DENIED", -80, 1000001)
            log.log_access("PAW1", "FN01", "GRANTED", -42, 1000002)
            entries = log.get_logs()
            assert len(entries) == 3

    def test_get_logs_empty(self):
        """get_logs returns empty list when no logs exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log = AuditLog(tmpdir)
            entries = log.get_logs()
            assert entries == []

    def test_log_preserves_order(self):
        """Logs are in chronological order."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log = AuditLog(tmpdir)
            log.log_access("PAW1", "FN01", "GRANTED", -45, 1000)
            log.log_access("PAW1", "FN01", "GRANTED", -45, 2000)
            log.log_access("PAW1", "FN01", "GRANTED", -45, 3000)
            entries = log.get_logs()
            assert entries[0]["timestamp"] < entries[1]["timestamp"]
            assert entries[1]["timestamp"] < entries[2]["timestamp"]

    def test_log_survives_reopen(self):
        """Logs persist across AuditLog instances."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log1 = AuditLog(tmpdir)
            log1.log_access("PAW1", "FN01", "GRANTED", -45, 1000)
            log2 = AuditLog(tmpdir)
            entries = log2.get_logs()
            assert len(entries) == 1
