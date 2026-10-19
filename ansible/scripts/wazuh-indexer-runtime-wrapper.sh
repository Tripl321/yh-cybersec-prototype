#!/usr/bin/env bash
set -euo pipefail

# Secret-free runtime wrapper prototype for the Wazuh indexer image.
# The secret input directory must be supplied explicitly at runtime.

: "${WAZUH_TLS_INPUT_DIR:?WAZUH_TLS_INPUT_DIR is required}"
: "${WAZUH_ORIGINAL_ENTRYPOINT:=/entrypoint.sh}"
CERT_ROOT=/etc/wazuh-indexer/certs

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

install -d -m 0750 -o 1000 -g 0 "$CERT_ROOT"

for name in "${!FILES[@]}"; do
  source="$WAZUH_TLS_INPUT_DIR/$name"
  target="$CERT_ROOT/$name"
  mode="${FILES[$name]}"
  [[ -f "$source" ]] || { echo "missing TLS input: $name" >&2; exit 1; }
  install -o 1000 -g 0 -m "$mode" "$source" "$target"
done

for name in "${!FILES[@]}"; do
  target="$CERT_ROOT/$name"
  expected="${FILES[$name]}"
  actual="$(stat -c "%a" "$target")"
  [[ "$actual" == "$expected" ]] || {
    echo "unexpected mode for $name: $actual" >&2
    exit 1
  }
done

exec "$WAZUH_ORIGINAL_ENTRYPOINT" "$@"
