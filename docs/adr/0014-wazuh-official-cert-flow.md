# ADR 0014: Wazuh official certificate provisioning boundary

- Status: Proposed
- Date: 2026-10-18
- Related: issue #94, ADR 0013

## Context

The Wazuh 4.9.0 indexer image starts OpenSearch Security with a Java SecurityManager.
Direct host bind-mounts into `/etc/wazuh-indexer/certs` are rejected with
`java.security.AccessControlException`, even when UID/GID and file modes match.

The current TLS overlay therefore cannot be treated as a verified runtime path.

## Decision

Use Wazuh’s official certificate provisioning flow as a separate lab increment.
The official `wazuh-certs-tool.sh` and its generated image-layout files must be
used before any indexer runtime start or `securityadmin.sh` application.

Certificate generation must remain local-only. Private keys must never enter Git,
logs, issue text, Compose files, or container image layers.

## Required official layout

- `/etc/wazuh-indexer/certs/root-ca.pem`
- `/etc/wazuh-indexer/certs/indexer.pem`
- `/etc/wazuh-indexer/certs/indexer-key.pem`
- `/etc/wazuh-indexer/certs/admin.pem`
- `/etc/wazuh-indexer/certs/admin-key.pem`

The generated files must be owned/readable for the image’s `wazuh-indexer`
process while preserving private-key confidentiality.

## Safety boundary

This ADR does not download images, generate certificates, start containers,
apply indexer security, or start the Wazuh manager.

The official flow must be validated first with:

1. image and tool version verification,
2. local-only certificate generation,
3. mode/owner verification,
4. certificate-chain and SAN verification,
5. clean Git/secret scan,
6. isolated indexer-only startup,
7. HTTPS and admin-client verification.

## Rollback

Remove only the generated local certificate directory and any isolated runtime
resources. Do not modify the committed repository or existing credential files.
