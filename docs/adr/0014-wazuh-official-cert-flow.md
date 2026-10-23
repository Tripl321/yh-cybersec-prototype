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

Superseded by ADR 0015: the certificate directory is
`/usr/share/wazuh-indexer/certs` (`path.conf`), not `/etc/wazuh-indexer/certs`.
The original requirement below was taken from the image default
`opensearch.yml` and is the recorded cause of the AccessControlException.

- `/usr/share/wazuh-indexer/certs/root-ca.pem`
- `/usr/share/wazuh-indexer/certs/indexer.pem`
- `/usr/share/wazuh-indexer/certs/indexer-key.pem`
- `/usr/share/wazuh-indexer/certs/admin.pem`
- `/usr/share/wazuh-indexer/certs/admin-key.pem`

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

## Verified findings

The following local tests were performed against the digest-pinned Wazuh
4.9.0 indexer image:

- Direct host bind-mounts to `/etc/wazuh-indexer/certs` failed.
- Host-staged read-only bind-mounts to the same path failed.
- Wazuh-generated certificate filenames and paths also failed when mounted
  from the host.
- Every failed indexer start reported:
  `java.security.AccessControlException: FilePermission ... indexer.pem read`.
- Rootless named-volume staging failed because the init container could not
  change ownership and permissions on the named volume.
- The official certificate tool could not run inside the read-only Wazuh image:
  it attempted to write its log and the image did not provide OpenSSL.
- The official script was subsequently run with host OpenSSL; certificate
  chain and key matching passed, but indexer startup remained blocked by the
  Java SecurityManager.
- No `securityadmin.sh` apply was performed.
- No Wazuh manager was started.
- All failed runtime resources were removed after each test.

## Current status

This increment is blocked for the Wazuh 4.9.0 rootless-container layout.
The repository must not claim that the current TLS overlay is a working runtime
configuration.

Resolved by ADR 0015: runtime probes on 2026-10-19 showed that the required
certificate directory is `${OPENSEARCH_PATH_CONF}/certs`, not
`/etc/wazuh-indexer/certs`, and the overlay was replaced by wrapper-based
staging with a corrected `opensearch.yml`.

Further work requires a separately reviewed deployment strategy that places
the certificates inside a Java-policy-compatible image or container-owned
filesystem before OpenSearch Security starts. Disabling the Java SecurityManager,
making private keys world-readable, or applying broad policy permissions is
not an accepted workaround.
