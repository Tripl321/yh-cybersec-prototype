from pathlib import Path


OVERLAY = Path("shallot-infra/compose.wazuh-tls.override.yml")
TEXT = OVERLAY.read_text(encoding="utf-8")
BASE = Path("shallot-infra/compose.wazuh.yml")
BASE_TEXT = BASE.read_text(encoding="utf-8")
CONFIG = Path("shallot-infra/config/wazuh_indexer/opensearch.yml")
CONFIG_LINES = [
    line for line in CONFIG.read_text(encoding="utf-8").splitlines()
    if not line.lstrip().startswith("#")
]
CONFIG_TEXT = "\n".join(CONFIG_LINES)


def test_overlay_stages_through_wrapper_instead_of_cert_mounts():
    assert "wazuh-indexer-runtime-wrapper.sh" in TEXT
    assert "/etc/wazuh-indexer/certs:" not in TEXT
    assert "/usr/share/wazuh-indexer/certs:" not in TEXT


def test_overlay_requires_explicit_input_directory():
    assert "SHALLOT_WAZUH_TLS_INPUT_DIR:?SHALLOT_WAZUH_TLS_INPUT_DIR is required" in TEXT
    assert "target: /run/wazuh-tls-input" in TEXT
    assert "read_only: true" in TEXT


def test_overlay_runs_wrapper_with_keepid_userns():
    assert "userns_mode: keep-id" in TEXT
    assert 'user: "0:0"' not in TEXT
    assert "cap_add" not in TEXT
    assert "- WAZUH_TLS_INPUT_DIR=/run/wazuh-tls-input" in TEXT


def test_overlay_mounts_corrected_opensearch_yml():
    assert "source: ./config/wazuh_indexer/opensearch.yml" in TEXT
    assert "target: /usr/share/wazuh-indexer/opensearch.yml" in TEXT


def test_overlay_drops_inert_ssl_environment_settings():
    assert "plugins.security.ssl." not in TEXT


def test_overlay_contains_no_key_material():
    assert "PRIVATE KEY" not in TEXT
    allowed = ("indexer-key.pem", "admin-key.pem", "filebeat.key")
    stripped = TEXT
    for name in allowed:
        stripped = stripped.replace(name, "")
    assert ".key" not in stripped


def test_config_uses_path_conf_certificate_directory():
    for name in ("indexer.pem", "indexer-key.pem", "root-ca.pem"):
        assert f"/usr/share/wazuh-indexer/certs/{name}" in CONFIG_TEXT
    assert "/etc/wazuh-indexer" not in CONFIG_TEXT


def test_config_is_single_node_without_initial_master_nodes():
    assert "discovery.type: single-node" in CONFIG_TEXT
    assert "initial_master_nodes" not in CONFIG_TEXT


def test_config_allows_default_security_index_init():
    assert "plugins.security.allow_default_init_securityindex: true" in CONFIG_TEXT


def test_config_contains_no_secrets():
    assert "PRIVATE KEY" not in CONFIG_TEXT
    assert "password" not in CONFIG_TEXT.lower()


def test_config_dn_matches_lab_ca():
    assert 'CN=admin,O=SHALLOT Local Lab,C=SE' in CONFIG_TEXT
    assert 'CN=wazuh-indexer.local,O=SHALLOT Local Lab,C=SE' in CONFIG_TEXT
    assert "OU=Wazuh" not in CONFIG_TEXT


def test_manager_uses_official_filebeat_environment_contract():
    assert "INDEXER_URL=https://wazuh-indexer.local:9200" in TEXT
    assert "FILEBEAT_SSL_VERIFICATION_MODE=full" in TEXT
    assert "SSL_CERTIFICATE_AUTHORITIES=/etc/ssl/root-ca.pem" in TEXT
    assert "SSL_CERTIFICATE=/etc/ssl/filebeat.pem" in TEXT
    assert "SSL_KEY=/etc/ssl/filebeat.key" in TEXT


def test_manager_mounts_filebeat_material_from_input_directory():
    prefix = "source: ${SHALLOT_WAZUH_TLS_INPUT_DIR:?SHALLOT_WAZUH_TLS_INPUT_DIR is required}"
    assert f"{prefix}/root-ca.pem" in TEXT
    assert f"{prefix}/filebeat/filebeat.pem" in TEXT
    assert f"{prefix}/filebeat/filebeat-key.pem" in TEXT
    assert "target: /etc/ssl/root-ca.pem" in TEXT
    assert "target: /etc/ssl/filebeat.pem" in TEXT
    assert "target: /etc/ssl/filebeat.key" in TEXT


def test_manager_keeps_hostname_and_certificate_verification():
    assert "VERIFICATION_MODE=none" not in TEXT
    assert "verify_certs: false" not in TEXT
    assert "SSL_VERIFICATION_MODE=none" not in TEXT


def test_indexer_alias_makes_certificate_name_resolvable():
    assert "aliases:" in BASE_TEXT
    assert "- wazuh-indexer.local" in BASE_TEXT


def test_plain_baseline_stays_plain_http():
    assert "INDEXER_URL=http://wazuh-indexer:9200" in BASE_TEXT
    assert "FILEBEAT_SSL_VERIFICATION_MODE" not in BASE_TEXT


def test_overlay_contains_no_manager_key_material():
    assert "PRIVATE KEY" not in TEXT
