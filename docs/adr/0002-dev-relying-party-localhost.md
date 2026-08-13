# Demo-RP kör på localhost med Host-härledd rp.id

`demo/`-servern är en prototyp-RP som binder på `::`:8000 och härleder `rp.id`/`origin` från den inkommande `Host`-headern; `attestation=none`.

WebAuthn kräver en secure context. På macOS blockerar Control Center (AirPlay-mottagare) port 5000, så default-porten är 8000. `rp.id` härleds från `Host` så att `localhost` och `127.0.0.1` matchar browserns ursprung — annars kastar browsern "invalid domain".

**Considered Options:** hårdkodad `rp.id` ("localhost") vs härledd från `Host`. Härledd valdes för demo-enkelhet (fungerar oavsett om användaren öppnar `localhost` eller `127.0.0.1`).

**Consequences:** I produktion måste `rp.id`/`origin` vara hårdkodade/allow-list:ade, eftersom `Host`-headern är attacker-kontrollerbar. Demonstratorn är inte produktionshärdad (se kartans *Out of scope*).
