# Contact-auth repository consolidation

This module was selectively migrated from
[`Tripl321/yh-contact-auth-projektarbete`](https://github.com/Tripl321/yh-contact-auth-projektarbete)
at source commit `c6bd6d809a017c49abd3225009671c0c20d7a69a`.

`Tripl321/yh-cybersec-prototype` is the canonical SHALLOT repository. New
contact-auth firmware, protocol, test, and documentation changes belong under
`hardware/contact-auth/` in the canonical repository.

## Included

- PAW and DEN firmware
- Mama Bear key-authority code
- UART and cryptographic support libraries
- SHALLOT CLI source and tests
- Security, protocol, hardware, and framework documentation
- The archived PAW responder and nested historical workflow because active
  source-guard tests still require them as fixtures

The nested `.github/workflows/build-paw-uf2.yml` is a test fixture only. GitHub
does not execute workflows outside the repository-root `.github/workflows/`
directory.

## Excluded

- Generated `*.egg-info` metadata
- Mama Bear status JSON dumps
- Upload-test scratch files
- IDE-specific `.theia` configuration
- Weekly status reports, generic document templates, reminders, and empty assets

## Test baseline

At migration time, both the source repository and this module report:

- 282 passed
- 4 skipped
- 2 failed

The two known failures are:

- `tests/test_pro45_key_generation.py::test_pro45_uses_stm32_rng`
- `tests/test_pro45_key_generation.py::test_pro45_rng_registers_documented`

They predate the migration and represent PRO-45 source/test drift. CI accepts
only those two exact failures. Any additional failure is a regression; if both
are fixed, CI intentionally fails until the known-failure baseline is removed.

## Safety boundary

The migration copies repository content only. It does not build or flash
firmware, contact Mama Bear, connect to a VPS or physical device, modify radio
settings, or execute the nested historical GitHub Actions workflow.

The source repository must not be archived until this migration PR is merged,
CI is green, and a separate human approval is recorded.
