# ADR 0016: Wazuh manager TLS to the indexer

- Status: Proposed
- Date: 2026-10-21
- Related: issue #94, ADR 0013, ADR 0014, ADR 0015

## Context

ADR 0015 verified that the indexer serves HTTPS with a certificate whose only
subject alternative name is `DNS:wazuh-indexer.local`. The manager image ships
filebeat, and the official `wazuh-docker` 4.9.0 model configures it from
environment variables (`INDEXER_URL`, `FILEBEAT_SSL_VERIFICATION_MODE`,
`SSL_CERTIFICATE_AUTHORITIES`, `SSL_CERTIFICATE`, `SSL_KEY`) through the image
init script `1-config-filebeat`. The manager hop to the indexer was still
plaintext.

The first runtime start of this increment also showed that the corrected
`opensearch.yml` copy lacked `plugins.security.allow_default_init_securityindex`,
so the security index was never created and the indexer ran unsecured. The
official single-node config sets that flag; the copy now does too.

## Decision

1. Manager TLS lives only in the opt-in overlay
   `shallot-infra/compose.wazuh-tls.override.yml`. The plain baseline in
   `compose.wazuh.yml` keeps `INDEXER_URL=http://wazuh-indexer:9200`.
2. `INDEXER_URL=https://wazuh-indexer.local:9200` with
   `FILEBEAT_SSL_VERIFICATION_MODE=full`, so hostname and chain verification
   stay enabled. The indexer service gets the compose network alias
   `wazuh-indexer.local` so the certificate name resolves on the network. No
   certificate is regenerated.
3. The manager trusts only the lab CA (`root-ca.pem`) and presents the lab
   manager certificate (`filebeat.pem`, `filebeat-key.pem`), mounted read-only
   under `/etc/ssl`, from the official `wazuh-certs-tool` input layout.
4. The manager authenticates to the indexer with the admin account, as in the
   official model. A least-privilege shipping user needs a custom roles mapping
   in the indexer security configuration, which is not applied in this
   increment; it is a follow-up.
5. Input layout: `root-ca.pem`, `indexer.pem`, `indexer-key.pem`,
   `admin/admin.pem`, `admin/admin-key.pem`, `filebeat/filebeat.pem`,
   `filebeat/filebeat-key.pem`.

## Safety boundary

This increment starts no container, pulls no image, runs no `securityadmin.sh`,
generates no credential, and pushes no branch. A runtime start requires
separate explicit approval.

## Verification

Static:

1. `pytest tests` passes.
2. `python ansible/scripts/check_runtime_policy.py` passes.
3. `podman compose ... config` shows the merged manager environment and
   mounts.
4. Secret scan finds no key material in the diff; `git diff --check` is clean.

Runtime, only after explicit approval:

1. Indexer reports cluster health GREEN and answers HTTPS.
2. Manager log shows filebeat connected to `https://wazuh-indexer.local:9200`
   without TLS errors, and the indexer accepts the admin credentials.
3. No `PRIVATE KEY` in container logs; stack is torn down afterwards.

## Rollback

Revert the overlay, base overlay, and ADR commits. Remove the local input
directory copy. No committed credential is touched.

## Consequences

- The manager hop is encrypted and hostname-verified; the indexer name is now
  part of the contract between certificate and network configuration.
- The plain HTTP baseline remains available for the non-TLS development path.
- If the indexer rejects the unmapped manager certificate DN, drop
  `SSL_CERTIFICATE` and `SSL_KEY`; the init script then leaves the client
  certificate settings unset and the manager trusts the CA only.
