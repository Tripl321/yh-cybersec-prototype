#!/usr/bin/env bash
set -euo pipefail

# Rootless Podman with userns_mode: keep-id maps host UID 1000 to container UID 0
# (root). Container UID 999 (the wazuh user) is not in the userns map, so Wazuh
# daemons cannot drop to the wazuh user and end up running as johannes (UID 1000
# in container = host root). Fix by moving johannes to UID 1001 and wazuh to
# UID 1000, both of which are valid in the keep-id userns map.
if id -u johannes >/dev/null 2>&1; then
  usermod -u 1001 johannes 2>/dev/null || true
fi
usermod -u 1000 wazuh 2>/dev/null || true
chown -R wazuh:wazuh /var/ossec 2>/dev/null || true
