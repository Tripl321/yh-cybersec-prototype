# SHALLOT container development reference

`compose.yml` remains a development reference while the runtime migrates to
rootless Quadlet. Normal validation does not pull or start any image.

## Immutable images

All external images are pinned by version and manifest digest. The canonical,
machine-readable identities are in `versions.yml`; CI and Ansible verification
require the Compose references to match that manifest exactly.

## Wazuh security gate

Wazuh is absent from the default Compose stack. It exists only in the explicit
`compose.wazuh.yml` overlay and remains gated by the `wazuh-secure` profile.
This keeps the default stack independent of Wazuh secrets.

Do not include the overlay until both local files exist and have mode `0600`:

- `shallot-infra/.env`, containing a non-default `WAZUH_INDEXER_PASSWORD`
- `shallot-infra/config/wazuh_indexer/internal_users.local.yml`, based on the
  complete official Wazuh 4.9.0 security configuration with reviewed, locally
  generated password hashes

The password in `.env` must match the local admin hash configuration. Neither
file may be committed, printed in logs, issues, or chat. Creating the Wazuh
security configuration is a separate human-reviewed bootstrap operation.

A future approved start command will use both files explicitly, for example:

```fish
podman compose \
    -f compose.yml \
    -f compose.wazuh.yml \
    --profile wazuh-secure \
    up -d
```

Do not run that command during this increment.

## Latitude

The former `middayai/latitude:latest` reference is not publicly accessible and
is removed from the runnable Compose definition. Current official Latitude
self-hosting is a multi-service platform and must be integrated in a separate,
reviewed increment. Cub continues safely without Latitude telemetry when no API
key is configured.

## Validation

Run from the repository root without starting containers:

```fish
python ansible/scripts/check_runtime_policy.py
```

Do not start containers, enable `wazuh-secure`, or pull images as part of normal
validation.
