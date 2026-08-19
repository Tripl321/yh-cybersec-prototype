"""ShallotRadio — SX1262 abstraction for SHALLOT.

Board-agnostic. Takes resolved pin objects from hardware_pins.load_pins().
Uses adafruit-circuitpython-sx1262 under the hood.
All encoding via struct.pack / struct.unpack. No JSON. No text.
"""

import struct
from constants import (
    MSG_BEACON, MSG_AUTH,
    BEACON_FMT, BEACON_SIZE,
    AUTH_FMT, AUTH_SIZE,
    LORA_FREQUENCY_MHZ, LORA_TX_POWER_DBM,
    LORA_SPREAD_FACTOR, LORA_BANDWIDTH_HZ, LORA_CODING_RATE,
)


class ShallotRadio:
    """Abstraction over Core1262-HF (SX1262) for SHALLOT.

    Parameters are resolved pin objects (from board.* or board.GP**),
    not raw strings.
    """

    def __init__(self, spi, cs, rst, irq, busy,
                 frequency_mhz=LORA_FREQUENCY_MHZ,
                 tx_power_dbm=LORA_TX_POWER_DBM):
        from adafruit_sx1262 import SX1262

        self._radio = SX1262(
            spi, cs, reset=rst,
            dio1=irq, busy=busy,
        )
        self._radio.configured = False
        self._radio.frequency = frequency_mhz
        self._radio.tx_power = tx_power_dbm
        self._radio.spreading_factor = LORA_SPREAD_FACTOR
        self._radio.signal_bandwidth = LORA_BANDWIDTH_HZ
        self._radio.coding_rate = LORA_CODING_RATE
        self._radio.configured = True

    # ── Send ───────────────────────────────────────────────────

    def send_beacon(self, node_id: bytes, timestamp: int, nonce: int):
        """Transmit a 13-byte beacon frame.

        node_id must be exactly 4 bytes (e.g. b'FN01').
        """
        packet = struct.pack(BEACON_FMT, MSG_BEACON, node_id, timestamp, nonce)
        self._radio.send(packet)

    def send_auth(self, badge_id: bytes, nonce: int, day: int, signature: bytes):
        """Transmit a 45-byte auth request frame.

        badge_id  — exactly 4 bytes (e.g. b'PAW1').
        nonce     — from the beacon being responded to.
        day       — current day number for epoch check.
        signature — exactly 32 bytes (HMAC-SHA256 over badge_id+nonce+day).
        """
        packet = struct.pack(AUTH_FMT, MSG_AUTH, badge_id, nonce, day, signature)
        self._radio.send(packet)

    # ── Receive ────────────────────────────────────────────────

    def receive(self):
        """Non-blocking receive. Returns (msg_type, data_dict, rssi) or None.

        msg_type  — MSG_BEACON or MSG_AUTH
        data_dict — unpacked fields (see constants.unpack_*)
        rssi      — received signal strength in dBm
        """
        packet = self._radio.receive(timeout=0)
        if packet is None or len(packet) == 0:
            return None

        msg_type = packet[0]
        rssi = self._radio.rssi

        if msg_type == MSG_BEACON and len(packet) == BEACON_SIZE:
            data = struct.unpack(BEACON_FMT, packet)
            return (MSG_BEACON, {
                "node_id": data[1],
                "timestamp": data[2],
                "nonce": data[3],
            }, rssi)

        if msg_type == MSG_AUTH and len(packet) == AUTH_SIZE:
            data = struct.unpack(AUTH_FMT, packet)
            return (MSG_AUTH, {
                "badge_id": data[1],
                "nonce": data[2],
                "day": data[3],
                "signature": data[4],
            }, rssi)

        return None
