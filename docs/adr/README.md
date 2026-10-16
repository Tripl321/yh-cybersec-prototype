# Architecture Decision Records — SHALLOT

Korta beslutsanteckningar. Format: se `.agents/skills/domain-modeling/ADR-FORMAT.md`.

- [0001-webauthn-rp-library](0001-webauthn-rp-library.md) — `demo/` använder `webauthn`, inte `py-webauthn`.
- [0002-dev-relying-party-localhost](0002-dev-relying-party-localhost.md) — Demo-RP på localhost:8000, `rp.id` härledd från `Host`, `attestation=none`.
- [0003-access-roles-mama-bear-cub](0003-access-roles-mama-bear-cub.md) — Roller `mama_bear` / `cub` som WebAuthn-users.
- [0010-standalone-shallot-harness](0010-standalone-shallot-harness.md) — Fristående personlig agentplattform med ACP, granskat minne och multi-worker-mål.
- [0011-ansible-rootless-quadlet-lab](0011-ansible-rootless-quadlet-lab.md) — Lokal Ansible-baseline och rootless Quadlet-målbild.
- [0012-consolidate-contact-auth-repository](0012-consolidate-contact-auth-repository.md) — Ett kanoniskt SHALLOT-repo med kontakt-autentisering under `hardware/contact-auth/`.

Se även [GLOSSARY.md](GLOSSARY.md) för domänmodellen.
