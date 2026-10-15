# SHALLOT Ansible baseline

This directory contains the reviewed local-only Ansible baseline for issue #94.
It validates the CachyOS/Arch workstation without installing packages, starting
services, pulling images, contacting external hosts, or touching physical
SHALLOT devices.

## Implemented

- Localhost-only inventory and explicit external-bootstrap block
- Ansible, OS, non-root, rootless Podman, systemd, subuid and subgid validation
- Local secret-file permission validation
- Machine-readable runtime image manifest
- Mandatory digest pins for all enabled external images
- CI and Ansible policy enforcement against mutable images and Wazuh defaults
- Wazuh fail-closed profile requiring local password and security configuration
- ADR 0011 for Ansible and rootless Quadlet

## Runtime security policy

`shallot-infra/versions.yml` is the canonical image manifest. The Compose
references must match it exactly. Normal validation never pulls those images.

Wazuh is disabled by default. Enabling `wazuh-secure` requires local files that
are git-ignored and mode `0600`. The indexer password and its local hash
configuration must match. Creating those secrets is a separate reviewed
bootstrap operation.

The former single Latitude image was inaccessible and has been removed from the
runnable Compose definition. A correct official multi-service integration is a
separate increment.

## Validation

Run from the repository root:

```fish
cd ansible
yamllint --config-file .yamllint.yml .
ansible-lint --config-file .ansible-lint
python scripts/check_runtime_policy.py
ansible-playbook playbooks/site.yml --syntax-check
ansible-playbook playbooks/verify.yml --syntax-check
```

On the CachyOS workstation, run the non-mutating verification separately:

```fish
cd ansible
ansible-playbook playbooks/verify.yml
```

A second verification run must report `changed=0`.

## Local secrets

- `inventory/lab/group_vars/secrets.local.yml`
- `../shallot-infra/.env`
- `../shallot-infra/config/wazuh_indexer/internal_users.local.yml`

These files must never be committed and must use mode `0400` or `0600`.
