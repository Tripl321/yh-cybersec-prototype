# ADR 0019: The default group lives in the manager's database

- Status: Accepted
- Date: 2026-10-22
- Related: issue #94, ADR 0018, wazuh/wazuh#38633

## Context

ADR 0018 recorded that the manager logged
`There was an error assigning the groups to agent '007'` and that the agent
belonged to no group. The assumed cause was a missing `etc/groups` file.

There is no `etc/groups` file. Wazuh 4.9 keeps the agent groups in the
manager's SQLite database, `queue/db/global.db`: the `group` table holds the
groups and `belongs` maps agents to them. The image builds that database from
`src/wazuh_db/schema_global.sql` at every start. The schema creates the tables
but inserts no row for `default`; a normal installation gets the row from its
setup scripts, which the image never runs.

Two consequences follow from an empty `group` table:

1. New agents are registered with the group name `default` on their agent row,
   but the group has no id.
2. The daemons assign the groups of the already enrolled agents while they
   start. The assignment looks the group up and logs
   `Unable to find the id of the group 'default'` followed by
   `There was an error assigning the groups to agent`, and the agent stays
   without a group until something creates the row and a later sync heals it.

The manager's own CLI cannot create the row: `agent_groups.py` refuses
`default` because the shipped configuration directory
`/var/ossec/etc/shared/default` already exists. Inserting the row directly is
therefore the only path, and it has to happen before the daemons assign the
groups, not after.

## Decision

1. `shallot-infra/scripts/1-wazuh-group.sh` runs from `cont-init.d`. Its name
   sorts before `2-manager`, so it runs before the daemons start.
2. It starts `wazuh-db` directly. The daemon creates the database from the
   schema, and it stays running, so `2-manager` finds it and leaves it alone.
3. It waits for the database socket `queue/db/wdb` and asks the daemon for the
   groups. If `default` is missing, it sends
   `global insert-agent-group default`; otherwise it is a no-op.
4. The script retries the query, so a database that is still initialising is
   not a start failure. A database that never answers fails the container
   start instead of hiding the problem.
5. The manager's database is not persisted. The row is created on every start,
   which keeps the container stateless and keeps the image's own queue
   initialisation intact: a volume under `queue/` would make that
   initialisation skip its copy of the queue tree.

## Runtime evidence

Verified on 2026-10-22, rootless Podman, indexer, manager and one agent
container:

1. The init output shows
   `wazuh-group: created the default group in the manager database` before
   `2-manager`, and both `0-wazuh-init` and the UID fix exit 0.
2. `global select-groups` returns `[{"name":"default"}]` and
   `global select-group-belong 008` returns `["default"]`, so the enrolled
   agent belongs to the group.
3. The manager's log has no new `Unable to find the id of the group` or
   `There was an error assigning the groups` line; the only occurrence is the
   2026-10-21 one that motivated this increment.
4. The agent connects over TCP 1514 and the indexer receives its rule 503
   `Wazuh agent started.` alert with `agent.id: "008"`.

## Follow-ups

- The `default` group has no content of its own; the shared
  `agent.conf` policy and the manager's own monitoring remain separate
  increments.
- A database volume was tried first and reverted: it hides the image's queue
  tree from the init script, which then skips creating `queue/alerts`,
  `queue/sockets` and the other directories the daemons expect.

## Rollback

Remove the script mount from `compose.wazuh.yml` and delete
`shallot-infra/scripts/1-wazuh-group.sh`. The manager then starts without the
group row, as before; no committed credential is touched.

## Consequences

- The agent has a real group, so the manager's group view, the shared
  configuration path and any per-group policy work from the first start.
- The fix depends on the manager's database schema and on the daemon's socket
  commands, so an image upgrade has to re-check the group table and the
  `insert-agent-group` command.
- The database stays in the container, so agent registrations are re-imported
  from the persisted `etc/client.keys` on every start and the group row is
  rebuilt from this script.
