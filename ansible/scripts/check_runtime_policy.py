#!/usr/bin/env python3
"""Validate immutable SHALLOT image and secret-policy declarations."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
COMPOSE_PATH = ROOT / "shallot-infra" / "compose.yml"
MANIFEST_PATH = ROOT / "shallot-infra" / "versions.yml"
DIGEST_RE = re.compile(r"@sha256:[0-9a-f]{64}$")


def validate() -> list[str]:
    errors: list[str] = []
    compose_text = COMPOSE_PATH.read_text(encoding="utf-8")
    compose = yaml.safe_load(compose_text)
    manifest = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))

    services = compose.get("services", {})
    actual = {
        name: config["image"]
        for name, config in services.items()
        if isinstance(config, dict) and "image" in config
    }
    expected = {
        name: metadata["reference"]
        for name, metadata in manifest.get("images", {}).items()
    }

    if actual != expected:
        errors.append(
            "Compose image references do not exactly match shallot-infra/versions.yml"
        )

    for service, reference in actual.items():
        if not DIGEST_RE.search(reference):
            errors.append(f"{service} image is not pinned by sha256 digest: {reference}")
        if ":latest" in reference:
            errors.append(f"{service} image uses mutable latest tag: {reference}")

    if "INDEXER_PASSWORD=admin" in compose_text:
        errors.append("Compose contains the known Wazuh indexer default password")

    wazuh = services.get("wazuh", {})
    wazuh_profiles = wazuh.get("profiles", [])
    wazuh_environment = wazuh.get("environment", [])
    required_password = (
        "INDEXER_PASSWORD=${WAZUH_INDEXER_PASSWORD:?"
        "WAZUH_INDEXER_PASSWORD is required}"
    )
    if "wazuh-secure" not in wazuh_profiles:
        errors.append("Wazuh manager is not gated by the wazuh-secure profile")
    if required_password not in wazuh_environment:
        errors.append("Wazuh manager does not require local indexer password injection")

    indexer = services.get("wazuh-indexer", {})
    if "wazuh-secure" not in indexer.get("profiles", []):
        errors.append("Wazuh indexer is not gated by the wazuh-secure profile")
    internal_users_mount = (
        "./config/wazuh_indexer/internal_users.local.yml:"
        "/usr/share/wazuh-indexer/opensearch-security/internal_users.yml:ro"
    )
    if internal_users_mount not in indexer.get("volumes", []):
        errors.append("Wazuh indexer lacks the required local internal_users mount")

    if "latitude" in services:
        errors.append("Unsupported single-image Latitude service remains enabled")
    if "latitude" not in manifest.get("blocked_components", {}):
        errors.append("Latitude removal is not documented in the versions manifest")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    errors = validate()

    if args.json:
        print(json.dumps({"errors": errors}, sort_keys=True))
    elif errors:
        for error in errors:
            print(f"ERROR: {error}")
    else:
        print("Runtime image and secret policy: PASS")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
