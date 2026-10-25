#!/usr/bin/env bash
set -euo pipefail

# Rootless Podman with userns_mode: keep-id maps the host user to exactly one
# container UID, and s6 starts the daemons with that UID. The image ships the
# wazuh account at 999, which is not mapped, so the daemons cannot drop to it
# and keep the inherited UID under an account that is not wazuh. Give the
# wazuh account the mapped UID instead.
#
# The keep-id account cannot be moved: s6 PID 1 runs with it, and usermod
# refuses to change the UID of an account that a running process uses. So the
# wazuh account takes the same UID with -o, which allows the duplicate. The
# wazuh entry comes first in /etc/passwd, so getpwuid still resolves it.
#
# cont-init.d order: after 0-wazuh-init (which still chowns to the old UID),
# before 1-config-filebeat and 2-manager (which start the daemons).

# Podman injects the host user as "<name>:*:<uid>:<gid>:<gecos>:<home>:/bin/sh".
# The home directory follows the container working directory, so only the shell
# identifies the account; no image account uses /bin/sh.
KEEPID_ACCOUNT=$(getent passwd | awk -F: '$7 == "/bin/sh" { print $1; exit }')
if [ -z "$KEEPID_ACCOUNT" ]; then
  echo "wazuh-uid: no keep-id account found; is userns_mode keep-id set?" >&2
  exit 1
fi

TARGET_UID=$(id -u "$KEEPID_ACCOUNT")
if [ "$(id -u wazuh)" != "$TARGET_UID" ]; then
  usermod -o -u "$TARGET_UID" wazuh
fi
chown -R wazuh:wazuh /var/ossec
