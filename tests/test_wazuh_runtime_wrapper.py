from pathlib import Path


WRAPPER = Path("ansible/scripts/wazuh-indexer-runtime-wrapper.sh")
TEXT = WRAPPER.read_text(encoding="utf-8")


def test_wrapper_requires_explicit_input_directory():
    assert "WAZUH_TLS_INPUT_DIR:?WAZUH_TLS_INPUT_DIR is required" in TEXT


def test_wrapper_uses_image_certificate_layout():
    for name in ("root-ca.pem", "indexer.pem", "indexer-key.pem", "admin.pem", "admin-key.pem"):
        assert name in TEXT
    assert "CERT_ROOT=/usr/share/wazuh-indexer/certs" in TEXT
    assert "CERT_ROOT=/etc/wazuh-indexer/certs" not in TEXT


def test_wrapper_links_legacy_conf_into_path_conf():
    assert 'ln -s /usr/share/wazuh-indexer "$LEGACY_CONF"' in TEXT
    assert 'readlink -f "$LEGACY_CONF"' in TEXT


def test_wrapper_rejects_foreign_legacy_conf():
    assert "is not a symlink to /usr/share/wazuh-indexer" in TEXT
    assert TEXT.rfind("is not a symlink") < TEXT.rfind('exec "$WAZUH_ORIGINAL_ENTRYPOINT"')


def test_wrapper_never_logs_secret_contents():
    assert "cat \"$source\"" not in TEXT
    assert "echo \"$source\"" not in TEXT


def test_wrapper_stages_restrictive_modes_and_ownership():
    assert "[indexer-key.pem]=0600" in TEXT
    assert "[admin-key.pem]=0600" in TEXT
    assert "install -o 1000 -g 0" in TEXT


def test_wrapper_normalizes_stat_mode_output():
    assert 'expected="${FILES[$name]#0}"' in TEXT


def test_wrapper_executes_original_entrypoint_only_after_validation():
    assert TEXT.rfind("exec \"$WAZUH_ORIGINAL_ENTRYPOINT\"") > TEXT.rfind("unexpected mode")

def test_wrapper_uses_nested_admin_input_directory():
    assert 'WAZUH_TLS_INPUT_DIR/admin/$name' in TEXT
