# Research Report: PicoFIDO (FIDO2/CTAP2 Passkey) feasibility on Raspberry Pi Pico 2 W (RP2350)

**Question:** Can a "PicoFIDO" (a FIDO2/CTAP2 passkey) run on a Raspberry Pi Pico 2 W (RP2350), and what firmware/libraries make it feasible? Realism within a ~few-month thesis timeline and a 4000 SEK hardware budget (project already owns 2× Pico 2 W).
**Date:** 2026-08-13
**Status:** Completed

---

## 1. Verdict

**Yes — it is feasible, and essentially "off-the-shelf."** A FIDO2/CTAP2.1 (and now CTAP 2.2) USB passkey runs on the Pico 2 W today via the community firmware **pico-fido** (`polhenarejos/pico-fido`), which ships prebuilt UF2 images for the `pico2` board and is actively maintained. The RP2350 has more than enough flash/RAM and the relevant crypto accelerators (SHA-256, TRNG, AES), so the hardware is not a constraint. The only meaningful gap is **BLE transport**, which no Pico FIDO firmware implements — the wireless radio on the Pico 2 W is unused for FIDO. For a thesis, the realistic deliverable is a working **USB HID passkey** (registration + authentication against a real WebAuthn/RP), achievable in hours with the prebuilt firmware and in days–weeks if you build from source and extend it. Budget is a non-issue: the project already owns the two boards; no extra hardware is required.

---

## 2. Known firmware / libraries (primary sources)

### 2.1 `polhenarejos/pico-fido` — the reference implementation
- **Repo:** https://github.com/polhenarejos/pico-fido
- **License:** GNU AGPL-3.0 (per source header in `src/fido/fido.c`: https://github.com/polhenarejos/pico-fido/blob/master/src/fido/fido.c)
- **Maintenance:** actively developed — `pushed_at` 2026-08-11, ~1,395 stars, not archived (GitHub API: https://api.github.com/repos/polhenarejos/pico-fido). Latest release **v7.0 (2025-12-03)** adds RP2354 support, FIDO 2.2, Brainpool/Ed448, `hmac-secret-mc`, `persistentPinUvAuthToken`, enterprise attestation (https://github.com/polhenarejos/pico-fido/releases/tag/v7.0). Prebuilt UF2 `pico_fido_pico-7.0.uf2` exists for the Pico 2 (`pico2`).
- **CTAP2 feature coverage (from README):** https://github.com/polhenarejos/pico-fido#readme
  - **CTAP 2.1 / CTAP 1 (U2F)**; README/product page now lists **CTAP 2.2** (https://www.picokeys.com/pico-fido/).
  - **WebAuthn / U2F** support.
  - **USB HID transport** — yes (FIDO HID usage page `0xF1D0`); source: `src/fido/hid/ctap_hid.c` and `src/fido/cbor.c` router (https://github.com/polhenarejos/pico-fido/blob/master/src/fido/cbor.c). **BLE transport — no** (no BLE CTAP implementation anywhere in the repo; the README transport list is HID/CCID only).
  - **Resident / discoverable credentials** — yes (`credential_store`, `credential_load_resident` in `src/fido/credential.c`: https://github.com/polhenarejos/pico-fido/blob/master/src/fido/credential.c).
  - **User presence (UP)** — yes, enforced via physical button (`check_user_presence` / `wait_button_pressed` in `src/fido/fido.c` and `src/fido/cmd_authenticate.c`: https://github.com/polhenarejos/pico-fido/blob/master/src/fido/cmd_authenticate.c).
  - **User verification (UV) with PIN** — yes (CTAP `authenticatorClientPIN`, `cbor_client_pin`; PIN protocol 1 & 2 in `src/fido/cbor_make_credential.c`: https://github.com/polhenarejos/pico-fido/blob/master/src/fido/cbor_make_credential.c).
  - **Attestation** — yes, self/single attestation with bundled x509 cert (`x509_crt` in `fido.c`; `x5c` emitted in MakeCredential response in `cbor_make_credential.c`).
  - **Extensions:** HMAC-Secret, CredProtect, largeBlobKey (source: `credential.c`).
  - **Curves:** ECDSA + EdDSA; secp256r1, secp384r1, secp521r1, secp256k1, Ed25519 (and v7 adds Brainpool, Ed448).
  - **Credential management** command implemented.
- **Crypto backend:** mbedTLS (`mbedtls_ecdsa`, `mbedtls_sha256`, `mbedtls_chachapoly` for credential encryption) — see `src/fido/credential.c` and `src/fido/fido.c`.

### 2.2 `librekeys/pico-fido` — maintained community/AGPL fork
- **Repo:** https://github.com/librekeys/pico-fido (explicit fork of `polhenarejos/pico-fido`: https://github.com/librekeys/pico-fido#readme)
- **License:** AGPL-3.0.
- **Maintenance:** `pushed_at` 2026-03-03, ~5 stars. Less active upstream but tracks the same feature set; adds app registration/login, 24-word backup, secure lock, permissions. Build defaults to OpenPicoKeys VID/PID `1D50:619B`.
- **Feature coverage:** identical CTAP2.1 feature matrix to upstream (USB HID, resident keys, PIN/UV, UP, attestation, HMAC-Secret, CredProtect). Good fallback if licensing/attestation identity or prebuilt binary availability matters.

### 2.3 `polhenarejos/pico-fido2` / `librekeys/pico-fido2` — FIDO + OpenPGP combos
- **Repos:** https://github.com/polhenarejos/pico-fido2 (license field null/non-AGPL, ~299 stars, last push 2026-01-29) and https://github.com/librekeys/pico-fido2 (AGPL, ~117 stars, active — last push 2026-07-23).
- Same FIDO capability as above **plus** an OpenPGP/CCID smartcard app. Uses HID for FIDO and CCID for OpenPGP. Only relevant if the thesis wants a combined FIDO+PGP token; otherwise the plain `pico-fido` is simpler.

### 2.4 Other implementations considered (not Pico-targeted)
- `solokeys/solo1` (https://github.com/solokeys/solo1) — the canonical open FIDO2 firmware, but targets **STM32L432**; portable HAL but no RP2040/RP2350 port. Useful as a reference/spec-compliance oracle (its `fido2-tests` suite is what pico-fido adapts: https://github.com/solokeys/fido2-tests).
- RIOT OS FIDO2 CTAP (https://api.riot-os.org/group__fido2.html) — RTOS-based, not Pico SDK; out of scope.
- `HamishWHC/FidoHID` — a student CTAP-HID partial implementation on ATmega32U4 (2.5 KB RAM); illustrates why a bare-metal attempt from scratch is hard, but irrelevant given pico-fido exists.

**Conclusion on libraries:** the practical path is pico-fido (mbedTLS + Pico SDK USB/flash stack). No need to write CTAP from scratch.

---

## 3. Hardware constraints on RP2350 (Pico 2 W)

Pico 2 W = RP2350A + 4 MB QSPI flash + Infineon CYW43439 wireless (wireless unused by pico-fido). Relevant limits vs. pico-fido needs:

- **Flash:** 4 MB on-board. The prebuilt `pico_fido_pico-7.0.uf2` is ~670 KB (https://github.com/polhenarejos/pico-fido/releases/tag/v7.0) — fits with large headroom for credential storage. **Sufficient.**
- **SRAM:** 520 KB on RP2350 (double the RP2040's 264 KB) — https://pip.raspberrypi.com/categories/1214-rp2350 (RP2350 product brief). mbedTLS ECDSA/P-256 signing needs only tens of KB; 520 KB is ample. **Sufficient.**
- **Crypto acceleration (RP2350 security architecture):** hardware **SHA-256 accelerator**, a hardware **TRNG** (Arm IP, "Compliance with FIPS 140-2, BSI AIS-31, and NIST SP 800-90B", ~7.5 kb/s entropy at 150 MHz — datasheet §12.12.1, discussed in https://github.com/embassy-rs/embassy/pull/3338 and the RP2350 security whitepaper https://pip.raspberrypi.com/categories/1260-security/documents/RP-009377-WP-1-Understanding%20RP2350_s%20security%20features.pdf), and an **AES** block (SCA/glitch-hardened). SHA-256 hardware gives ~14× speedup vs software (https://link.springer.com/article/10.1007/s44291-026-00253-4). pico-fido currently does ECDSA in mbedTLS software but uses SHA-256/TRNG; the accelerators are present and sufficient. **Sufficient.**
- **Key storage security:** RP2350 has **8 KB antifuse OTP** for protected key material and optional signed/encrypted boot (secure boot ROM, ACCESSCTRL bus filtering) — https://pip.raspberrypi.com/categories/1214-rp2350. The librekeys fork explicitly stores the MKEK/device key in RP2350 OTP with ECC + chaff + page locking (https://github.com/librekeys/pico-fido2#readme), which the RP2040 cannot do. This is what makes the Pico 2 W (RP2350) meaningfully more secure than an RP2040 for a passkey.
- **BLE:** not a hardware limit (CYW43439 supports BLE), but **no CTAP-over-BLE stack exists** in any Pico FIDO firmware — a firmware/effort gap, not a silicon gap.

**Net:** the RP2350 exceeds the resource requirements of a USB FIDO2 authenticator; the only hard gaps are BLE (unimplemented) and true secure-element-grade key isolation (OTP + secure boot help but it is not a vault).

---

## 4. What is realistic for the thesis vs. out of reach

**Realistic (within a few months, mostly within days):**
- Flash the prebuilt `pico_fido_pico-7.0.uf2` to a Pico 2 W, set a PIN, register a discoverable credential, and authenticate against a live WebAuthn Relying Party (browser flow) or via `libfido2`/`fido2-token -L`. Demonstrated end-to-end in an afternoon.
- Build pico-fido from source with the Pico SDK, customize attestation cert / VID-PID, and run the adapted `fido2-tests` conformance suite (https://github.com/solokeys/fido2-tests). Days.
- Leverage RP2350 security features as a **thesis contribution**: store the MKEK in OTP, enable signed/encrypted boot, demonstrate "secure lock" against flash dump — i.e. position the Pico 2 W passkey as more tamper-resistant than an RP2040 one. Weeks.
- Use the second owned board for a duplicated/backup token or an A/B comparison (RP2350 vs RP2040) — no cost.

**Out of reach / not worth it for the timeline:**
- **BLE/CTAP-over-BLE passkey** (e.g. phone-as-authenticator via NFC/ble). No Pico firmware implements CTAP BLE; building it means writing a BLE GATT CTAP stack from scratch on the CYW43439 — months, high risk. Avoid.
- **NFC transport** — likewise unimplemented on Pico (it exists on Solo/STM32). Avoid.
- **FIPS/Common Criteria certification or secure-element equivalence** — RP2350 OTP + secure boot raise the bar but do not make it a certified vault. Frame as "hardware-assisted," not "certified."
- **From-scratch CTAP implementation** — unnecessary given pico-fido; only justified if the thesis is specifically about protocol implementation (then base it on pico-fido source, not from zero).

---

## 5. Recommendation

Take the **prebuilt-firmware + source-extend** path, not a from-scratch build:

1. **Primary firmware:** `polhenarejos/pico-fido` (AGPL-3.0, actively maintained, prebuilt `pico2` UF2, CTAP 2.1/2.2, USB HID, resident creds, PIN/UV, UP button, attestation). Flash it to one of the two owned Pico 2 W boards and demonstrate a real WebAuthn login as the baseline deliverable.
2. **If you need a libre/AGPL combo or source-level hacking room:** use the `librekeys/pico-fido` (or `librekeys/pico-fido2` for FIDO+OpenPGP) fork, which already exploits RP2350 OTP secure storage.
3. **Scope the thesis contribution around RP2350 security**, not BLE: enable OTP MKEK storage + signed/encrypted boot and compare tamper-resistance vs RP2040. This is novel, on-hardware, and fits a few months.
4. **Budget:** 0 SEK of the 4 000 SEK is required — the two Pico 2 W boards are already owned; at most spend on a button/LED breakout or a second board (~100–200 SEK) for redundancy. Keep the rest as contingency.
5. **Explicitly exclude BLE/NFC** from scope to protect the timeline.

---

## Primary-source URLs

- https://github.com/polhenarejos/pico-fido
- https://github.com/polhenarejos/pico-fido/releases/tag/v7.0
- https://github.com/polhenarejos/pico-fido/blob/master/src/fido/fido.c
- https://github.com/polhenarejos/pico-fido/blob/master/src/fido/cbor.c
- https://github.com/polhenarejos/pico-fido/blob/master/src/fido/credential.c
- https://github.com/polhenarejos/pico-fido/blob/master/src/fido/cmd_authenticate.c
- https://github.com/polhenarejos/pico-fido/blob/master/src/fido/cbor_make_credential.c
- https://github.com/librekeys/pico-fido
- https://github.com/librekeys/pico-fido2
- https://github.com/polhenarejos/pico-fido2
- https://www.picokeys.com/pico-fido/
- https://pip.raspberrypi.com/categories/1214-rp2350 (RP2350 product brief / datasheet)
- https://pip.raspberrypi.com/categories/1260-security/documents/RP-009377-WP-1-Understanding%20RP2350_s%20security%20features.pdf
- https://github.com/embassy-rs/embassy/pull/3338 (RP2350 TRNG datasheet details)
- https://link.springer.com/article/10.1007/s44291-026-00253-4 (RP2350 SHA-256 acceleration benchmarks)
- https://github.com/solokeys/solo1 (reference FIDO2 firmware, STM32)
- https://github.com/solokeys/fido2-tests (conformance suite pico-fido adapts)
- https://api.riot-os.org/group__fido2.html (RIOT CTAP, reference)
