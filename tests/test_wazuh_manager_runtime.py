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
