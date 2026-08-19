"""Relay controller for Field Node.

Single responsibility: GPIO on/off. No protocol logic.
Fail-closed: default state is OFF.
"""

import digitalio


class RelayController:
    """Drives a relay (or LED fallback) via GPIO.

    active_high=True  → relay ON  = pin HIGH (most relay modules)
    active_high=False → relay ON  = pin LOW  (inverted modules)
    """

    def __init__(self, pin, active_high: bool = True):
        self._pin = digitalio.DigitalInOut(pin)
        self._pin.direction = digitalio.Direction.OUTPUT
        self._active_high = active_high
        self._state = False
        self.off()  # fail-closed: start OFF

    def on(self):
        """Energise relay (close circuit)."""
        self._pin.value = self._active_high
        self._state = True

    def off(self):
        """De-energise relay (open circuit). Fail-closed default."""
        self._pin.value = not self._active_high
        self._state = False

    @property
    def is_active(self) -> bool:
        return self._state
