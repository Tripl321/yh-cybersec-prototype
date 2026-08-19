"""Button handler for PAW.

Uses hardware interrupt on BOOT button.
Debounce: 50ms.
Calls paw.on_button_press() on valid press.
"""

import board
import digitalio
import time


DEBOUNCE_MS = 50


class Button:
    """Hardware button handler.

    On real hardware, uses interrupt pin.
    In tests, use MockButton instead.
    """

    def __init__(self, pin=None, callback=None):
        """Initialize button handler.

        Args:
            pin: Button pin (default: board.BUTTON or board.GP0).
            callback: Function to call on valid press.
        """
        self._pin = digitalio.DigitalInOut(pin or board.BUTTON)
        self._pin.direction = digitalio.Direction.INPUT
        self._pin.pull = digitalio.Pull.UP
        self._callback = callback
        self._last_press_ms = 0

    def check(self):
        """Check button state. Call in main loop.

        Returns:
            True if button was pressed (with debounce), False otherwise.
        """
        now_ms = int(time.monotonic() * 1000)
        if not self._pin.value:  # Button pressed (active low)
            if now_ms - self._last_press_ms >= DEBOUNCE_MS:
                self._last_press_ms = now_ms
                if self._callback:
                    self._callback()
                return True
        return False


class MockButton:
    """Mock button for testing."""

    def __init__(self):
        self._callback = None
        self.press_count = 0

    def set_callback(self, callback):
        self._callback = callback

    def press(self):
        """Simulate a button press."""
        self.press_count += 1
        if self._callback:
            self._callback()
