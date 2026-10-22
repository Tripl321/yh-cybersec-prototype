#!/usr/bin/env python3
"""Build a reproducible Wazuh agent tree from the pinned official package.

The tree holds the agent installation and its enrollment key, so it must live
outside the repository. The agent payload is the whole official package: the
lab tree that existed before this script was hand-picked and mixed binaries
from two agent versions (ADR 0018).
"""
from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import tempfile
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "shallot-infra" / "versions.yml"
TEMPLATE_PATH = ROOT / "shallot-infra" / "config" / "wazuh_agent" / "ossec.conf"
DEFAULT_TARGET = Path.home() / ".local" / "share" / "shallot" / "wazuh-agent"
IDENTITY_FILES = ("etc/client.keys", "etc/agent-name")


def package() -> dict:
    manifest = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    return manifest["packages"]["wazuh-agent"]


def unpack(rpm: Path, into: Path) -> None:
    """Unpack the RPM payload, which is a cpio archive."""
    if shutil.which("bsdtar"):
        subprocess.run(["bsdtar", "-xf", str(rpm), "-C", str(into)], check=True)
        return
    if shutil.which("rpm2cpio") and shutil.which("cpio"):
        with subprocess.Popen(["rpm2cpio", str(rpm)], stdout=subprocess.PIPE) as reader:
            subprocess.run(
                ["cpio", "-idm", "--quiet"], cwd=into, stdin=reader.stdout, check=True
            )
        return
    raise SystemExit("unpacking needs bsdtar (libarchive), or rpm2cpio and cpio")


def normalise(tree: Path) -> None:
    """The package ships directories without the execute bit, which only root
    can work around. The tree belongs to an unprivileged user, so fix it."""
    for root, dirs, _ in os.walk(tree, topdown=True):
        for name in dirs:
            os.chmod(os.path.join(root, name), 0o750)


def agent_name(target: Path) -> str:
    """One agent name per tree, so a re-prepared tree keeps its identity."""
    digest = hashlib.sha256(str(target).encode()).hexdigest()
    return f"shallot-agent-{digest[:8]}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=Path, default=DEFAULT_TARGET)
    parser.add_argument("--manager", default="wazuh")
    args = parser.parse_args()

    target = args.target.expanduser().resolve()
    if target == ROOT or ROOT in target.parents:
        raise SystemExit(f"agent tree must live outside the repository: {target}")

    spec = package()
    with urllib.request.urlopen(spec["url"]) as response:
        payload = response.read()
    digest = hashlib.sha256(payload).hexdigest()
    if digest != spec["sha256"]:
        raise SystemExit(f"agent package digest mismatch: {digest}")

    tree = target / "var" / "ossec"
    with tempfile.TemporaryDirectory() as work:
        rpm = Path(work) / "agent.rpm"
        rpm.write_bytes(payload)
        unpacked = Path(work) / "unpacked"
        unpacked.mkdir()
        unpack(rpm, unpacked)
        source = unpacked / "var" / "ossec"
        if not source.is_dir():
            raise SystemExit("agent package did not contain var/ossec")
        normalise(source)
        # The enrollment key and the agent name survive a re-prepare, so the
        # manager keeps one agent identity for this tree.
        identity = {}
        for name in IDENTITY_FILES:
            if not (tree / name).exists():
                continue
            try:
                identity[name] = (tree / name).read_bytes()
            except OSError as error:
                raise SystemExit(f"cannot read {tree / name}: {error}") from error
        tree.parent.mkdir(parents=True, exist_ok=True)
        if tree.exists():
            # The agent writes into the tree and some of those files are not
            # owned by the host user, so replace the tree instead of writing
            # over it.
            shutil.rmtree(tree)
        shutil.copytree(source, tree)

    for name, content in identity.items():
        (tree / name).write_bytes(content)
    (tree / "etc" / "ossec.conf").write_text(
        TEMPLATE_PATH.read_text(encoding="utf-8").replace(
            "{{MANAGER_ADDRESS}}", args.manager
        ),
        encoding="utf-8",
    )
    name_file = tree / "etc" / "agent-name"
    if not name_file.exists():
        name_file.write_text(f"{agent_name(target)}\n", encoding="utf-8")
    # The enrollment key is a secret: it stays readable by its owner only.
    (tree / "etc" / "client.keys").chmod(0o600)

    # The lab's event file lives next to the tree, not inside it, so a
    # re-prepare does not drop the events and the host user keeps writing to
    # it while the agent reads it read-only.
    lab = target / "lab"
    lab.mkdir(parents=True, exist_ok=True)
    events = lab / "events.json"
    if not events.exists():
        events.touch()

    print(f"agent tree ready: {tree} (agent {name_file.read_text().strip()})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
