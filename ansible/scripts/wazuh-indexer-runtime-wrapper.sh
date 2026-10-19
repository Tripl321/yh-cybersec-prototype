#!/usr/bin/env bash
set -euo pipefail

# Secret-free runtime wrapper prototype for the Wazuh indexer image.
# The secret input directory must be supplied explicitly at runtime.

: "${WAZUH_TLS_INPUT_DIR:?WAZUH_TLS_INPUT_DIR is required}"
: "${WAZUH_ORIGINAL_ENTRYPOINT:=/entrypoint.sh}"
# path.conf (/usr/share/wazuh-indexer) is the only certificate directory the
# OpenSearch SecurityManager grants read access to (ADR 0015).
CERT_ROOT=/usr/share/wazuh-indexer/certs
LEGACY_CONF=/etc/wazuh-indexer

declare -A FILES=(
  [root-ca.pem]=0644
  [indexer.pem]=0644
  [indexer-key.pem]=0600
  [admin.pem]=0644
  [admin-key.pem]=0600
)

if [[ "$(id -u)" != "0" ]]; then
  echo "wrapper must start as root to stage into the container-owned filesystem" >&2
  exit 1
fi

# The image default opensearch.yml references /etc/wazuh-indexer/certs.
# FilePermission compares canonical paths, so a symlink into path.conf keeps
# those references policy-readable without a policy change (ADR 0015).
if [[ ! -e "$LEGACY_CONF" ]]; then
  ln -s /usr/share/wazuh-indexer "$LEGACY_CONF"
elif [[ "$(readlink -f "$LEGACY_CONF")" != "/usr/share/wazuh-indexer" ]]; then
  echo "$LEGACY_CONF exists and is not a symlink to /usr/share/wazuh-indexer" >&2
  exit 1
fi

install -d -m 0750 -o 1000 -g 0 "$CERT_ROOT"

for name in "${!FILES[@]}"; do
  case "$name" in
    admin.pem|admin-key.pem)
      source="$WAZUH_TLS_INPUT_DIR/admin/$name"
      ;;
    *)
      source="$WAZUH_TLS_INPUT_DIR/$name"
      ;;
  esac
  target="$CERT_ROOT/$name"
  mode="${FILES[$name]}"
  [[ -f "$source" ]] || { echo "missing TLS input: $name" >&2; exit 1; }
  install -o 1000 -g 0 -m "$mode" "$source" "$target"
done

for name in "${!FILES[@]}"; do
  target="$CERT_ROOT/$name"
  # stat prints "644"; the table uses "0644". Strip the leading zero.
  expected="${FILES[$name]#0}"
  actual="$(stat -c "%a" "$target")"
  [[ "$actual" == "$expected" ]] || {
    echo "unexpected mode for $name: $actual" >&2
    exit 1
  }
done

exec "$WAZUH_ORIGINAL_ENTRYPOINT" "$@"
