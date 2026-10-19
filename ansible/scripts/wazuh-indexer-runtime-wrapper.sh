#!/usr/bin/env bash
set -euo pipefail

# Secret-free runtime wrapper prototype for the Wazuh indexer image.
# The secret input directory must be supplied explicitly at runtime.

: "${WAZUH_TLS_INPUT_DIR:?WAZUH_TLS_INPUT_DIR is required}"
: "${WAZUH_ORIGINAL_ENTRYPOINT:=/entrypoint.sh}"
# path.conf (/usr/share/wazuh-indexer) is the only certificate directory the
# OpenSearch SecurityManager grants read access to (ADR 0015). The certificate
# path strings in opensearch.yml must also point here; the overlay mounts a
# corrected opensearch.yml because this image's env->-E conversion is inert.
CERT_ROOT=/usr/share/wazuh-indexer/certs

declare -A FILES=(
  [root-ca.pem]=0644
  [indexer.pem]=0644
  [indexer-key.pem]=0600
  [admin.pem]=0644
  [admin-key.pem]=0600
)

if [[ "$(id -u)" == "0" ]]; then
  # Staging as root would produce root-owned keys that the UID 1000 indexer
  # cannot read under cap_drop ALL (/usr/share/wazuh-indexer is 0700 1000:1000).
  echo "wrapper must run as the image user, not root" >&2
  exit 1
fi

install -d -m 0750 "$CERT_ROOT"

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
  install -m "$mode" "$source" "$target"
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
