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
from epoch import verify_hmac
from storage import Storage
from provisioning import parse_command, handle_enroll, handle_revoke
from audit import AuditLog

# ── Hardware init ──────────────────────────────────────────────

spi = busio.SPI(clock=board.GP18, MOSI=board.GP19, MISO=board.GP16)
cs = digitalio.DigitalInOut(board.GP17)
rst = digitalio.DigitalInOut(board.GP15)
irq = digitalio.DigitalInOut(board.GP20)
busy = digitalio.DigitalInOut(board.GP21)

radio = ShallotRadio(spi, cs, rst, irq, busy)
relay = RelayController(board.GP14)

# ── Storage ────────────────────────────────────────────────────

store = Storage("/flash")
audit = AuditLog("/flash")

# ── Provisioning GPIO ──────────────────────────────────────────

provision_pin = digitalio.DigitalInOut(board.GP0)
provision_pin.direction = digitalio.Direction.INPUT
provision_pin.pull = digitalio.Pull.UP

# ── Serial for provisioning ────────────────────────────────────

import usb_cdc
serial = usb_cdc.data

# ── Callbacks ──────────────────────────────────────────────────

def get_keys():
    """Load enrolled keys from flash."""
    return store.load_enrolled()

def get_day():
    """Load current day from epoch data."""
    epoch = store.load_epoch()
    return epoch.get("day", 0)

def verify_auth(auth_data, keys):
    """Verify HMAC signature against enrolled key."""
    badge_id = auth_data["badge_id"]
    if badge_id not in keys:
        return False
    key = keys[badge_id]
    secret = bytes.fromhex(key["epoch_secret"])
    msg = auth_data["nonce"].to_bytes(4, "big") + auth_data["day"].to_bytes(4, "big")
    return verify_hmac(secret, msg, auth_data["signature"])

# ── State machine ──────────────────────────────────────────────

def on_access_decision(badge_id, decision):
    """Log access decision."""
    audit.log_access(badge_id, "FN01", decision, 0, int(time.monotonic() * 1000))

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
    # Check provisioning mode
    if not provision_pin.value:  # LOW = provisioning mode
        line = serial.readline()
        if line:
            cmd = parse_command(line.decode())
            if cmd:
                if cmd["cmd"] == "ENROLL":
                    result = handle_enroll(cmd, store)
                elif cmd["cmd"] == "REVOKE":
                    result = handle_revoke(cmd, store)
                serial.write(f"{result}\n".encode())
    else:
        # Normal operation
        fsm.tick()
