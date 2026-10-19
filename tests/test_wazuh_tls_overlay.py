from pathlib import Path


OVERLAY = Path("shallot-infra/compose.wazuh-tls.override.yml")
TEXT = OVERLAY.read_text(encoding="utf-8")


def test_overlay_stages_through_wrapper_instead_of_cert_mounts():
    assert "wazuh-indexer-runtime-wrapper.sh" in TEXT
    assert "/etc/wazuh-indexer/certs:" not in TEXT
    assert "/usr/share/wazuh-indexer/certs:" not in TEXT


def test_overlay_requires_explicit_input_directory():
    assert "SHALLOT_WAZUH_TLS_INPUT_DIR:?SHALLOT_WAZUH_TLS_INPUT_DIR is required" in TEXT
    assert "target: /run/wazuh-tls-input" in TEXT
    assert "read_only: true" in TEXT


def test_overlay_starts_wrapper_as_root():
    assert 'user: "0:0"' in TEXT
    assert "- WAZUH_TLS_INPUT_DIR=/run/wazuh-tls-input" in TEXT


def test_overlay_contains_no_key_material():
    assert "PRIVATE KEY" not in TEXT
    assert ".key" not in TEXT.replace("indexer-key.pem", "").replace("admin-key.pem", "")
