#!/usr/bin/env python3
"""Validate immutable SHALLOT image and secret-policy declarations."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
BASE_COMPOSE_PATH = ROOT / "shallot-infra" / "compose.yml"
WAZUH_COMPOSE_PATH = ROOT / "shallot-infra" / "compose.wazuh.yml"
MANIFEST_PATH = ROOT / "shallot-infra" / "versions.yml"
GITIGNORE_PATH = ROOT / "shallot-infra" / ".gitignore"
DIGEST_RE = re.compile(r"@sha256:[0-9a-f]{64}$")


def _services(path: Path) -> dict:
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    return document.get("services", {})


def validate() -> list[str]:
    errors: list[str] = []
    base_text = BASE_COMPOSE_PATH.read_text(encoding="utf-8")
    wazuh_text = WAZUH_COMPOSE_PATH.read_text(encoding="utf-8")
    base_services = _services(BASE_COMPOSE_PATH)
    wazuh_services = _services(WAZUH_COMPOSE_PATH)
    services = {**base_services, **wazuh_services}
    manifest = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))

    if {"wazuh", "wazuh-indexer"} & set(base_services):
        errors.append("Wazuh services must not exist in the default Compose file")
    if "WAZUH_INDEXER_PASSWORD" in base_text:
        errors.append("Default Compose file unexpectedly depends on a Wazuh secret")

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
        errors.append("Compose image references do not exactly match versions.yml")

    for service, reference in actual.items():
        if not DIGEST_RE.search(reference):
            errors.append(f"{service} image is not pinned by sha256 digest: {reference}")
        if ":latest" in reference:
            errors.append(f"{service} image uses mutable latest tag: {reference}")

    if "INDEXER_PASSWORD=admin" in wazuh_text:
        errors.append("Wazuh overlay contains the known indexer default password")

    wazuh = wazuh_services.get("wazuh", {})
    required_password = (
        "INDEXER_PASSWORD=${WAZUH_INDEXER_PASSWORD:?"
        "WAZUH_INDEXER_PASSWORD is required}"
    )
    if "wazuh-secure" not in wazuh.get("profiles", []):
        errors.append("Wazuh manager is not gated by the wazuh-secure profile")
    if required_password not in wazuh.get("environment", []):
        errors.append("Wazuh manager does not require local password injection")

    indexer = wazuh_services.get("wazuh-indexer", {})
    if "wazuh-secure" not in indexer.get("profiles", []):
        errors.append("Wazuh indexer is not gated by the wazuh-secure profile")
    internal_users_mount = (
        "./config/wazuh_indexer/internal_users.local.yml:"
        "/usr/share/wazuh-indexer/opensearch-security/internal_users.yml:ro"
    )
    if internal_users_mount not in indexer.get("volumes", []):
        errors.append("Wazuh indexer lacks the local internal_users mount")

    if "latitude" in services:
        errors.append("Unsupported single-image Latitude service remains enabled")
    if "latitude" not in manifest.get("blocked_components", {}):
        errors.append("Latitude removal is not documented in versions.yml")

    gitignore = set(GITIGNORE_PATH.read_text(encoding="utf-8").splitlines())
    for required_entry in {
        ".env",
        "config/wazuh_indexer/internal_users.local.yml",
    }:
        if required_entry not in gitignore:
            errors.append(f"Sensitive local file is not git-ignored: {required_entry}")

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
