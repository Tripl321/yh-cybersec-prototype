"""Access decision logging for SHALLOT.

Appends one JSON object per access attempt to a JSONL file.
Used by Field Node after each auth attempt.
"""

import os
import json


class AuditLog:
    """Append-only log for access decisions.

    Each entry is a JSON object on its own line (JSONL format).
    """

    def __init__(self, data_dir: str):
        """Initialize audit log with a data directory.

        Args:
            data_dir: Path to directory for audit.jsonl.
        """
        self._path = os.path.join(data_dir, "audit.jsonl")
        os.makedirs(data_dir, exist_ok=True)

    def log_access(self, badge_id: str, node_id: str, decision: str,
                   rssi: int, timestamp: int) -> None:
        """Append an access decision to the log.

        Args:
            badge_id: Badge identifier (e.g. "PAW1").
            node_id: Field Node identifier (e.g. "FN01").
            decision: "GRANTED" or "DENIED" or "TIMEOUT" etc.
            rssi: Signal strength in dBm.
            timestamp: Milliseconds since boot.
        """
        entry = {
            "badge_id": badge_id,
            "node_id": node_id,
            "decision": decision,
            "rssi": rssi,
            "timestamp": timestamp,
        }
        with open(self._path, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def get_logs(self) -> list:
        """Read all log entries.

        Returns:
            List of dicts, one per access attempt. Empty list if no log file.
        """
        if not os.path.exists(self._path):
            return []

        entries = []
        with open(self._path, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
        return entries
