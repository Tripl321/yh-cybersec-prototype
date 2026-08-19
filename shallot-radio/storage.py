"""Flash storage for enrolled keys and epoch data.

Uses JSON files on CircuitPython's storage mount.
In tests, uses a temp directory instead of real flash.
"""

import os
import json


MAX_ENROLLED = 16


class Storage:
    """Persistent storage for enrolled keys and epoch data.

    Data is stored as JSON files in the given directory.
    """

    def __init__(self, data_dir: str):
        """Initialize storage with a data directory.

        Args:
            data_dir: Path to directory for JSON files.
                      On CircuitPython: "/flash" or similar.
                      In tests: temp directory.
        """
        self._dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

    def load_enrolled(self) -> dict:
        """Load enrolled keys from flash.

        Returns:
            Dict of {badge_id: {"pubkey": str, "epoch_secret": str, "valid_until": int}}.
            Empty dict if no file exists.
        """
        path = os.path.join(self._dir, "enrolled.json")
        if not os.path.exists(path):
            return {}
        with open(path, "r") as f:
            return json.load(f)

    def save_enrolled(self, data: dict) -> None:
        """Save enrolled keys to flash.

        Caps at MAX_ENROLLED entries. Extra entries are dropped.
        """
        # Cap at MAX_ENROLLED
        if len(data) > MAX_ENROLLED:
            keys = list(data.keys())[:MAX_ENROLLED]
            data = {k: data[k] for k in keys}

        path = os.path.join(self._dir, "enrolled.json")
        with open(path, "w") as f:
            json.dump(data, f)

    def load_epoch(self) -> dict:
        """Load epoch data from flash.

        Returns:
            Dict with "secret", "valid_until", "day".
            Empty dict if no file exists.
        """
        path = os.path.join(self._dir, "epoch.json")
        if not os.path.exists(path):
            return {}
        with open(path, "r") as f:
            return json.load(f)

    def save_epoch(self, data: dict) -> None:
        """Save epoch data to flash."""
        path = os.path.join(self._dir, "epoch.json")
        with open(path, "w") as f:
            json.dump(data, f)
