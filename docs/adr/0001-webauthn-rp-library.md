# WebAuthn-bibliotek för relying party

SHALLOT:s demo/auth-server (`demo/`) använder `webauthn` (pyauth, v3.x) som FIDO2/WebAuthn-beroende — inte `py-webauthn`.

`demo/pyproject.toml` angav ursprungligen `py-webauthn>=2.0`, men det namnet på PyPI pekar på ett annat, gammalt bibliotek (0.0.6, helt annan API). Det moderna biblioteket med `generate_registration_options` / `verify_registration_response` publiceras som `webauthn`. Valet är svårt att backa (låst i kod och test) och överraskande för den som läser pyproject, därav denna ADR.

**Consequences:** Byte av beroende krävde uppdatering av `pyproject.toml` och ominstallation. `py-webauthn` får inte finnas i samma miljö (namnkrock i `webauthn`-modulen).
