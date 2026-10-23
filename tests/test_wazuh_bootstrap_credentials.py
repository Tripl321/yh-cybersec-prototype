import importlib.util
from pathlib import Path


SCRIPT = Path("ansible/scripts/bootstrap_wazuh_credentials.py")
OVERLAY = Path("shallot-infra/compose.wazuh-tls.override.yml")


def _definitions() -> dict:
    spec = importlib.util.spec_from_file_location("bootstrap_wazuh_credentials", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.USER_DEFINITIONS


def test_bootstrap_generates_the_filebeat_password_the_overlay_requires():
    overlay = OVERLAY.read_text(encoding="utf-8")
    assert ":?WAZUH_FILEBEAT_PASSWORD is required" in overlay
    definitions = _definitions()
    assert definitions["filebeat"]["env"] == "WAZUH_FILEBEAT_PASSWORD"


def test_bootstrap_env_covers_every_password_the_overlay_requires():
    overlay = OVERLAY.read_text(encoding="utf-8")
    definitions = _definitions()
    generated = {metadata["env"] for metadata in definitions.values()}
    for line in overlay.splitlines():
        if "PASSWORD" in line and "is required}" in line:
            assert line.split("${")[1].split(":?")[0] in generated
