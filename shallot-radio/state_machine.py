"""State machines for Field Node and PAW.

Non-blocking. Uses time.monotonic() for all timing.
No time.sleep(). Call tick() in your main loop.
"""

import time
from constants import (
    MSG_BEACON, MSG_AUTH,
    HEARTBEAT_TIMEOUT_MS, RSSI_THRESHOLD_DBM,
)

# ── Field Node states ──────────────────────────────────────────

FN_LOCKED = 0
FN_LISTENING = 1
FN_ACCESS_GRANTED = 2


class FieldNodeFSM:
    """Field Node state machine.

    States:
        LOCKED       → relay OFF, sending beacons, waiting for auth
        LISTENING    → beacon sent, listening for auth request
        GRANTED      → auth valid, relay ON, monitoring RSSI + timeout

    Fail-closed: any timeout or RSSI drop → LOCKED.
    """

    def __init__(self, radio, relay, node_id: bytes,
                 verify_fn=None, get_keys_fn=None, get_day_fn=None):
        """
        radio       — ShallotRadio instance
        relay       — RelayController instance
        node_id     — 4-byte identifier (e.g. b'FN01')
        verify_fn   — callable(auth_data, keys) -> bool
                      Returns True if signature is valid.
        get_keys_fn — callable() -> dict
                      Returns enrolled keys for verification.
        get_day_fn  — callable() -> int
                      Returns current day number for epoch check.
        """
        self._radio = radio
        self._relay = relay
        self._node_id = node_id
        self._verify_fn = verify_fn
        self._get_keys_fn = get_keys_fn
        self._get_day_fn = get_day_fn

        self._state = FN_LOCKED
        self._last_beacon_ms = 0
        self._last_valid_auth_ms = 0
        self._current_nonce = 0

        self._enter_locked()

    # ── Public API ─────────────────────────────────────────────

    def tick(self):
        """Call once per main loop iteration. Non-blocking."""
        now_ms = int(time.monotonic() * 1000)

        if self._state == FN_LOCKED:
            self._tick_locked(now_ms)

        elif self._state == FN_LISTENING:
            self._tick_listening(now_ms)

        elif self._state == FN_ACCESS_GRANTED:
            self._tick_granted(now_ms)

    @property
    def state(self) -> int:
        return self._state

    @property
    def state_name(self) -> str:
        return {FN_LOCKED: "LOCKED", FN_LISTENING: "LISTENING",
                FN_ACCESS_GRANTED: "GRANTED"}.get(self._state, "UNKNOWN")

    # ── State handlers ─────────────────────────────────────────

    def _tick_locked(self, now_ms):
        """Send beacons periodically. Listen for auth requests."""
        if now_ms - self._last_beacon_ms >= 1000:
            self._current_nonce = now_ms & 0xFFFFFFFF
            self._radio.send_beacon(self._node_id, now_ms, self._current_nonce)
            self._last_beacon_ms = now_ms
            self._state = FN_LISTENING

    def _tick_listening(self, now_ms):
        """Wait for auth request. Timeout → back to LOCKED."""
        result = self._radio.receive()
        if result is not None:
            msg_type, data, rssi = result
            if msg_type == MSG_AUTH and rssi >= RSSI_THRESHOLD_DBM:
                if self._verify_auth(data):
                    self._last_valid_auth_ms = now_ms
                    self._enter_granted()
                    return

        # No valid auth received → fail-closed
        self._enter_locked()

    def _tick_granted(self, now_ms):
        """Keep relay ON. Monitor timeout + RSSI. Fail-closed on any breach."""
        # Heartbeat timeout
        if now_ms - self._last_valid_auth_ms >= HEARTBEAT_TIMEOUT_MS:
            self._enter_locked()
            return

        # Listen for re-auth (heartbeat renewal)
        result = self._radio.receive()
        if result is not None:
            msg_type, data, rssi = result
            if msg_type == MSG_AUTH and rssi >= RSSI_THRESHOLD_DBM:
                if self._verify_auth(data):
                    self._last_valid_auth_ms = now_ms
                    return
            # Invalid auth → immediate lock
            self._enter_locked()

    # ── Transitions ────────────────────────────────────────────

    def _enter_locked(self):
        self._state = FN_LOCKED
        self._relay.off()

    def _enter_granted(self):
        self._state = FN_ACCESS_GRANTED
        self._relay.on()

    # ── Verification ───────────────────────────────────────────

    def _verify_auth(self, data: dict) -> bool:
        """Verify auth request: nonce match + day valid + signature valid."""
        if data["nonce"] != self._current_nonce:
            return False
        if self._verify_fn is None or self._get_keys_fn is None or self._get_day_fn is None:
            return False
        keys = self._get_keys_fn()
        badge_id = data["badge_id"]
        if badge_id not in keys:
            return False
        # Offline revocation: calendar passed the badge's valid_until
        if data["day"] > keys[badge_id].get("valid_until", 0):
            return False
        return self._verify_fn(data, keys)


# ── PAW states ─────────────────────────────────────────────────

PAW_OFF_SITE = 0
PAW_ON_SITE = 1
PAW_REQUESTING = 2
PAW_AUTH_SENT = 3
PAW_GRANTED = 4


class PAWFSM:
    """PAW (wearable) state machine.

    States:
        OFF_SITE    → no beacon, E-ink blank
        ON_SITE     → beacon received, E-ink shows "on site"
        REQUESTING  → button pressed, requesting FIDO signature
        AUTH_SENT   → auth transmitted, waiting for Field Node response
        GRANTED     → access confirmed

    The PAW does NOT control a relay. It only sends auth and displays status.
    """

    def __init__(self, radio, badge_id: bytes,
                 sign_fn=None, get_day_fn=None, on_state_change=None):
        """
        radio          — ShallotRadio instance
        badge_id       — 4-byte identifier (e.g. b'PAW1')
        sign_fn        — callable(nonce: int, day: int) -> bytes(32)
                         Calls FIDO Key to sign (nonce + day).
        get_day_fn     — callable() -> int
                         Returns current day number for epoch.
        on_state_change — callable(new_state: int) -> None
                         Called on every state transition (for E-ink update).
        """
        self._radio = radio
        self._badge_id = badge_id
        self._sign_fn = sign_fn
        self._get_day_fn = get_day_fn
        self._on_state_change = on_state_change

        self._state = PAW_OFF_SITE
        self._last_beacon_ms = 0
        self._last_nonce = 0

    # ── Public API ─────────────────────────────────────────────

    def tick(self):
        """Call once per main loop. Non-blocking."""
        now_ms = int(time.monotonic() * 1000)

        if self._state == PAW_OFF_SITE:
            self._tick_off_site(now_ms)
        elif self._state == PAW_ON_SITE:
            self._tick_on_site(now_ms)
        elif self._state == PAW_REQUESTING:
            self._tick_requesting(now_ms)
        elif self._state == PAW_AUTH_SENT:
            self._tick_auth_sent(now_ms)
        elif self._state == PAW_GRANTED:
            self._tick_granted(now_ms)

    def on_button_press(self):
        """Call from hardware interrupt. Transitions ON_SITE → REQUESTING."""
        if self._state == PAW_ON_SITE:
            self._set_state(PAW_REQUESTING)

    @property
    def state(self) -> int:
        return self._state

    @property
    def state_name(self) -> str:
        return {
            PAW_OFF_SITE: "OFF_SITE",
            PAW_ON_SITE: "ON_SITE",
            PAW_REQUESTING: "REQUESTING",
            PAW_AUTH_SENT: "AUTH_SENT",
            PAW_GRANTED: "GRANTED",
        }.get(self._state, "UNKNOWN")

    # ── State handlers ─────────────────────────────────────────

    def _tick_off_site(self, now_ms):
        """Listen for beacons. Transition → ON_SITE on first beacon."""
        result = self._radio.receive()
        if result is not None:
            msg_type, data, rssi = result
            if msg_type == MSG_BEACON and rssi >= RSSI_THRESHOLD_DBM:
                self._last_beacon_ms = now_ms
                self._last_nonce = data["nonce"]
                self._set_state(PAW_ON_SITE)

    def _tick_on_site(self, now_ms):
        """Listen for beacons to stay on-site. Timeout → OFF_SITE."""
        result = self._radio.receive()
        if result is not None:
            msg_type, data, rssi = result
            if msg_type == MSG_BEACON and rssi >= RSSI_THRESHOLD_DBM:
                self._last_beacon_ms = now_ms
                self._last_nonce = data["nonce"]
                return

        if now_ms - self._last_beacon_ms >= HEARTBEAT_TIMEOUT_MS:
            self._set_state(PAW_OFF_SITE)

    def _tick_requesting(self, now_ms):
        """Request FIDO signature, then send auth."""
        if self._sign_fn is None or self._get_day_fn is None:
            self._set_state(PAW_ON_SITE)
            return

        day = self._get_day_fn()
        signature = self._sign_fn(self._last_nonce, day)
        if signature is None or len(signature) != 32:
            self._set_state(PAW_ON_SITE)
            return

        self._radio.send_auth(self._badge_id, self._last_nonce, day, signature)
        self._set_state(PAW_AUTH_SENT)

    def _tick_auth_sent(self, now_ms):
        """Wait for Field Node to accept (relay ON = implicit ACK via beacon).
        Timeout → back to ON_SITE.
        """
        result = self._radio.receive()
        if result is not None:
            msg_type, data, rssi = result
            if msg_type == MSG_BEACON and rssi >= RSSI_THRESHOLD_DBM:
                # Field Node still sending beacons = hasn't accepted yet
                self._last_beacon_ms = now_ms
                self._last_nonce = data["nonce"]
                # If we got our beacon nonce back, access was granted
                self._set_state(PAW_GRANTED)
                return

        if now_ms - self._last_beacon_ms >= HEARTBEAT_TIMEOUT_MS:
            self._set_state(PAW_ON_SITE)

    def _tick_granted(self, now_ms):
        """Monitor beacons. Timeout → OFF_SITE."""
        result = self._radio.receive()
        if result is not None:
            msg_type, data, rssi = result
            if msg_type == MSG_BEACON and rssi >= RSSI_THRESHOLD_DBM:
                self._last_beacon_ms = now_ms
                self._last_nonce = data["nonce"]
                return

        if now_ms - self._last_beacon_ms >= HEARTBEAT_TIMEOUT_MS:
            self._set_state(PAW_OFF_SITE)

    # ── Transitions ────────────────────────────────────────────

    def _set_state(self, new_state: int):
        old = self._state
        self._state = new_state
        if self._on_state_change is not None and old != new_state:
            self._on_state_change(new_state)
