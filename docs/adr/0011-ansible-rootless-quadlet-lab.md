# ADR 0011: Ansible and rootless Podman Quadlet for the SHALLOT lab

- Status: Proposed
- Date: 2026-10-13
- Related: #94, ADR 0005, ADR 0007

## Context

SHALLOT has a local-first Podman Compose definition, but no reproducible host provisioning, deployment verification, backup, restore, or rollback layer. The lab must remain local, reviewable, and fail closed. Infrastructure automation must not enter the FIDO2, LoRa, relay, or other safety-critical runtime paths.

## Decision

Use Ansible as the host provisioning and configuration layer for a production-like local lab. Use rootless Podman Quadlet and systemd user services as the target runtime. Keep the existing Compose file as a development reference during migration.

The first supported baseline is a local CachyOS/Arch-family workstation using `ansible_connection: local`. External hosts, VPS systems, and physical SHALLOT devices are explicitly out of scope until separately approved.

Ansible may manage packages, rootless Podman prerequisites, directories, configuration, Quadlet units, local firewall policy, version manifests, backup, restore, rollback, and verification. It must not make access decisions, control a Field Node relay, implement LoRa protocol logic, or become a runtime dependency for safe operation.

Secrets must not be committed. The repository contains placeholders only. External image or model downloads must be isolated behind an explicit bootstrap operation and must not occur during normal convergence or verification.

## Consequences

### Positive

- Reproducible and reviewable lab deployment
- Idempotent host configuration
- Native lifecycle management through systemd user services
- Clear separation between infrastructure and safety-critical application logic
- Verifiable controls for versions, permissions, network exposure, backup, and recovery

### Negative

- Compose and Quadlet definitions coexist during migration
- Distribution-specific tasks are required
- Rootless service startup and lingering require careful documentation
- Backup consistency must be designed per stateful service

## Security boundaries

- Local inventory only in the initial implementation
- No automatic SSH or external host access
- No embedded-device flashing or relay control
- No real secrets in Git, logs, issues, or examples
- No merge or execution of security-critical changes without human review

## Follow-up

Issue #94 defines the phased implementation and acceptance criteria. This ADR becomes Accepted only after the first draft pull request has been reviewed and the target architecture approved.
