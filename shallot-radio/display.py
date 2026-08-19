"""E-ink display driver for PAW.

Shows contextual status:
- off_site: blank or generic branding
- on_site: credentials + node_id
- granted: "Access Granted"
- denied: "Access Denied"

Uses adafruit_epd library for Feather RP2350 + Waveshare E-ink.
"""

import board


class Display:
    """E-ink display driver.

    On real hardware, uses adafruit_epd.
    In tests, use MockDisplay instead.
    """

    def __init__(self, cs_pin=None, dc_pin=None, rst_pin=None, busy_pin=None):
        """Initialize E-ink display.

        Args:
            cs_pin: Chip select pin.
            dc_pin: Data/command pin.
            rst_pin: Reset pin.
            busy_pin: Busy pin.
        """
        # Real implementation would initialize adafruit_epd here
        pass

    def show_on_site(self, node_id: bytes):
        """Show on-site status with node_id.

        Args:
            node_id: 4-byte Field Node identifier (e.g. b'FN01').
        """
        # Real implementation: render text to E-ink
        pass

    def show_off_site(self):
        """Clear display or show generic branding."""
        # Real implementation: clear E-ink
        pass

    def show_granted(self):
        """Show "Access Granted" message."""
        # Real implementation: render text to E-ink
        pass

    def show_denied(self):
        """Show "Access Denied" message."""
        # Real implementation: render text to E-ink
        pass


class MockDisplay:
    """Mock E-ink display for testing."""

    def __init__(self):
        self.last_shown = None

    def show_on_site(self, node_id: bytes):
        self.last_shown = ("on_site", node_id)

    def show_off_site(self):
        self.last_shown = ("off_site",)

    def show_granted(self):
        self.last_shown = ("granted",)

    def show_denied(self):
        self.last_shown = ("denied",)
