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

# ── Hardware init ──────────────────────────────────────────────

spi = busio.SPI(clock=board.SCK, MOSI=board.MOSI, MISO=board.MISO)
cs = digitalio.DigitalInOut(board.D5)
rst = digitalio.DigitalInOut(board.D6)
irq = digitalio.DigitalInOut(board.D9)
busy = digitalio.DigitalInOut(board.D10)

radio = ShallotRadio(spi, cs, rst, irq, busy)

# ── Button (active-low, use internal pull-up) ──────────────────

button = digitalio.DigitalInOut(board.D12)
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.UP

_last_button = True


def check_button():
    """Poll button. Returns True on press edge (not held)."""
    global _last_button
    current = button.value
    pressed = _last_button and not current
    _last_button = current
    return pressed


# ── FIDO signing stub ─────────────────────────────────────────

def sign_nonce(nonce: int, day: int) -> bytes:
    """Stub: replace with PicoFIDO HMAC signing over USB-serial.

    Signs: badge_id + nonce + day (12 bytes).
    Returns 32-byte HMAC-SHA256.
    """
    # TODO: send (nonce, day) to FIDO Key, receive 32-byte HMAC-SHA256
    return b"\x00" * 32


def get_day() -> int:
    """Stub: replace with real day counter (epoch-based)."""
    # TODO: read from RTC or Mama Bear sync
    return 1


# ── E-ink stub ─────────────────────────────────────────────────

def on_state_change(new_state):
    """Stub: update E-ink display on state transition."""
    # TODO: drive Waveshare e-Paper
    pass


# ── State machine ──────────────────────────────────────────────

paw = PAWFSM(
    radio=radio,
    badge_id=b"PAW1",
    sign_fn=sign_nonce,
    get_day_fn=get_day,
    on_state_change=on_state_change,
)

# ── Main loop ──────────────────────────────────────────────────

while True:
    if check_button():
        paw.on_button_press()
    paw.tick()
