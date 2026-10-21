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
3. The wrapper runs as the image user (UID 1000) under
   `userns_mode: keep-id`, which maps the host user to the same container
   UID so the read-only host input directory stays readable. It refuses to
   run as root. No capabilities are needed: `/usr/share/wazuh-indexer` is
   `0700` owned `1000:1000` in the image, so the wrapper can create
   `certs/` in its own path.conf directory and the base Compose
   `cap_drop: ALL` stays in force. Staged files end up owned `1000:1000`
   with the existing mode table (private keys `0600`), and the original
   entrypoint executes directly as UID 1000.
4. The certificate path strings in `opensearch.yml` must also live under
   `path.conf`. The image default `opensearch.yml` references
   `/etc/wazuh-indexer/certs`; a corrected copy of the file (see
   `shallot-infra/config/wazuh_indexer/opensearch.yml`) is bind-mounted
   read-only, as in the official deployment model. A symlink from
   `/etc/wazuh-indexer` does **not** work: the runtime probe showed that the
   `FilePermission` check uses the literal configured path. Environment-based
   SSL settings are also inert in this image because
   `OPENSEARCH_DISTRIBUTION_TYPE` is `rpm`, so the image's env-to-`-E`
   conversion never runs.
5. The corrected `opensearch.yml` sets `discovery.type: single-node` and drops
   `cluster.initial_master_nodes`, because the image's env override for
   `discovery.type` is inert and the two settings are mutually exclusive.
6. Host bind mounts of certificate files into the indexer are not a verified
   runtime path and are removed from the TLS overlay.

Strategies A (secret-free local image build) and C (official deployment model)
are recorded as follow-up options. Strategy A bakes only an empty
`${OPENSEARCH_PATH_CONF}/certs` directory, with no key material in image
layers.

## Required layout

- `/usr/share/wazuh-indexer/certs/root-ca.pem`
- `/usr/share/wazuh-indexer/certs/indexer.pem`
- `/usr/share/wazuh-indexer/certs/indexer-key.pem` (mode `0600`)
- `/usr/share/wazuh-indexer/certs/admin.pem`
- `/usr/share/wazuh-indexer/certs/admin-key.pem` (mode `0600`)

Owner `1000:1000` for all five files. The host input directory uses the
official `wazuh-certs-tool.sh` layout, including the nested `admin/`
directory.

## Safety boundary

This ADR does not generate certificates, start the indexer or the manager,
apply indexer security, build or pull images, contact external hosts, or push
or merge branches. Each of those steps requires separate explicit approval.
Indexer-only runtime probes were performed on 2026-10-19 under explicit human
approval; see Runtime evidence.

## Verification

Static, before any runtime step:

1. Wrapper tests pass and assert the `path.conf` certificate directory.
2. Shell syntax check passes.
3. Secret scan finds no key material in the diff.
4. `git diff --check` is clean.

Runtime, only after explicit approval:

1. Start the indexer alone and confirm the OpenSearch Security init passes the
   certificate read. (Done; see Runtime evidence.)
2. Confirm private keys are not readable by other UIDs. (Done; see Runtime
   evidence.)

## Runtime evidence

Probe series on 2026-10-19, rootless Podman, indexer only, no
`securityadmin.sh`, no manager, explicit human approval per start:

1. Wrapper staging plus a `/etc/wazuh-indexer` symlink, image default
   `opensearch.yml`: `AccessControlException` on the literal path
   `/etc/wazuh-indexer/certs/indexer.pem`. Symlinks do not satisfy the check.
2. SSL environment overrides to `path.conf`: identical
   `AccessControlException`. The env-to-`-E` conversion in `bin/opensearch`
   is gated on `OPENSEARCH_DISTRIBUTION_TYPE=docker`; the image sets `rpm`.
3. Corrected `opensearch.yml` with `path.conf` certificate paths, 256m heap:
   certificate read passed (SSLConfig initialized). JVM died with
   `OutOfMemoryError` on direct buffer memory.
4. 512m heap: same direct-buffer OOM (needs ~291 MB).
5. 1g heap plus `discovery.type: single-node` and without
   `cluster.initial_master_nodes`: indexer started, cluster health GREEN,
   security index initialized automatically (no `securityadmin.sh`), HTTPS
   answered on 127.0.0.1:9200.
   Correction on 2026-10-21: the security index was in fact **not**
   initialized. The image entrypoint runs `securityadmin.sh` only in a
   commented-out block, and the plugin creates the index only with
   `plugins.security.allow_default_init_securityindex: true`, which the
   corrected `opensearch.yml` lacked. The GREEN cluster health above was
   an unsecured cluster. The flag is now set, matching the official
   Wazuh 4.9.0 single-node config (ADR 0016).
6. Wrapper staging as container root with the Compose `cap_drop: ALL`:
   `install` failed with `Permission denied` on
   `/usr/share/wazuh-indexer`, which the image sets to `0700` owned
   `1000:1000`. Root without `DAC_OVERRIDE` cannot traverse it. This
   motivated decision item 3: stage as the image user under `keep-id`.
7. Final configuration, committed wrapper plus corrected `opensearch.yml`,
   `userns_mode: keep-id`, `cap_drop: ALL` plus `IPC_LOCK`, 1g heap: cluster
   health GREEN, HTTPS answered, and no `AccessControlException`. Verified
   after start: served certificate `CN=wazuh-indexer.local` with SAN exactly
   `DNS:wazuh-indexer.local, DNS:localhost, IP:127.0.0.1`; staged keys mode
   `0600` and public material `0644`, all owner `1000:1000`; the JVM process
   UID from `/proc` was `1000`; no key material in logs.

Post-run verification in step 5:

- Served certificate: `CN=wazuh-indexer.local`, SAN exactly
  `DNS:wazuh-indexer.local, DNS:localhost, IP:127.0.0.1`, issued by the local
  SHALLOT lab CA.
- Staged files: `indexer-key.pem` and `admin-key.pem` mode `0600`, public
  material `0644`, all owner `1000:0`.
- No key material in container logs (0 matches for `PRIVATE KEY`).
- Probe container, probe input copies, and probe configuration were removed
  afterwards; the pre-existing local TLS material was not modified.

Follow-up on 2026-10-19: `authcz.admin_dn` and `nodes_dn` in the corrected
`opensearch.yml` were aligned to the lab CA (`CN=admin,O=SHALLOT Local Lab,C=SE`
and `CN=wazuh-indexer.local,O=SHALLOT Local Lab,C=SE`). Re-verified rootless
(`keep-id`, `cap_drop: ALL`): cluster GREEN, and an admin-client request with
the lab admin certificate returned HTTP 200 on `https://127.0.0.1:9200/`.
No certificate or key was regenerated.

## Rollback

Revert the wrapper, overlay, and ADR commits. Remove only local runtime
artifacts created for a test. Do not modify committed credentials.

## Consequences

- The verified blocker path is corrected instead of worked around; no Java
  SecurityManager policy change is needed.
- Private keys never appear in image layers, Git, logs, or host-visible
  process paths.
- Container start never uses UID 0: the wrapper and the indexer both run as
  the image user under `keep-id`, and the base `cap_drop: ALL` remains in
  force.
- The corrected `opensearch.yml` is a maintained copy of the image default;
  image upgrades require re-checking it against the new default.
- Environment-based OpenSearch settings are inert in this image, so
  configuration changes must go through `opensearch.yml`.
