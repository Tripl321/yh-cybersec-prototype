"""USB device detection using pyserial."""

from __future__ import annotations

import re
from dataclasses import dataclass

from serial.tools.list_ports import comports
from serial.tools.list_ports_common import ListPortInfo


# Known USB vendor/product IDs for SHALLOT hardware
KNOWN_DEVICES: dict[tuple[int, int], dict[str, str]] = {
    # Espressif ESP32-S3
    (0x303A, 0x1001): {"type": "esp32", "name": "ESP32-S3"},
    (0x303A, 0x0002): {"type": "esp32", "name": "ESP32-S3"},
    # Raspberry Pi Pico / RP2350
    (0x2E8A, 0x000A): {"type": "pico", "name": "RP2350"},
    (0x2E8A, 0x0003): {"type": "pico", "name": "RP2040"},
    (0x2E8A, 0x000C): {"type": "pico", "name": "RP2350"},
    # Arduino
    (0x2341, 0x0057): {"type": "arduino", "name": "Arduino UNO R4"},
    (0x2341, 0x0042): {"type": "arduino", "name": "Arduino Mega 2560"},
    (0x2341, 0x0001): {"type": "arduino", "name": "Arduino Uno"},
    # FTDI (common USB-serial adapter)
    (0x0403, 0x6001): {"type": "unknown", "name": "FTDI Adapter"},
}

# Fallback: match by port name pattern (Linux/macOS)
PORT_PATTERNS: list[tuple[str, str, str]] = [
    (r"ttyUSB\d", "esp32", "USB Serial Device"),
    (r"ttyACM\d", "pico", "Pico Device"),
    (r"cu\.usbmodem", "esp32", "ESP32"),
    (r"cu\.usbserial", "pico", "Serial Device"),
]


@dataclass
class ScannedDevice:
    id: str
    name: str
    type: str  # esp32 | pico | arduino | unknown
    port: str
    vendor_id: int | None = None
    product_id: int | None = None
    flashable: bool = True


def _device_id(port: ListPortInfo) -> str:
    """Generate a stable device ID from port info."""
    if port.vid and port.pid:
        return f"{port.vid:04x}-{port.pid:04x}-{port.device}"
    return port.device


def _identify(port: ListPortInfo) -> tuple[str, str]:
    """Identify device type and name from USB IDs or port pattern matching."""
    if port.vid and port.pid:
        key = (port.vid, port.pid)
        if key in KNOWN_DEVICES:
            info = KNOWN_DEVICES[key]
            return info["type"], info["name"]

    # Fallback to port name pattern matching
    port_name = port.device.split("/")[-1]
    for pattern, dev_type, dev_name in PORT_PATTERNS:
        if re.search(pattern, port_name):
            return dev_type, dev_name

    return "unknown", port.description or "Unknown Device"


def scan_usb() -> list[ScannedDevice]:
    """Scan for connected USB serial devices.

    Returns a list of ScannedDevice objects representing detected hardware.
    Filters out obvious non-hardware ports (debug ports, bluetooth, etc.).
    """
    devices: list[ScannedDevice] = []

    for port in comports():
        # Skip Bluetooth ports
        if "Bluetooth" in (port.description or ""):
            continue
        # Skip ports that look like debug/console bridges
        if "debug" in (port.description or "").lower():
            continue

        dev_type, dev_name = _identify(port)

        devices.append(
            ScannedDevice(
                id=_device_id(port),
                name=dev_name,
                type=dev_type,
                port=port.device,
                vendor_id=port.vid,
                product_id=port.pid,
                flashable=dev_type in ("esp32", "pico", "arduino"),
            )
        )

    return devices
