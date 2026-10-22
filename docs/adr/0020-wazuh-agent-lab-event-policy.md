# ADR 0020: The agent collects a lab event file

- Status: Accepted
- Date: 2026-10-22
- Related: issue #94, ADR 0018, ADR 0019

## Context

ADR 0018 left the agent's monitoring policy empty: the increment proved the
agent to manager to indexer hop with the agent's own status events only. A
real policy needs a file to watch and a manager rule that turns its events
into alerts.

The manager's shipped ruleset has no rule for the lab's JSON events. An event
without a matching rule is dropped before it reaches the indexer, so adding a
`localfile` alone would produce no alert and no evidence.

The file must sit outside `/var/ossec`: the UID fix chowns the whole agent tree
to the agent's account, and the host user has to keep writing to the file.

## Decision

1. The agent template `config/wazuh_agent/ossec.conf` watches
   `/opt/shallot/lab/events.json` with `<log_format>json</log_format>`, so
   every JSON object becomes one event with its fields decoded.
2. `ansible/scripts/prepare_wazuh_agent.py` creates `lab/events.json` next to
   the agent tree, not inside it. The file is empty on the first prepare and
   survives later prepares.
3. `compose.wazuh-agent.override.yml` mounts that `lab` directory read-only at
   `/opt/shallot/lab`. The host user writes the events; the agent only reads.
4. The manager ships `config/wazuh_manager/local_rules.xml`, mounted over
   `/var/ossec/etc/rules/local_rules.xml`. Rule 100100 matches
   `<decoded_as>json</decoded_as>` at level 5 and carries the agent id, so the
   event reaches the indexer as an alert.
5. The rule is a lab placeholder: it exists to prove the path, not to classify
   events. Real detection rules are a separate increment.

## Runtime evidence

Verified on 2026-10-22 with the pinned stack and one agent container:

1. The agent log shows
   `Analyzing file: '/opt/shallot/lab/events.json'` and the collector starts
   without a permission error.
2. Writing
   `{"shallot":"lab","event":"door-open","node":"field-node-1","ts":"..."}`
   to the host file produced an alert in `wazuh-alerts-4.x-*` with
   `agent.id: "008"`, `rule.id: "100100"`,
   `rule.description: "Shallot lab JSON event."` and the event's fields under
   `data` (`shallot`, `event`, `node`, `ts`), so decoding and forwarding both
   work.
3. The manager starts with the local rules file mounted read-only; the UID fix
   tolerates the failed chown on that file and still fixes the rest of the
   tree.

## Follow-ups

- Rule 100100 does not distinguish event types; the lab's detection content is
  a separate increment.
- The event file is append-only from the host and has no rotation; the lab
  truncates it by hand.

## Rollback

Remove the `localfile` block, the `lab` mount, the `lab/events.json` creation
and the manager's local rules mount. The agent then reports only its own status
events, as in ADR 0018.

## Consequences

- The lab has an end-to-end path from a host-written file to an indexed alert
  that carries the agent id, which is the evidence the event policy needs.
- The event file lives outside the repository and outside the agent tree, so
  no lab event is committed and a re-prepare does not lose it.
- The manager needs a local rule for every new event shape; without one the
  event is dropped silently.
