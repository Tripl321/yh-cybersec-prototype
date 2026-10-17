# Wazuh TLS verification checklist

Use this checklist after certificate generation and before any indexer-security
application or runtime start. It is intentionally non-executing documentation.

## Identity

- [ ] Certificate contains DNS SAN `wazuh-indexer.local`.
- [ ] Certificate contains DNS SAN `localhost`.
- [ ] Certificate contains IP SAN `127.0.0.1`.
- [ ] No unapproved DNS names or IP addresses are present.

## Key and certificate integrity

- [ ] Private keys are local-only and absent from Git.
- [ ] Private keys have mode `0600`.
- [ ] Private keys have the intended owner.
- [ ] Certificate and private-key public parameters match.
- [ ] Certificate chains to the intended local CA.

## Configuration

- [ ] Indexer TLS paths are explicit and reviewed.
- [ ] Trust-store path is explicit and reviewed.
- [ ] Hostname verification remains enabled.
- [ ] No `verify_certs: false`, insecure skip, or trust-all setting exists.
- [ ] No private key or password appears in configuration or logs.

## Read-only verification

- [ ] `openssl x509` inspection completed without printing private material.
- [ ] SAN and issuer checks passed.
- [ ] TLS client verification passed for `wazuh-indexer.local`.
- [ ] TLS client verification passed for `localhost`.
- [ ] TLS client verification passed for `127.0.0.1`.
- [ ] An unlisted hostname fails verification.
- [ ] No service was started during verification.

## Approval gates

- [ ] Human review completed for certificate layout.
- [ ] Separate approval received before applying indexer security.
- [ ] Separate approval received before starting Wazuh runtime.
- [ ] Backup and rollback plan reviewed.
