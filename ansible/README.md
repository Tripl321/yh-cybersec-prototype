# SHALLOT Ansible baseline

This directory contains the reviewed local-only Ansible baseline for issue #94.
Normal validation installs nothing, starts no service, pulls no runtime image,
and contacts no external host or physical SHALLOT device.

## Implemented

- Localhost-only inventory and explicit external-bootstrap block
- Rootless Podman and workstation preflight verification
- Digest-pinned runtime image manifest and enforced policy checks
- Wazuh isolated in an explicit fail-closed Compose overlay
- Local secret-file permissions and secret-format validation
- Explicit Wazuh credential-bootstrap playbook

## Wazuh credential bootstrap

`playbooks/bootstrap_wazuh.yml` creates credentials only. It never starts Wazuh
or any other service. The real run:

- generates six unique URL-safe passwords,
- hashes each password with Wazuh 4.9.0's official `hash.sh`,
- uses the digest-pinned Wazuh indexer image with networking disabled,
- writes `.env` and `internal_users.local.yml` atomically with mode `0600`,
- refuses to overwrite existing credential files,
- suppresses all task output with `no_log`.

Check mode is local and non-mutating:

```fish
cd ansible
ansible-playbook playbooks/bootstrap_wazuh.yml --check
```

A real bootstrap requires explicit human approval and both flags:

```fish
ansible-playbook playbooks/bootstrap_wazuh.yml \
    -e shallot_wazuh_bootstrap_enabled=true \
    -e shallot_wazuh_bootstrap_allow_pull=true
```

Do not run the real command until the PR is reviewed. The pull flag permits only
the already digest-pinned Wazuh indexer image. No secret is printed.

## Remaining Wazuh blockers

Credential generation does not make the Wazuh runtime production-ready. TLS
certificates, indexer security application, runtime health verification, backup,
and rollback remain separate reviewed increments. `compose.wazuh.yml` must not
be started before those controls are implemented.

## Validation

```fish
cd ansible
yamllint --config-file .yamllint.yml .
ansible-lint --config-file .ansible-lint
python scripts/check_runtime_policy.py
python -m py_compile scripts/bootstrap_wazuh_credentials.py
ansible-playbook playbooks/site.yml --syntax-check
ansible-playbook playbooks/verify.yml --syntax-check
ansible-playbook playbooks/bootstrap_wazuh.yml --syntax-check
```

On the CachyOS workstation, normal verification must remain idempotent with
`changed=0`.
