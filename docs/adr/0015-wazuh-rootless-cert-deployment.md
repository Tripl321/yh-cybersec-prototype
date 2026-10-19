# ADR 0015: Rootless Wazuh certificate deployment path and strategy

- Status: Proposed
- Date: 2026-10-19
- Related: issue #94, ADR 0013, ADR 0014

## Context

ADR 0014 records a verified blocker: every indexer start failed with
`java.security.AccessControlException: FilePermission
"/etc/wazuh-indexer/certs/indexer.pem" "read"`. The failed tests all placed
certificates under `/etc/wazuh-indexer/certs`, by host bind mount, by
host-staged read-only mount, or by named-volume staging.

Read-only inspection of the pinned image
(`wazuh/wazuh-indexer:4.9.0@sha256:a7adcac99648b73e075c4fa8daa5bd552da46ec4a7700d7faccd579a2c5e7cc2`)
produced the following evidence, without starting a container:

1. `org.opensearch.bootstrap.Security.addFilePermissions` in
   `lib/opensearch-2.13.0.jar` grants SecurityManager `read,readlink` only on
   `bin`, `lib`, `modules`, `plugins`, `path.conf`, `java.io.tmpdir`,
   `path.logs`, and the data paths. There is no grant for
   `/etc/wazuh-indexer`.
2. The image entrypoint sets `OPENSEARCH_PATH_CONF=/usr/share/wazuh-indexer`
   and derives `CERT=${OPENSEARCH_PATH_CONF}/certs/admin.pem`.
3. The official Wazuh 4.9.0 single-node Compose mounts certificates into
   `/usr/share/wazuh-indexer/certs` and replaces `opensearch.yml` with a file
   that references the same directory.
4. The image default `opensearch.yml` references
   `/etc/wazuh-indexer/certs/*`. That directory does not exist in the image and
   is outside every granted directory.

Conclusion: the blocker is path-based, not mount-based. A certificate file
under `path.conf` is policy-readable regardless of its mount origin.

Rootless DAC is a second, independent factor. In rootless Podman the container
UID 0 maps to the host user, so a host-owned `0600` private key appears as
container UID 0 and is not readable by the indexer process (UID 1000, GID 0).
The certificate files must therefore be copied by the container into a
container-owned filesystem and receive container ownership; host key files
must never be the process-visible source.

## Decision

Use deployment strategy B: rootless runtime init with container-owned
certificate files.

1. The certificate target directory is
   `/usr/share/wazuh-indexer/certs` (`${OPENSEARCH_PATH_CONF}/certs`).
2. The secret-free runtime wrapper stages the files there at container start,
   before the original entrypoint runs. The destination is the container
   writable layer, never a host bind mount and never a named volume.
3. The wrapper starts as container root (Compose sets `user: "0:0"`), reads
   the read-only input directory, installs files with owner `1000:0` and the
   existing mode table (private keys `0600`), then execs the original
   entrypoint, which drops to `1000:0`.
4. For the image default `opensearch.yml`, the wrapper creates the
   compatibility symlink `/etc/wazuh-indexer -> /usr/share/wazuh-indexer` when
   `/etc/wazuh-indexer` does not exist. Java `FilePermission` compares
   canonical paths, so reads through the symlink resolve into the granted
   directory. This symlink behavior is a runtime verification item.
5. Host bind mounts of certificate files into the indexer are not a verified
   runtime path and are removed from the TLS overlay.

Strategies A (secret-free local image build) and C (official deployment model)
are recorded as follow-up options. Strategy A bakes only an empty
`${OPENSEARCH_PATH_CONF}/certs` directory and the compatibility symlink, with
no key material in image layers.

## Required layout

- `/usr/share/wazuh-indexer/certs/root-ca.pem`
- `/usr/share/wazuh-indexer/certs/indexer.pem`
- `/usr/share/wazuh-indexer/certs/indexer-key.pem` (mode `0600`)
- `/usr/share/wazuh-indexer/certs/admin.pem`
- `/usr/share/wazuh-indexer/certs/admin-key.pem` (mode `0600`)

Owner `1000:0` for all five files. The host input directory uses the official
`wazuh-certs-tool.sh` layout, including the nested `admin/` directory.

## Safety boundary

This ADR does not generate certificates, start the indexer or the manager,
apply indexer security, build or pull images, contact external hosts, or push
or merge branches. Each of those steps requires separate explicit approval.

## Verification

Static, before any runtime step:

1. Wrapper tests pass and assert the `path.conf` certificate directory.
2. Shell syntax check passes.
3. Secret scan finds no key material in the diff.
4. `git diff --check` is clean.

Runtime, only after explicit approval:

1. Start the indexer alone and confirm the OpenSearch Security init passes the
   certificate read.
2. Confirm the compatibility symlink canonicalizes into `path.conf`.
3. Confirm private keys are not readable by other UIDs.

## Rollback

Revert the wrapper, overlay, and ADR commits. Remove only local runtime
artifacts created for a test. Do not modify committed credentials.

## Consequences

- The verified blocker path is corrected instead of worked around; no Java
  SecurityManager policy change is needed.
- Private keys never appear in image layers, Git, logs, or host-visible
  process paths.
- Container start runs the wrapper as root inside the rootless namespace; the
  original entrypoint drops privileges before OpenSearch starts.
- The compatibility symlink depends on Java canonical-path comparison and must
  be confirmed at runtime.
