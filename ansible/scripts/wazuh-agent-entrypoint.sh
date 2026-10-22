#!/usr/bin/env bash
set -euo pipefail

# The manager accepts enrollment without a password in this lab, so the key is
# created inside the agent container and never leaves the host tree. The tree
# is outside the repository and client.keys keeps mode 0600.
#
# The UID fix is the same one the manager uses (ADR 0017): under rootless
# Podman with keep-id only the host user is mapped, so the wazuh account takes
# that UID and the agent's own processes keep writing as the host user.
/opt/shallot/0-wazuh-uid.sh

if [ ! -s /var/ossec/etc/client.keys ]; then
  /var/ossec/bin/agent-auth \
    -m "${WAZUH_MANAGER_HOST:-wazuh}" \
    -A "$(cat /var/ossec/etc/agent-name)" \
    -G default
fi

# The agent is the whole daemon set, not only the agent daemon: the manager
# pushes a shared configuration and the agent applies it over the socket that
# the module daemon owns. Every daemon runs in the foreground, so the
# container lives exactly as long as the agent does.
/var/ossec/bin/wazuh-modulesd -f &
/var/ossec/bin/wazuh-logcollector -f &
/var/ossec/bin/wazuh-syscheckd -f &
/var/ossec/bin/wazuh-execd -f &

exec /var/ossec/bin/wazuh-agentd -f
