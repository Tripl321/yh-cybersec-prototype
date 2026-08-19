"""Pin definitions for Core1262-HF (SX1262) on each board.

CircuitPython only. Import the correct module at runtime.
"""

# ── PAW: Adafruit Feather RP2350 ──────────────────────────────

PAW_PINS = {
    "sck":  "SCK",    # board.SCK
    "mosi": "MOSI",   # board.MOSI
    "miso": "MISO",   # board.MISO
    "cs":   "D5",     # board.D5
    "rst":  "D6",     # board.D6
    "irq":  "D9",     # board.D9
    "busy": "D10",    # board.D10
}

# ── Field Node: Raspberry Pi Pico 2 W ─────────────────────────

FIELDNODE_PINS = {
    "sck":  "GP18",   # SPI0 SCK
    "mosi": "GP19",   # SPI0 TX
    "miso": "GP16",   # SPI0 RX
    "cs":   "GP17",   # SPI0 CSn
    "rst":  "GP15",
    "irq":  "GP20",   # DIO1
    "busy": "GP21",
}


def load_pins(pin_map: dict):
    """Resolve pin name strings to board/GPIO objects.

    Must be called from CircuitPython with `import board` in scope.
    Returns a dict of resolved pin objects.
    """
    import board as _board

    resolved = {}
    for key, name in pin_map.items():
        resolved[key] = getattr(_board, name)
    return resolved
