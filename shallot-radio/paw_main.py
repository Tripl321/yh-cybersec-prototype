"""PAW entry point — CircuitPython on Adafruit Feather RP2350.

Main loop: non-blocking state machine. No time.sleep().
Button press triggers FIDO Key signing.
"""

import time
import board
import busio
import digitalio

from constants import HEARTBEAT_TIMEOUT_MS, RSSI_THRESHOLD_DBM
from shallot_radio import ShallotRadio
from state_machine import PAWFSM
from storage import Storage
from fido_bridge import FidoBridge
from display import Display
from button import Button

# ── Hardware init ──────────────────────────────────────────────

spi = busio.SPI(clock=board.SCK, MOSI=board.MOSI, MISO=board.MISO)
cs = digitalio.DigitalInOut(board.D5)
rst = digitalio.DigitalInOut(board.D6)
irq = digitalio.DigitalInOut(board.D9)
busy = digitalio.DigitalInOut(board.D10)

radio = ShallotRadio(spi, cs, rst, irq, busy)

# ── Storage ────────────────────────────────────────────────────

store = Storage("/flash")

# ── FIDO Key bridge ────────────────────────────────────────────

fido = FidoBridge()

# ── Display ────────────────────────────────────────────────────

display = Display()

# ── Button ─────────────────────────────────────────────────────

paw_state = None  # Will be set after PAWFSM init

def on_button_press():
    """Called by Button handler on valid press."""
    if paw_state:
        paw_state.on_button_press()

button = Button(callback=on_button_press)

# ── Callbacks ──────────────────────────────────────────────────

def sign_nonce(nonce: int, day: int) -> bytes:
    """Sign (nonce, day) via FIDO Key over USB-serial."""
    return fido.sign(nonce, day)

def get_day() -> int:
    """Load current day from epoch data."""
    epoch = store.load_epoch()
    return epoch.get("day", 0)

def on_state_change(new_state):
    """Update E-ink display on state transition."""
    state_names = {
        0: "OFF_SITE",
        1: "ON_SITE",
        2: "REQUESTING",
        3: "AUTH_SENT",
        4: "GRANTED",
    }
    name = state_names.get(new_state, "UNKNOWN")
    if name == "OFF_SITE":
        display.show_off_site()
    elif name == "ON_SITE":
        display.show_on_site(b"FN01")  # TODO: get from beacon
    elif name == "GRANTED":
        display.show_granted()
    elif name in ("REQUESTING", "AUTH_SENT"):
        pass  # No display change during request

# ── State machine ──────────────────────────────────────────────

paw_state = PAWFSM(
    radio=radio,
    badge_id=b"PAW1",
    sign_fn=sign_nonce,
    get_day_fn=get_day,
    on_state_change=on_state_change,
)

# ── Main loop ──────────────────────────────────────────────────

while True:
    button.check()
    paw_state.tick()
