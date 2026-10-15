# ADR 0012: Consolidate contact-auth into the canonical SHALLOT repository

- Status: Proposed
- Date: 2026-10-16
- Related: issue #94, ADR 0008, ADR 0009

## Context

SHALLOT evolved in two public repositories. `yh-cybersec-prototype` became the
broader thesis, software, infrastructure, FIDO2, LoRa, and agent platform.
`yh-contact-auth-projektarbete` developed the active PAW–DEN UART hardware MVP,
Mama Bear provisioning, firmware, protocol libraries, CLI tooling, and detailed
security tests.

Maintaining both as active SHALLOT sources causes architectural drift, duplicate
documentation, split issues, and uncertainty about which implementation is
canonical.

## Decision

`Tripl321/yh-cybersec-prototype` is the canonical SHALLOT repository.

Unique current source material from `yh-contact-auth-projektarbete` at commit
`c6bd6d809a017c49abd3225009671c0c20d7a69a` is migrated under
`hardware/contact-auth/`. Root-level files are not overlaid, so the broader
SHALLOT structure remains intact and the hardware module remains independently
testable.

Generated metadata, local status dumps, scratch uploads, IDE state, weekly
status reports, generic templates, and unrelated document artifacts are not
migrated. Historical files that are still required by active tests remain as
nested test fixtures.

The source repository remains available as migration history and is archived
only after the migration is merged, CI is green, and a human explicitly
approves archival.

## Test policy

The source and migrated module share the same baseline: 282 passed, 4 skipped,
and two pre-existing PRO-45 source/test drift failures. CI accepts only those
two exact failures. Additional failures block the migration. Resolution of the
PRO-45 drift is a separate reviewed change.

## Safety boundary

Repository consolidation does not build or flash firmware, change radio
parameters, contact external hosts, connect to Mama Bear, or alter physical
SHALLOT devices.

## Consequences

### Positive

- One canonical issue, review, and documentation location
- Hardware firmware and protocol evidence become part of the main thesis repo
- Existing software, infrastructure, and hardware work can evolve together
- The old repository can become read-only historical evidence

### Negative

- The canonical repository becomes larger
- UART MVP and LoRa target architecture coexist and require explicit labeling
- Historical test fixtures remain until their source guards are redesigned
- Two known PRO-45 failures remain visible as tracked technical debt
