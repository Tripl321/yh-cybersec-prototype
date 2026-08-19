"""Field Node entry point — CircuitPython on Raspberry Pi Pico 2 W.

Main loop: non-blocking state machine. No time.sleep().
Fail-closed: relay OFF by default, 5s timeout, RSSI gate.
"""

import time
import board
import busio
import digitalio

from constants import HEARTBEAT_TIMEOUT_MS, RSSI_THRESHOLD_DBM
from hardware_pins import FIELDNODE_PINS
from shallot_radio import ShallotRadio
from relay_controller import RelayController
from state_machine import FieldNodeFSM

# ── Hardware init ──────────────────────────────────────────────

spi = busio.SPI(clock=board.GP18, MOSI=board.GP19, MISO=board.GP16)
cs = digitalio.DigitalInOut(board.GP17)
rst = digitalio.DigitalInOut(board.GP15)
irq = digitalio.DigitalInOut(board.GP20)
busy = digitalio.DigitalInOut(board.GP21)

radio = ShallotRadio(spi, cs, rst, irq, busy)
relay = RelayController(board.GP14)  # relay on GP14, adjust as needed

# ── Enrolled keys (populated by provisioning) ──────────────────

KEYS = {}


def get_keys():
    return KEYS


def get_day():
    """Stub: replace with real day counter (epoch-based)."""
    # TODO: read from RTC or Mama Bear sync
    return 1


def verify_auth(auth_data, keys):
    """Stub: replace with real HMAC verification from lock/main.py."""
    badge_id = auth_data["badge_id"]
    if badge_id not in keys:
        return False
    # TODO: verify signature against enrolled public key
    return True


# ── State machine ──────────────────────────────────────────────

fsm = FieldNodeFSM(
    radio=radio,
    relay=relay,
    node_id=b"FN01",
    verify_fn=verify_auth,
    get_keys_fn=get_keys,
    get_day_fn=get_day,
)

# ── Main loop ──────────────────────────────────────────────────

while True:
    fsm.tick()
