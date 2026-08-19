# 0009 — Epoch context in auth frame

Auth frame includes `day` field (4 bytes) for offline revocation. FIDO Key signs `badge_id + nonce + day`, not just nonce.

## Why

Without epoch, the FIDO Key's HMAC secret is static. A stolen auth frame can be replayed forever. With day, each day's signature is different. Mama Bear can revoke a badge by advancing the calendar past its `valid_until` day — no network call needed.

## Consequences

- Auth frame grows from 41 to 45 bytes (still well within LoRa MTU).
- PAW and Field Node must agree on current day (synced via Mama Bear USB-serial).
- FIDO Key signing includes day, so signature changes daily even with same nonce.
- Offline revocation: Field Node checks `day <= valid_until` before accepting auth.
