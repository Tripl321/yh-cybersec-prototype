# SHALLOT Ansible baseline

This directory contains the first reviewed baseline for issue #94. It validates a local CachyOS/Arch-family workstation before later roles add host hardening, rootless Quadlet units, backup, restore, and rollback.

## Current scope

Implemented:

- Localhost-only inventory
- Explicit block on external bootstrap
- Ansible and OS-family validation
- Non-root execution validation
- Rootless Podman validation
- Systemd user-manager validation
- `/etc/subuid` and `/etc/subgid` validation
- Local secret-file permission validation
- Audit detection for unpinned images and the current Wazuh default password
- Proposed ADR for Ansible and rootless Quadlet

Not implemented in this increment:

- Package installation or host mutation
- Quadlet generation
- Firewall changes
- Image or model downloads
- Secret generation
- Backup, restore, or rollback
- Connections to external hosts or physical SHALLOT devices

## Security boundary

The inventory contains localhost only and uses `ansible_connection: local`. Normal runs must not fetch external images or models. Real secrets must never be committed, pasted into issues, or included in command output.

Copy `inventory/lab/group_vars/secrets.example.yml` to the ignored `secrets.local.yml` only when a later implementation requires local secrets. Keep its permissions at `0600` or stricter.

## Workstation commands

Run from the repository root on the local workstation.

```fish
cd ansible
ansible-playbook playbooks/site.yml --check
```

Run the non-mutating verification playbook separately:

```fish
cd ansible
ansible-playbook playbooks/verify.yml
```

The current site playbook performs validation only. It does not install packages, enable lingering, create services, pull images, or contact external systems.

## Expected current finding

The verification role reports audit findings while the Compose development reference still contains `:latest` images or the known Wazuh indexer default password. Enforcement remains disabled until those items are corrected in a separately reviewed change.

## Next reviewed increment

After this baseline is approved:

1. Add version and digest manifest.
2. Replace known default credentials with required local secret injection.
3. Add rootless Quadlet templates.
4. Add systemd user-service verification.
5. Add local backup, restore, and rollback roles.

No security-critical change should be merged or executed against a real environment without human review.
