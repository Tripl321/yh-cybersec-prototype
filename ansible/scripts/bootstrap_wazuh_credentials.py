#!/usr/bin/env python3
"""Generate local Wazuh credentials without printing secret material."""
from __future__ import annotations

import argparse
import os
import re
import secrets
import shutil
import subprocess
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "shallot-infra" / "versions.yml"
ENV_PATH = ROOT / "shallot-infra" / ".env"
INTERNAL_USERS_PATH = (
    ROOT
    / "shallot-infra"
    / "config"
    / "wazuh_indexer"
    / "internal_users.local.yml"
)
BCRYPT_RE = re.compile(r"\$2[aby]\$[0-9]{2}\$[./A-Za-z0-9]{53}")
HASH_TOOL = "/usr/share/wazuh-indexer/plugins/opensearch-security/tools/hash.sh"

USER_DEFINITIONS = {
    "admin": {
        "env": "WAZUH_INDEXER_PASSWORD",
        "reserved": True,
        "backend_roles": ["admin"],
        "description": "SHALLOT indexer administrator",
    },
    "kibanaserver": {
        "env": "WAZUH_KIBANASERVER_PASSWORD",
        "reserved": True,
        "description": "SHALLOT dashboard service user",
    },
    "kibanaro": {
        "env": "WAZUH_KIBANARO_PASSWORD",
        "reserved": False,
        "backend_roles": ["kibanauser", "readall"],
        "description": "SHALLOT read-only dashboard user",
    },
    "logstash": {
        "env": "WAZUH_LOGSTASH_PASSWORD",
        "reserved": False,
        "backend_roles": ["logstash"],
        "description": "SHALLOT log ingestion user",
    },
    "readall": {
        "env": "WAZUH_READALL_PASSWORD",
        "reserved": False,
        "backend_roles": ["readall"],
        "description": "SHALLOT read-all user",
    },
    "snapshotrestore": {
        "env": "WAZUH_SNAPSHOTRESTORE_PASSWORD",
        "reserved": False,
        "backend_roles": ["snapshotrestore"],
        "description": "SHALLOT snapshot and restore user",
    },
}


def fail(message: str) -> None:
    raise RuntimeError(message)


def image_reference() -> str:
    manifest = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    reference = manifest["images"]["wazuh-indexer"]["reference"]
    if not re.search(r"@sha256:[0-9a-f]{64}$", reference):
        fail("Wazuh indexer image is not digest-pinned")
    return reference


def preflight() -> str:
    if shutil.which("podman") is None:
        fail("Podman is required for the local Wazuh hash tool")
    if ENV_PATH.exists() or INTERNAL_USERS_PATH.exists():
        fail("Wazuh credential files already exist; rotation is a separate operation")
    return image_reference()


def ensure_image(reference: str, allow_pull: bool) -> None:
    present = subprocess.run(
        ["podman", "image", "exists", reference],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode == 0
    if present:
        return
    if not allow_pull:
        fail("Pinned Wazuh indexer image is absent; explicit --allow-pull is required")
    subprocess.run(
        ["podman", "pull", reference],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def hash_password(reference: str, password: str) -> str:
    environment = os.environ.copy()
    environment["SHALLOT_WAZUH_PASSWORD"] = password
    command = [
        "podman",
        "run",
        "--rm",
        "--network=none",
        "--cap-drop=all",
        "--security-opt=no-new-privileges",
        "--pids-limit=64",
        "--env",
        "SHALLOT_WAZUH_PASSWORD",
        "--entrypoint",
        "bash",
        reference,
        "-lc",
        f'test -x {HASH_TOOL} && exec {HASH_TOOL} -p "$SHALLOT_WAZUH_PASSWORD"',
    ]
    result = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        env=environment,
    )
    match = BCRYPT_RE.search(result.stdout + result.stderr)
    if match is None:
        fail("Wazuh hash tool did not return a valid bcrypt hash")
    return match.group(0)


def render_files(reference: str) -> tuple[str, str]:
    passwords = {
        user: secrets.token_urlsafe(32)
        for user in USER_DEFINITIONS
    }
    hashes = {
        user: hash_password(reference, password)
        for user, password in passwords.items()
    }

    env_text = "".join(
        f"{metadata['env']}={passwords[user]}\n"
        for user, metadata in USER_DEFINITIONS.items()
    )

    internal_users: dict = {
        "_meta": {"type": "internalusers", "config_version": 2}
    }
    for user, metadata in USER_DEFINITIONS.items():
        entry = {
            "hash": hashes[user],
            "reserved": metadata["reserved"],
        }
        if "backend_roles" in metadata:
            entry["backend_roles"] = metadata["backend_roles"]
        entry["description"] = metadata["description"]
        internal_users[user] = entry

    users_text = yaml.safe_dump(internal_users, sort_keys=False)
    return env_text, users_text


def stage_file(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary_path = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise
    return temporary_path


def write_atomically(env_text: str, users_text: str) -> None:
    env_temp = stage_file(ENV_PATH, env_text)
    users_temp = stage_file(INTERNAL_USERS_PATH, users_text)
    created: list[Path] = []
    try:
        os.replace(env_temp, ENV_PATH)
        created.append(ENV_PATH)
        os.replace(users_temp, INTERNAL_USERS_PATH)
        created.append(INTERNAL_USERS_PATH)
        os.chmod(ENV_PATH, 0o600)
        os.chmod(INTERNAL_USERS_PATH, 0o600)
    except Exception:
        env_temp.unlink(missing_ok=True)
        users_temp.unlink(missing_ok=True)
        for path in created:
            path.unlink(missing_ok=True)
        raise


def execute(allow_pull: bool) -> None:
    reference = preflight()
    ensure_image(reference, allow_pull)
    env_text, users_text = render_files(reference)
    write_atomically(env_text, users_text)
    print("Wazuh credential files created with mode 0600; secret values were not displayed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--allow-pull", action="store_true")
    args = parser.parse_args()

    if args.execute:
        execute(args.allow_pull)
    else:
        preflight()
        print("Wazuh credential bootstrap preflight: PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Wazuh credential bootstrap blocked: {exc}")
        raise SystemExit(1) from None
