from pathlib import Path


BASE = Path("shallot-infra/compose.wazuh.yml")
MANAGER = BASE.read_text(encoding="utf-8").split("  wazuh:")[1]


def test_manager_runs_with_keep_id_userns():
    assert "userns_mode: keep-id" in MANAGER


def test_manager_keeps_capabilities_the_image_init_needs():
    for capability in (
        "CHOWN",
        "SETUID",
        "SETGID",
        "DAC_OVERRIDE",
        "FOWNER",
        "SYS_CHROOT",
        "KILL",
    ):
        assert f"- {capability}" in MANAGER
    assert "cap_drop:\n      - ALL" in MANAGER


def test_manager_runs_uid_fix_from_cont_init():
    assert "source: ./scripts/0-wazuh-uid.sh" in MANAGER
    assert "target: /etc/cont-init.d/0-wazuh-uid.sh" in MANAGER


def test_uid_fix_script_is_executable():
    script = Path("shallot-infra/scripts/0-wazuh-uid.sh")
    assert script.exists()
    assert script.stat().st_mode & 0o111


def test_manager_seeds_the_default_group_before_the_daemons_start():
    assert "source: ./scripts/1-wazuh-group.sh" in MANAGER
    assert "target: /etc/cont-init.d/1-wazuh-group.sh" in MANAGER
    script = Path("shallot-infra/scripts/1-wazuh-group.sh")
    assert script.exists()
    assert script.stat().st_mode & 0o111
    text = script.read_text(encoding="utf-8")
    assert "global insert-agent-group default" in text
    # cont-init.d runs in name order: before 2-manager, which starts the daemons.
    assert script.name < "2-manager"


def test_manager_ships_the_lab_rule():
    assert "source: ./config/wazuh_manager/local_rules.xml" in MANAGER
    assert "target: /var/ossec/etc/rules/local_rules.xml" in MANAGER
    rules = Path("shallot-infra/config/wazuh_manager/local_rules.xml").read_text(
        encoding="utf-8"
    )
    assert "<decoded_as>json</decoded_as>" in rules
