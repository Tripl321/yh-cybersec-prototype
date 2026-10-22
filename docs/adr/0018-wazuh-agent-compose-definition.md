# ADR 0018: Reproducible Wazuh agent container definition

- Status: Accepted
- Date: 2026-10-21
- Related: issue #94, ADR 0016, ADR 0017

## Context

ADR 0017 enrolled an agent from a hand-picked lab tree: a handful of binaries
and libraries copied into `~/.local/share/shallot/wazuh-agent` by hand. The
tree was not reproducible, it was missing `wazuh-syscheckd`,
`wazuh-modulesd`, `wazuh-execd` and `wazuh-logcollector`, and it had no
Compose definition, so the agent was a local artifact outside the stack.

There is no official `wazuh/wazuh-agent` image for 4.9.0; the first published
agent tag is 4.13.0, and a 4.13 agent cannot register with a 4.9.0 manager.
The agent must therefore run the pinned 4.9.0 manager image and take its
binaries from the official `wazuh-agent` 4.9.0-1 package.

## Decision

1. The agent service runs the same pinned manager image as the manager
   (`wazuh/wazuh-manager:4.9.0` at the recorded digest). The image supplies
   the agent's runtime; the agent's own code comes from the official package.
2. `ansible/scripts/prepare_wazuh_agent.py` builds the agent tree outside the
   repository. It downloads the package from the URL in `versions.yml`, checks
   the SHA-256 against the same file, unpacks the whole payload, renders
   `etc/ossec.conf` from the repository template and writes the deterministic
   agent name to `etc/agent-name`. The tree is the package payload, not a
   selection of files, so the eight binaries and the nine libraries stay
   consistent with each other.
3. The enrollment key and the agent name survive a re-prepare, so the manager
   keeps one agent identity per tree. The agent name is
   `shallot-agent-<sha256 of the tree path, first 8 hex digits>`, which makes
   the identity stable without storing it anywhere else.
4. The agent lives in `shallot-infra/compose.wazuh-agent.override.yml` behind
   the `wazuh-secure` profile, next to the indexer and the manager. The tree
   is bind-mounted at `/var/ossec`, the working directory is `/var/ossec`
   because the agent resolves paths like `queue/sockets/com` relative to the
   install directory, and the manager is reached by its service name `wazuh`
   on the compose network rather than through the published port.
5. The tree directory is mandatory: the bind mount uses
   `${SHALLOT_WAZUH_AGENT_DIR:?...}`, so a start without it fails instead of
   silently using an empty tree.
6. The agent runs the whole daemon set, not only `wazuh-agentd`. The manager
   pushes a shared configuration and the agent applies it over the socket the
   module daemon owns; without `wazuh-modulesd` the agent stops at
   `Could not connect to socket 'queue/sockets/com'`. Every daemon runs in the
   foreground, so the container lives exactly as long as the agent does.
7. The agent reuses the manager's UID fix (`shallot-infra/scripts/0-wazuh-uid.sh`)
   because both run their daemons as the `wazuh` account under rootless
   Podman with `keep-id`. The keep-id account is now found by its shell, not
   by its home directory: Podman sets the injected home to the container's
   working directory, and the agent runs with `/var/ossec` as its working
   directory.
8. The tree is mounted read-write. The UID fix chowns the whole tree, and a
   read-only payload would make that chown fail.
9. The agent's monitoring policy is empty in this increment. The increment
   proves the agent to manager to indexer hop, not the content of the policy.

## Runtime evidence

Verified on 2026-10-21, rootless Podman, indexer, manager and one agent
container, explicit human approval:

1. The tree was built from the pinned package: 279 files, the eight binaries
   (`wazuh-agentd`, `wazuh-modulesd`, `wazuh-logcollector`, `wazuh-syscheckd`,
   `wazuh-execd`, `agent-auth`, `manage_agents`, `wazuh-control`) and the
   nine libraries, all owned by the host user. The package ships directories
   without the execute bit, so the prepare script normalises the directory
   modes; as shipped only root could read them.
2. Enrollment: `agent-auth` against the manager's service name returned
   `Valid key received` for the agent name `shallot-agent-dc8aa746`, and the
   manager logged `Agent key generated for 'shallot-agent-dc8aa746'`.
3. Reporting: the agent connected over TCP 1514 with
   `(4102): Connected to the server ([wazuh]:1514/tcp)`, received the
   manager's shared configuration (`etc/shared/merged.mg`, 899 kB) and the
   indexer holds the manager's alerts for the agent:
   rule 501 `New wazuh agent connected.` with `agent.id: "007"` and
   `agent.name: "shallot-agent-dc8aa746"`.
4. Lifecycle: a stop and a restart produced rule 506 `Wazuh agent stopped.`
   and rule 503 `Wazuh agent started.` with the same agent id, so the
   manager tracks one identity across restarts.
5. Identity across a re-prepare: the prepare script was run again over the
   live tree. The enrollment key and the agent name were byte-identical
   afterwards, the agent restarted without an enrollment request, and the
   manager logged no new `Received request for a new agent`.
6. Host ownership: the tree is owned by the host user, so the agent does not
   need root on the host. The manager still logs
   `There was an error assigning the groups to agent '007'`, because the
   manager's own `etc/groups` file is missing from the image; the agent is
   registered and reports, but it belongs to no group.

## Follow-ups

- The agent's monitoring policy is empty; ADR 0020 adds the lab event file and
  the manager rule that turns its events into alerts.
- ADR 0019 corrects runtime evidence 6 above: the image ships no `etc/groups`
  because there is no such file. The groups live in the manager's database,
  and the database starts without a row for `default`.
- The manager `ossec.conf` monitors almost nothing; a fuller
  `wazuh_manager.conf` is a separate increment.

## Rollback

Remove the overlay, the prepare script and the agent template, and delete the
tree outside the repository. The manager keeps the agent entry until
`manage_agents` removes it; no committed credential is touched.

## Consequences

- The agent is reproducible from a pinned package and a pinned image, and it
  is part of the managed stack instead of a local artifact.
- The agent tree lives outside the repository, so the enrollment key is never
  committed, and the tree is replaced rather than updated in place.
- The agent shares the manager's UID fix, so an image upgrade has to re-check
  the keep-id account detection in one place.
