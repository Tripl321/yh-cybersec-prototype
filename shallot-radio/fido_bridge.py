"""USB-serial bridge between PAW and FIDO Key.

PAW sends: SIGN <nonce_hex> <day_hex>\n
FIDO Key replies: <signature_hex>\n

Timeout: 500ms. On timeout, returns None.
"""

import board
import busio


BAUD_RATE = 115200
TIMEOUT_MS = 500


class FidoBridge:
    """USB-serial bridge to FIDO Key.

    On real hardware, uses UART to communicate with ESP32-S3-Nano.
    In tests, use MockFidoBridge instead.
    """

    def __init__(self, tx_pin=None, rx_pin=None, baud_rate=BAUD_RATE):
        """Initialize UART bridge.

        Args:
            tx_pin: TX pin (default: board.TX).
            rx_pin: RX pin (default: board.RX).
            baud_rate: UART baud rate.
        """
        self._uart = busio.UART(
            tx_pin or board.TX,
            rx_pin or board.RX,
            baudrate=baud_rate,
        )

    def sign(self, nonce: int, day: int) -> bytes | None:
        """Request FIDO Key to sign (nonce, day).

        Args:
            nonce: Challenge nonce from Field Node.
            day: Current day index.

        Returns:
            32-byte signature, or None on timeout/error.
        """
        # Build request: "SIGN <nonce_hex> <day_hex>\n"
        nonce_hex = f"{nonce:08x}"
        day_hex = f"{day:08x}"
        request = f"SIGN {nonce_hex} {day_hex}\n"
        self._uart.write(request.encode())

        # Read response: "<signature_hex>\n"
        response = b""
        import time
        start = time.monotonic()
        while time.monotonic() - start < TIMEOUT_MS / 1000:
            byte = self._uart.read(1)
            if byte:
                if byte == b"\n":
                    break
                response += byte

        if not response:
            return None

        try:
            return bytes.fromhex(response.decode().strip())
        except (ValueError, UnicodeDecodeError):
            return None


class MockFidoBridge:
    """Mock FIDO Key for testing."""

    def __init__(self):
        self._signature = None

    def set_signature(self, sig: bytes):
        """Set the signature to return on next sign() call."""
        self._signature = sig

    def sign(self, nonce: int, day: int) -> bytes | None:
        """Return pre-configured signature."""
        return self._signature
