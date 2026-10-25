#!/usr/bin/env bash
set -euo pipefail

# Wazuh keeps the agent groups in the manager's database, and the image builds
# that database from its schema at every start. The schema has no row for the
# "default" group, so the daemons that assign the groups of the enrolled
# agents find no id for it: "Unable to find the id of the group 'default'" and
# "There was an error assigning the groups to agent". The row is put in the
# database here, before the daemons start.
#
# The manager's own CLI refuses the group, because the shipped configuration
# directory /var/ossec/etc/shared/default already exists, so the row goes in
# over the socket that the database daemon owns. The daemon is started here
# because it only exists inside the manager that 2-manager starts; 2-manager
# finds it running and leaves it alone.
#
# cont-init.d order: after 0-wazuh-uid.sh (the daemons must run as the
# mapped UID) and before 2-manager (which starts the daemons).

/var/ossec/bin/wazuh-db

for attempt in $(seq 1 30); do
    [ -S /var/ossec/queue/db/wdb ] && break
    sleep 1
done

for attempt in $(seq 1 30); do
    if /var/ossec/framework/python/bin/python3 -c '
import json
from wazuh.core.wdb import WazuhDBConnection

wdb = WazuhDBConnection()
try:
    groups = json.loads(wdb.send("global select-groups", raw=True)[1])
    if any(group["name"] == "default" for group in groups):
        print("wazuh-group: the default group is already in the manager database")
    else:
        wdb.send("global insert-agent-group default", raw=True)
        print("wazuh-group: created the default group in the manager database")
finally:
    wdb.close()
'; then
        exit 0
    fi
    sleep 1
done

echo "wazuh-group: the manager database did not answer" >&2
exit 1
