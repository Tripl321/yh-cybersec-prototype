"""Tests for storage.py — flash storage for enrolled keys and epoch.

Tests verify behavior through public interface.
Uses temp directory instead of real flash.
"""

import sys
import os
import tempfile
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage import Storage


class TestEnrolledStorage:
    """Tests for enrolled key storage."""

    def test_save_and_load_enrolled(self):
        """Saved enrolled keys can be loaded back."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = Storage(tmpdir)
            data = {
                "PAW1": {
                    "pubkey": "aabbccdd",
                    "epoch_secret": "11223344",
                    "valid_until": 30,
                }
            }
            store.save_enrolled(data)
            loaded = store.load_enrolled()
            assert loaded == data

    def test_load_enrolled_empty_when_no_file(self):
        """load_enrolled returns empty dict when no file exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = Storage(tmpdir)
            loaded = store.load_enrolled()
            assert loaded == {}

    def test_enrolled_cap_at_16(self):
        """Cannot save more than 16 enrolled badges."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = Storage(tmpdir)
            data = {}
            for i in range(17):
                data[f"PAW{i:02d}"] = {
                    "pubkey": f"key{i}",
                    "epoch_secret": f"secret{i}",
                    "valid_until": 30,
                }
            store.save_enrolled(data)
            loaded = store.load_enrolled()
            assert len(loaded) <= 16

    def test_overwrite_enrolled(self):
        """Saving new enrolled data overwrites old."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = Storage(tmpdir)
            store.save_enrolled({"PAW1": {"pubkey": "old"}})
            store.save_enrolled({"PAW2": {"pubkey": "new"}})
            loaded = store.load_enrolled()
            assert "PAW1" not in loaded
            assert "PAW2" in loaded


class TestEpochStorage:
    """Tests for epoch data storage."""

    def test_save_and_load_epoch(self):
        """Saved epoch data can be loaded back."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = Storage(tmpdir)
            data = {
                "secret": "aabbccdd",
                "valid_until": 30,
                "day": 15,
            }
            store.save_epoch(data)
            loaded = store.load_epoch()
            assert loaded == data

    def test_load_epoch_empty_when_no_file(self):
        """load_epoch returns empty dict when no file exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = Storage(tmpdir)
            loaded = store.load_epoch()
            assert loaded == {}

    def test_overwrite_epoch(self):
        """Saving new epoch data overwrites old."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = Storage(tmpdir)
            store.save_epoch({"secret": "old", "valid_until": 10, "day": 1})
            store.save_epoch({"secret": "new", "valid_until": 20, "day": 2})
            loaded = store.load_epoch()
            assert loaded["secret"] == "new"
            assert loaded["day"] == 2


class TestStorageInit:
    """Tests for Storage initialization."""

    def test_creates_directory(self):
        """Storage creates the data directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = os.path.join(tmpdir, "subdir")
            store = Storage(data_dir)
            assert os.path.isdir(data_dir)
