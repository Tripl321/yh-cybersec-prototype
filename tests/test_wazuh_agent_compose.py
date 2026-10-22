import subprocess
import sys
from pathlib import Path

import yaml

OVERLAY = Path("shallot-infra/compose.wazuh-agent.override.yml")
TEXT = OVERLAY.read_text(encoding="utf-8")
SERVICE = yaml.safe_load(TEXT)["services"]["wazuh-agent"]
MANIFEST = yaml.safe_load(Path("shallot-infra/versions.yml").read_text(encoding="utf-8"))
TEMPLATE = Path("shallot-infra/config/wazuh_agent/ossec.conf").read_text(encoding="utf-8")
PREPARE = Path("ansible/scripts/prepare_wazuh_agent.py").read_text(encoding="utf-8")
ENTRYPOINT = Path("ansible/scripts/wazuh-agent-entrypoint.sh").read_text(encoding="utf-8")


def test_agent_runs_the_pinned_manager_image():
    assert SERVICE["image"] == MANIFEST["images"]["wazuh-agent"]["reference"]
    assert "@sha256:" in SERVICE["image"]


def test_agent_is_gated_by_the_secure_profile():
    assert SERVICE["profiles"] == ["wazuh-secure"]
    assert "wazuh-agent" not in yaml.safe_load(
        Path("shallot-infra/compose.yml").read_text(encoding="utf-8")
    )["services"]


def test_agent_runs_in_the_install_directory():
    assert SERVICE["working_dir"] == "/var/ossec"


def test_agent_tree_directory_is_mandatory():
    sources = [mount["source"] for mount in SERVICE["volumes"]]
    assert any(
        "SHALLOT_WAZUH_AGENT_DIR:?" in source for source in sources
    ), "the agent tree must not default to a path"


def test_agent_mounts_the_entrypoint_and_uid_fix_read_only():
    mounts = {mount["target"]: mount for mount in SERVICE["volumes"]}
    assert mounts["/opt/shallot/wazuh-agent-entrypoint.sh"]["read_only"] is True
    assert mounts["/opt/shallot/0-wazuh-uid.sh"]["read_only"] is True


def test_agent_tree_carries_the_whole_payload():
    mounts = {mount["target"]: mount for mount in SERVICE["volumes"]}
    assert mounts["/var/ossec"]["source"].endswith("/var/ossec")
    assert mounts["/var/ossec"].get("read_only") is not True


def test_agent_package_is_pinned():
    package = MANIFEST["packages"]["wazuh-agent"]
    assert package["url"] == (
        "https://packages.wazuh.com/4.x/yum/wazuh-agent-4.9.0-1.x86_64.rpm"
    )
    assert package["sha256"] == (
        "13c8ec9bf3cdb22be4e0a498d3e2cb712b7cc0f60a91c9527dde59885e576e4d"
    )


def test_prepare_script_reads_the_pin_from_the_manifest():
    assert "13c8ec9bf3cdb22be4e0a498d3e2cb712b7cc0f60a91c9527dde59885e576e4d" not in PREPARE
    assert 'manifest["packages"]["wazuh-agent"]' in PREPARE


def test_prepare_script_refuses_a_tree_inside_the_repository():
    result = subprocess.run(
        [
            sys.executable,
            "ansible/scripts/prepare_wazuh_agent.py",
            "--target",
            "shallot-infra/agent-tree",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "outside the repository" in result.stderr


def test_template_carries_the_manager_address_placeholder():
    assert "{{MANAGER_ADDRESS}}" in TEMPLATE
    assert "127.0.0.1" not in TEMPLATE
    assert "<use_password>no</use_password>" in TEMPLATE


def test_entrypoint_enrolls_only_without_a_key():
    assert "if [ ! -s /var/ossec/etc/client.keys ]; then" in ENTRYPOINT
    assert "/var/ossec/bin/agent-auth" in ENTRYPOINT
    assert "/var/ossec/etc/agent-name" in ENTRYPOINT
    assert "exec /var/ossec/bin/wazuh-agentd -f" in ENTRYPOINT


def test_uid_fix_does_not_depend_on_the_working_directory():
    script = Path("shallot-infra/scripts/0-wazuh-uid.sh").read_text(encoding="utf-8")
    assert '$7 == "/bin/sh"' in script
    assert '$6 == "/"' not in script


def test_agent_collects_the_lab_events():
    assert "<log_format>json</log_format>" in TEMPLATE
    assert "<location>/opt/shallot/lab/events.json</location>" in TEMPLATE


def test_agent_reads_the_lab_events_read_only():
    mounts = {mount["target"]: mount for mount in SERVICE["volumes"]}
    lab = mounts["/opt/shallot/lab"]
    assert lab["source"].endswith("/lab")
    assert lab["read_only"] is True


def test_prepare_script_creates_the_lab_event_file():
    assert '"lab"' in PREPARE
    assert 'events = lab / "events.json"' in PREPARE
