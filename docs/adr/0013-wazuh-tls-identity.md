# ADR 0013: Wazuh TLS identity and verification boundary

- Status: Proposed
- Date: 2026-10-18
- Related: issue #94

## Context

Wazuh TLS must be designed before indexer security configuration or runtime start.
The credential bootstrap is intentionally separate and does not create certificates,
apply indexer security, start services, or contact external hosts.

## Decision

The primary TLS identity is `wazuh-indexer.local`.
The certificate Subject Alternative Name list is:

- DNS: `wazuh-indexer.local`
- DNS: `localhost`
- IP: `127.0.0.1`

The design uses a local CA and separate node/client certificates. Private keys
must remain local, must never be committed, and must use mode `0600`. Public
certificates and CA material may be distributed only after review.

## Required layout

The implementation must define explicit paths before deployment:

- local CA private key: secret, mode `0600`
- indexer private key: secret, mode `0600`
- indexer certificate: public certificate, restrictive ownership
- CA certificate: public trust material
- trust-store configuration: no embedded secrets

The exact paths remain an implementation decision and must not be inferred
from the credential bootstrap output.

## Verification boundary

Before runtime start, verification must confirm:

1. SANs exactly cover `wazuh-indexer.local`, `localhost`, and `127.0.0.1`.
2. The certificate chains to the intended local CA.
3. The private key matches the certificate.
4. Private-key files have mode `0600` and the intended owner.
5. The indexer configuration references the intended certificate and trust paths.
6. No certificate or key is embedded in Git, logs, command output, or issue text.
7. A TLS client rejects the endpoint when the hostname is outside the SAN list.
8. Verification is read-only and does not start Wazuh.

## Safety boundary

This ADR does not generate certificates, create private keys, apply indexer
security configuration, pull images, start services, modify firewall rules,
or connect to external hosts. Those actions require separate reviewed steps.

## Consequences

- Hostname verification works for the chosen local names.
- IP-based localhost verification is explicit rather than accidental.
- A future runtime must not silently fall back to insecure TLS settings.
- Certificate generation and deployment remain auditable, separate operations.
