"""Integration test — full access flow with mocks.

Tests the complete flow: button → sign → send → verify → relay.
Uses mock hardware (radio, relay, display, FIDO Key).
"""

import sys
import os
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from epoch import sign_hmac, verify_hmac
from storage import Storage
from provisioning import parse_command, handle_enroll, handle_revoke
from audit import AuditLog
from constants import MSG_BEACON, MSG_AUTH
from state_machine import FieldNodeFSM, PAWFSM


# ── Mocks ────────────────────────────────────────────────────────

class MockRadio:
    """Mock LoRa radio for testing."""

    def __init__(self):
        self.sent = []
        self.receive_queue = []

    def send_beacon(self, node_id, timestamp, nonce):
        self.sent.append(("beacon", node_id, timestamp, nonce))

    def send_auth(self, badge_id, nonce, day, signature):
        self.sent.append(("auth", badge_id, nonce, day, signature))

    def receive(self):
        if self.receive_queue:
            return self.receive_queue.pop(0)
        return None

    def queue_beacon(self, node_id, timestamp, nonce, rssi=-40):
        self.receive_queue.append((MSG_BEACON, {"node_id": node_id, "timestamp": timestamp, "nonce": nonce}, rssi))

    def queue_auth(self, badge_id, nonce, day, signature, rssi=-40):
        self.receive_queue.append((MSG_AUTH, {"badge_id": badge_id, "nonce": nonce, "day": day, "signature": signature}, rssi))


class MockRelay:
    """Mock relay for testing."""

    def __init__(self):
        self.state = "OFF"
        self.history = []

    def on(self):
        self.state = "ON"
        self.history.append(("ON",))

    def off(self):
        self.state = "OFF"
        self.history.append(("OFF",))


class MockDisplay:
    """Mock E-ink display for testing."""

    def __init__(self):
        self.last_shown = None

    def show_on_site(self, node_id):
        self.last_shown = ("on_site", node_id)

    def show_off_site(self):
        self.last_shown = ("off_site",)

    def show_granted(self):
        self.last_shown = ("granted",)

    def show_denied(self):
        self.last_shown = ("denied",)


# ── Integration Tests ────────────────────────────────────────────

class TestProvisioningFlow:
    """Test ENROLL/REVOKE over serial."""

    def test_enroll_then_verify(self):
        """Enrolled badge can be verified."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = Storage(tmpdir)
            epoch_secret = b"secret123"

            # Mama Bear enrolls PAW1
            cmd = {"cmd": "ENROLL", "badge_id": "PAW1", "pubkey": "aabbccdd"}
            result = handle_enroll(cmd, store)
            assert result == "OK"

            # Set epoch secret
            store.save_epoch({"secret": epoch_secret.hex(), "valid_until": 30, "day": 15})

            # Verify badge is enrolled
            enrolled = store.load_enrolled()
            assert "PAW1" in enrolled

            # Verify HMAC works
            nonce = 12345
            day = 15
            msg = nonce.to_bytes(4, "big") + day.to_bytes(4, "big")
            sig = sign_hmac(epoch_secret, msg)
            assert verify_hmac(epoch_secret, msg, sig) is True

    def test_revoke_then_deny(self):
        """Revoked badge is no longer enrolled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = Storage(tmpdir)

            # Enroll then revoke
            cmd = {"cmd": "ENROLL", "badge_id": "PAW1", "pubkey": "aabbccdd"}
            handle_enroll(cmd, store)
            cmd = {"cmd": "REVOKE", "badge_id": "PAW1"}
            result = handle_revoke(cmd, store)
            assert result == "OK"

            # Badge is gone
            enrolled = store.load_enrolled()
            assert "PAW1" not in enrolled


class TestFieldNodeFlow:
    """Test Field Node state machine with real crypto."""

    def test_valid_auth_triggers_relay(self):
        """Valid signature → relay ON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = Storage(tmpdir)
            epoch_secret = b"secret123"
            store.save_epoch({"secret": epoch_secret.hex(), "valid_until": 30, "day": 15})
            store.save_enrolled({"PAW1": {"pubkey": "aabb", "epoch_secret": epoch_secret.hex(), "valid_until": 30}})

            radio = MockRadio()
            relay = MockRelay()

            def verify_fn(data, keys):
                badge_id = data["badge_id"]
                if badge_id not in keys:
                    return False
                key = keys[badge_id]
                secret = bytes.fromhex(key["epoch_secret"])
                msg = data["nonce"].to_bytes(4, "big") + data["day"].to_bytes(4, "big")
                return verify_hmac(secret, msg, data["signature"])

            def get_keys_fn():
                return store.load_enrolled()

            def get_day_fn():
                return 15

            node = FieldNodeFSM(radio, relay, b"FN01",
                               verify_fn=verify_fn,
                               get_keys_fn=get_keys_fn,
                               get_day_fn=get_day_fn)

            # Node sends beacon
            node.tick()
            assert len(radio.sent) == 1
            assert radio.sent[0][0] == "beacon"
            nonce = radio.sent[0][3]

            # Queue valid auth response
            day = 15
            msg = nonce.to_bytes(4, "big") + day.to_bytes(4, "big")
            sig = sign_hmac(epoch_secret, msg)
            radio.queue_auth("PAW1", nonce, day, sig)

            # Node processes auth
            node.tick()
            assert relay.state == "ON"

    def test_bad_signature_stays_locked(self):
        """Invalid signature → relay stays OFF."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = Storage(tmpdir)
            store.save_enrolled({"PAW1": {"pubkey": "aabb", "epoch_secret": "00" * 32, "valid_until": 30}})

            radio = MockRadio()
            relay = MockRelay()

            def verify_fn(data, keys):
                return False  # Always reject

            def get_keys_fn():
                return store.load_enrolled()

            def get_day_fn():
                return 15

            node = FieldNodeFSM(radio, relay, b"FN01",
                               verify_fn=verify_fn,
                               get_keys_fn=get_keys_fn,
                               get_day_fn=get_day_fn)

            node.tick()
            nonce = radio.sent[0][3]

            radio.queue_auth("PAW1", nonce, 15, b"\x00" * 32)
            node.tick()
            assert relay.state == "OFF"


class TestPAWFlow:
    """Test PAW state machine with mock FIDO Key."""

    def test_beacon_triggers_on_site(self):
        """Receiving beacon → ON_SITE state."""
        radio = MockRadio()
        paw = PAWFSM(radio, b"PAW1")

        radio.queue_beacon("FN01", 1000, 42)
        paw.tick()
        assert paw.state_name == "ON_SITE"

    def test_button_press_requests_signature(self):
        """Button press → REQUESTING state."""
        radio = MockRadio()
        paw = PAWFSM(radio, b"PAW1")

        radio.queue_beacon("FN01", 1000, 42)
        paw.tick()
        assert paw.state_name == "ON_SITE"

        paw.on_button_press()
        assert paw.state_name == "REQUESTING"

    def test_sign_and_send_auth(self):
        """REQUESTING → sign → AUTH_SENT."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = Storage(tmpdir)
            epoch_secret = b"secret123"
            store.save_epoch({"secret": epoch_secret.hex(), "valid_until": 30, "day": 15})

            radio = MockRadio()

            def sign_fn(nonce, day):
                return sign_hmac(epoch_secret, nonce.to_bytes(4, "big") + day.to_bytes(4, "big"))

            def get_day_fn():
                return 15

            paw = PAWFSM(radio, b"PAW1", sign_fn=sign_fn, get_day_fn=get_day_fn)

            radio.queue_beacon("FN01", 1000, 42)
            paw.tick()
            paw.on_button_press()
            paw.tick()

            assert paw.state_name == "AUTH_SENT"
            assert len(radio.sent) == 1
            assert radio.sent[0][0] == "auth"


class TestAuditTrail:
    """Test audit logging during access flow."""

    def test_access_logged(self):
        """Access decisions are logged."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log = AuditLog(tmpdir)
            log.log_access("PAW1", "FN01", "GRANTED", -45, 1000000)
            log.log_access("PAW2", "FN01", "DENIED", -80, 1000001)

            entries = log.get_logs()
            assert len(entries) == 2
            assert entries[0]["decision"] == "GRANTED"
            assert entries[1]["decision"] == "DENIED"
