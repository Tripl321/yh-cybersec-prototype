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
