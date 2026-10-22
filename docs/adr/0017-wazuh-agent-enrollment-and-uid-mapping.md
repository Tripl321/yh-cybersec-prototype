# ADR 0017: Wazuh agent enrollment and rootless UID mapping

- Status: Accepted
- Date: 2026-10-21
- Related: issue #94, ADR 0011, ADR 0016

## Context

ADR 0016 secured the manager hop to the indexer. Two things were still missing
for a usable lab runtime: an agent that reports to the manager, and manager
daemons that run unprivileged.

The manager image ships the `wazuh` account at UID 999 and its init chowns the
permanent data to that UID. Under rootless Podman with `userns_mode: keep-id`
the host user is mapped to exactly one container UID; every other container UID
is unmapped, so a daemon cannot `setuid` to UID 999. The daemons kept the
inherited UID and the process list showed them under the injected keep-id
account instead of `wazuh`.

The agent also needs the manager's agent port. The official single-node model
publishes TCP and UDP 1514; the base overlay published only the API port
55000 and the enrollment port 1515.

## Decision

1. The manager publishes 1514 on TCP and UDP, bound to 127.0.0.1. TCP carries
   the enrolled agent traffic; UDP is kept because the official model listens
   on both and the manager binds both.
2. `shallot-infra/scripts/0-wazuh-uid.sh` runs from `/etc/cont-init.d`. The
   image init `s6-overlay` runs those scripts in name order, so the script
   lands after `0-wazuh-init` (which still chowns to the old UID) and before
   `1-config-filebeat` and `2-manager` (which start the daemons). It gives the
   `wazuh` account the mapped keep-id UID and chowns `/var/ossec` to the
   `wazuh` account. The keep-id account is found by the shape Podman injects
   it in (`<name>:*:<uid>:<gid>:<gecos>:<home>:/bin/sh`); no account name is
   hardcoded. The keep-id account itself cannot be moved: s6 PID 1 runs with
   it and `usermod` refuses to change the UID of an account that a running
   process uses. The `wazuh` account therefore takes the same UID with `-o`,
   which allows the duplicate; the `wazuh` entry comes first in `/etc/passwd`,
   so `getpwuid` still resolves it. The script is idempotent through the UID
   comparison and aborts loudly instead of swallowing a failed `usermod`.
   ADR 0018 narrowed the detection to the shell, because Podman sets the
   injected home directory to the container's working directory.
3. The manager keeps `cap_add: CHOWN, SETUID, SETGID, DAC_OVERRIDE, FOWNER,
   SYS_CHROOT, KILL` over `cap_drop: ALL`, because the script chowns the
   installed tree and the daemons drop privileges.
4. The agent is enrolled with `agent-auth` against the manager's enrollment
   port 1515 and then reports over TCP 1514. The agent process is not part of
   the Compose stack: the lab runs it from the pinned `wazuh-agent` 4.9.0
   package in its own rootless container, so the manager stack stays the only
   managed runtime. ADR 0018 replaces this with a Compose definition for the
   agent container.
5. The enrollment key never leaves the lab: the agent's `client.keys` is
   written to the agent's own key store, and the manager holds the
   corresponding entry. Neither file is committed.

## Runtime evidence

Verified on 2026-10-21, rootless Podman, indexer, manager and one agent
container, explicit human approval:

1. UID mapping: the container starts with `wazuh` at UID 999 and the injected
   keep-id account at the mapped UID 1000, s6 PID 1 running as UID 1000. The
   script runs from `/etc/cont-init.d` and exits 0. After it, `wazuh` holds
   UID 1000 and every manager process, including s6-svscan and filebeat, is
   listed as `wazuh`.
2. Host ownership: the manager log files under the `wazuh-logs` volume are
   owned by the host user UID 1000 with GID 100999, so the daemons do not run
   as host root.
3. The mount is read-only, so the image init logs `s6-chown: fatal: unable to
   chown /var/run/s6/etc/cont-init.d/0-wazuh-uid.sh: Read-only file system`
   and the matching `s6-chmod` line. The script itself still runs and exits 0;
   the messages are harmless and the repository file keeps its host
   ownership.
4. Enrollment: `agent-auth` against `127.0.0.1:1515` returned
   `Valid key received` for the agent name `shallot-agent-clean`, agent ID
   006.
5. Reporting: the agent connected over TCP `127.0.0.1:1514` with AES and the
   indexer documents for `agent.id: "006"` carry the manager's own events:
   rule 501 `New wazuh agent connected.`, rule 506 `Wazuh agent stopped.` and
   rule 222 `Could not restart due to a error while unmerging files`. Rule 222
   came from the wrong working directory, which made the agent resolve
   `etc/shared/ar.conf` relative to the wrong place. The lab tree had no log
   collector, so no event decoded by the agent itself is part of this
   evidence. ADR 0018 records the corrected agent runtime.

## CI evidence

Woodpecker runs `pytest tests/test_wazuh_*.py` and
`ansible/scripts/check_runtime_policy.py` on every pull request (status
context `ci/woodpecker/pr/woodpecker`). For commit `0aebd24` (PR #117) the
status context was green on 2026-10-21 (pipeline 38). Every new push needs a
new green pipeline before the merge.

## Follow-ups

- The manager `ossec.conf` still monitors almost nothing; a fuller
  `wazuh_manager.conf` is a separate increment.
- The agent container has no Compose or Quadlet definition yet; ADR 0018 adds
  the Compose definition and the reproducible package tree.

## Rollback

Revert the agent port mapping and the UID script. Existing volumes keep their
ownership; a `chown -R wazuh:wazuh /var/ossec` inside the manager restores the
expected state.

## Consequences

- Agents can reach the manager over the published port without exposing it
  beyond the loopback interface.
- The manager daemons run under the `wazuh` account inside the container and
  as the host user on the host, so neither layer is privileged.
- The UID fix depends on the image's `s6-overlay` init ordering; an image
  upgrade must re-check that `0-wazuh-uid.sh` still runs before `2-manager`.
