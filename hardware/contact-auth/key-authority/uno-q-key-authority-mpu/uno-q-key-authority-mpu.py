# SHALLOT — UNO Q Key Authority MPU Script (PRO-45 + PRO-46)
#
# Linux side: Qualcomm QRB2210 (Debian) via Arduino App Lab
# Role: orchestration UI, audit log, and validation. Never handles key material.

import json
import os
import time
from datetime import datetime

from arduino.app_utils import App, Bridge

AUDIT_LOG_PATH = "/home/user/shallot/audit/provisioning_log.jsonl"
AUDIT_DIR = os.path.dirname(AUDIT_LOG_PATH)

TARGET_NAMES = {
    1: "PLC (edge enforcement)",
    2: "PAW (ID-bricka)",
}

STATE_NAMES = {
    0: "UNINITIALIZED",
    1: "GENERATED",
    2: "DISTRIBUTED_PLC",
    3: "DISTRIBUTED_PAW",
    4: "DISTRIBUTED_BOTH",
    0xFF: "ERROR",
}


def ensure_audit_dir():
    """Create audit log directory if it does not exist."""
    if not os.path.exists(AUDIT_DIR):
        os.makedirs(AUDIT_DIR)


def write_audit_log(event_type, details):
    """Append a JSON line containing status metadata, never key material."""
    ensure_audit_dir()
    entry = {
        "timestamp": datetime.now().isoformat(),
        "event": event_type,
        "details": details,
    }
    with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as audit_file:
        audit_file.write(json.dumps(entry) + "\n")
    print(f"[AUDIT] {entry['timestamp']} | {event_type} | {details}")


def on_key_authority_event(event, message):
    """Handle status-only notifications from the MCU."""
    print(f"[MCU EVENT] {event}: {message}")
    write_audit_log(event, {"message": message})


def get_key_state():
    """Query the MCU for current key state via Bridge RPC."""
    state = Bridge.call("get_key_state")
    state_name = STATE_NAMES.get(state, "UNKNOWN")
    print(f"[STATUS] Key state: {state_name} (0x{state:02X})")
    return state


def get_key_fingerprint():
    """Query the MCU for the non-secret key fingerprint."""
    fingerprint = Bridge.call("get_key_fingerprint")
    print(f"[STATUS] Key fingerprint: {fingerprint}")
    return fingerprint


def request_key_generation():
    """Request hardware-backed AES key generation on the MCU."""
    print("[ORCHESTRATION] Requesting key generation on MCU...")
    success = Bridge.call("request_key_generation")
    if success:
        print("[ORCHESTRATION] Key generation successful.")
        fingerprint = get_key_fingerprint()
        write_audit_log(
            "key_generation_requested",
            {"result": "success", "fingerprint": fingerprint},
        )
    else:
        print("[ORCHESTRATION] Key generation FAILED.")
        write_audit_log("key_generation_requested", {"result": "failure"})
    return success


def request_key_distribution(target_id):
    """Arm MCU distribution to a target; physical confirmation remains required."""
    target_name = TARGET_NAMES.get(target_id, f"Unknown({target_id})")
    print(f"[ORCHESTRATION] Requesting key distribution to {target_name}.")
    print("[ORCHESTRATION] Operator must press confirmation button on UNO Q.")

    success = Bridge.call("request_key_distribution", target_id)
    if not success:
        print(f"[ORCHESTRATION] Failed to arm distribution to {target_name}.")
        return False

    write_audit_log("distribution_armed", {"target": target_name})
    print(f"[ORCHESTRATION] Distribution to {target_name} armed.")

    max_wait = 30
    start = time.time()
    while time.time() - start < max_wait:
        time.sleep(1)
        state = get_key_state()
        if target_id == 1 and state in (2, 4):
            print(f"[ORCHESTRATION] Distribution to {target_name} confirmed.")
            write_audit_log("distribution_confirmed", {"target": target_name})
            return True
        if target_id == 2 and state in (3, 4):
            print(f"[ORCHESTRATION] Distribution to {target_name} confirmed.")
            write_audit_log("distribution_confirmed", {"target": target_name})
            return True

    print(f"[ORCHESTRATION] Timeout waiting for {target_name} distribution.")
    write_audit_log("distribution_timeout", {"target": target_name})
    return False


def validate_provisioning():
    """Validate distributed state and availability of a key fingerprint."""
    print("\n=== VALIDATION ===")
    state = get_key_state()
    if state != 4:
        state_name = STATE_NAMES.get(state, "UNKNOWN")
        print(f"[VALIDATION] Key state: {state_name} — INCOMPLETE")
        return False
    print("[VALIDATION] Key state: DISTRIBUTED_BOTH — OK")

    fingerprint = get_key_fingerprint()
    if not fingerprint or len(fingerprint) != 8:
        print(f"[VALIDATION] Key fingerprint: {fingerprint} — INVALID")
        return False
    print(f"[VALIDATION] Key fingerprint: {fingerprint} — OK")

    write_audit_log(
        "validation",
        {
            "result": "pass",
            "state": "DISTRIBUTED_BOTH",
            "fingerprint": fingerprint,
        },
    )
    print("[VALIDATION] All checks passed.")
    print("===================\n")
    return True


def print_menu():
    """Print the operator menu."""
    print("\n=== SHALLOT UNO Q — Orchestration (MPU) ===")
    print("  1 — Generate new AES-128 key (MCU TRNG)")
    print("  2 — Distribute key to PLC (edge enforcement)")
    print("  3 — Distribute key to PAW (ID-bricka)")
    print("  4 — Query key state")
    print("  5 — Show key fingerprint")
    print("  6 — Validate provisioning (both nodes)")
    print("  7 — Print audit log")
    print("  q — Quit")
    print("===========================================\n")


def print_audit_log():
    """Print the local status-only audit log."""
    if not os.path.exists(AUDIT_LOG_PATH):
        print("[AUDIT] No audit log file found.")
        return
    print("\n=== AUDIT LOG ===")
    with open(AUDIT_LOG_PATH, "r", encoding="utf-8") as audit_file:
        for line in audit_file:
            entry = json.loads(line.strip())
            timestamp = entry.get("timestamp", "?")
            event = entry.get("event", "?")
            details = entry.get("details", {})
            print(f"  {timestamp} | {event} | {details}")
    print("==================\n")


def loop():
    """Run the local operator menu."""
    print_menu()
    while True:
        command = input("Select option: ").strip().lower()
        if command == "1":
            request_key_generation()
        elif command == "2":
            request_key_distribution(1)
        elif command == "3":
            request_key_distribution(2)
        elif command == "4":
            get_key_state()
        elif command == "5":
            get_key_fingerprint()
        elif command == "6":
            validate_provisioning()
        elif command == "7":
            print_audit_log()
        elif command == "q":
            print("Exiting.")
            break
        else:
            print("Unknown option.")


Bridge.provide("key_authority_event", on_key_authority_event)
App.run(user_loop=loop)
