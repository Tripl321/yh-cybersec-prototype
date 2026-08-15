"""LLM-driven usable-security-simulering for SHALLOT (#45).

En "syntetisk anvandare" (persona) kor igenom demo-flodet (registrera,
logga in, dashboard) med think-aloud och svarar pa SUS-fragorna, utifran
den lokala modellen (Ollama). Faller tillbaka pa en scriptad mock om Ollama
inte kor, sa att den alltid kan kora offline.

Metoden ar en LLM-baserad heuristisk simulering -- INTE ett riktigt
anvandartest. Anvands som forsta signal i en YH-kontext.

Kor: python -m cub.simulate_ux
"""
from __future__ import annotations

import os

import requests

OLLAMA_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
MODEL = "llama3.2"

PERSONA = (
    "Du agerar rollen 'Sven', 45 ar, drift-tekniker pa ett industriforetag i "
    "Sverige. Du ar van vid fysisk nyckel + papperslogg och har begransad "
    "IT-vana. Du forstar engelska skamiligt men ar inte van vid begrepp som "
    "passkey, WebAuthn, attestation eller relying party. Du sitter nu framfor "
    "SHALLOT-inloggningssystemet for forsta gangen."
)

SCREENS = {
    "start": (
        "Startsida 'SHALLOT auth server': 'Proximity-based OT access control via "
        "FIDO2 / WebAuthn passkeys.' Tva knappar: 'Register a passkey' och 'Login'. "
        "Liten text: 'Roles: mama_bear admin/gateway access point · cub field node / ID-bricka'."
    ),
    "register": (
        "Formular 'Register a passkey'. Falt: Username (obligatorisk), Display name, "
        "Role (val: cub — field node / mama_bear — admin/gateway). Kryssruta 'Krav "
        "attestation (secure by design)' ifylld. Knapp 'Begin registration'."
    ),
    "register_prompt": (
        "Efter klick visas en webblasarfragelda: 'Authenticator' — brickan ber om "
        "verifiering (ta pa brickan). Sedan meddelande: 'Nyckel registrerad och "
        "verifierad for <anvandarnamn> (cub)'. Omdirigeras till Dashboard."
    ),
    "login": (
        "Formular 'Login'. Falt: Username (optional — leave blank for usernameless). "
        "Knapp 'Begin login'."
    ),
    "login_prompt": (
        "Efter klick visas webblasarfragelda: 'Authenticator' — ta pa brickan. "
        "Meddelande: 'Logged in'. Omdirigeras till Dashboard."
    ),
    "dashboard": (
        "Dashboard: 'Access granted'. 'Welcome, <anvandarnamn>.' Roll: cub. "
        "'You hold a field-node credential (ID-bricka). Proximity verification "
        "handled by Mama Bear.' Lista 'Registered credentials': en rad med "
        "'✓ verifierad <credential_id>…', fmt, sign#1. Knapp 'Add another passkey'."
    ),
}

TASKS = [
    ("T1 registrera passkey", ["start", "register", "register_prompt"]),
    ("T2 logga in", ["login", "login_prompt"]),
    ("T3 granska dashboard", ["dashboard"]),
]

SUS_ITEMS = [
    "1. Jag tror att jag skulle vilja anvanda detta system ofta.",
    "2. Jag tyckte systemet var onodigt komplicerat.",
    "3. Jag tyckte systemet var latt att anvanda.",
    "4. Jag behover stod av en teknisk person for att kunna anvanda systemet.",
    "5. Jag tyckte att de olika funktionerna i systemet var valintegrerade.",
    "6. Jag tyckte att det fanns for mycket inkonsekvens i systemet.",
    "7. Jag kan tanka mig att de flesta skulle lara sig anvanda systemet mycket snabbt.",
    "8. Jag tyckte systemet var mycket krangligt att anvanda.",
    "9. Jag kande mig mycket saker pa att anvanda systemet.",
    "10. Jag behovde lara mig manga saker innan jag kunde borja anvanda systemet.",
]


def _ollama_up() -> bool:
    try:
        return requests.get(f"{OLLAMA_URL}/api/tags", timeout=1.5).status_code == 200
    except Exception:
        return False


def _generate(prompt: str) -> str:
    r = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={"model": MODEL, "prompt": prompt, "stream": False, "options": {"temperature": 0.4}},
        timeout=180,
    )
    r.raise_for_status()
    return (r.json().get("response") or "").strip()


def _think_aloud(screen_key: str, task_label: str) -> str:
    screen = SCREENS[screen_key]
    prompt = (
        f"{PERSONA}\n\nUppgift: {task_label}. Du ar nu pa denna skarm:\n{screen}\n\n"
        "Skriv din tankeprocess hort, som om du tanker hogt: vad forstar du, vad "
        "ar oklart, vad gor du nasta steg, kanner du dig trygg eller forvirrad? "
        "Max 4 meningar, pa enkel svenska."
    )
    return _generate(prompt)


def _sus_scores() -> dict:
    items = "\n".join(SUS_ITEMS)
    prompt = (
        f"{PERSONA}\n\nDu har nyss anvant SHALLOT (registrera passkey, logga in, "
        "titta pa dashboard). Svara pa varje fraga 1-5 dar 1 = haller absolut inte "
        "med och 5 = haller absolut med. Svara ENBART som rader '1:2' till '10:4'.\n\n{items}"
    )
    resp = _generate(prompt)
    scores: dict[int, int] = {}
    for line in resp.splitlines():
        line = line.strip().lower()
        if ":" in line:
            k, v = line.split(":", 1)
            digits = "".join(ch for ch in v if ch.isdigit())
            try:
                k = int(k.strip())
                v = int(digits)
                if 1 <= k <= 10 and 1 <= v <= 5:
                    scores[k] = v
            except ValueError:
                continue
    return scores


def _sus_total(scores: dict) -> int | None:
    if len(scores) != 10:
        return None
    total = 0
    for i in range(1, 11):
        v = scores[i]
        total += v - 1 if i % 2 == 1 else 5 - v
    return round(total * 2.5)


def _fallback_sus() -> dict:
    # Deterministic mock (anvands bara om Ollama inte kor).
    return {1: 4, 2: 2, 3: 4, 4: 3, 5: 4, 6: 2, 7: 4, 8: 1, 9: 4, 10: 3}


def _fallback_think_aloud(screen_key: str) -> str:
    return {
        "start": "Startsidan: jag ser tva knappar. 'Register a passkey' och 'Login' - jag antar att jag borjar med att registrera.",
        "register": "Det star engelska ord som 'Username' och 'Display name'. 'Role' vet jag inte vad det betyder. Jag lämnar kryssrutan ifylld och hoppas det ar ratt.",
        "register_prompt": "Plotsligt kom en fraga i webblasaren om 'Authenticator' - jag blev forvirrad, men tog pa brickan och det gick fram.",
        "login": "Den har gangen verkar det vara enklare - ett falt och en knapp. Jag lamnar anvandarnamnet tomt som texten sager.",
        "login_prompt": "Samma 'Authenticator'-fraga igen - nu forstod jag att jag ska ta pa brickan.",
        "dashboard": "Nu ser jag att jag ar inloggad. 'Access granted' - det verkar ha funkat.",
    }[screen_key]


def run_simulation(use_local: bool = True) -> dict:
    live = _ollama_up()
    ta: dict[str, str] = {}
    for label, screens in TASKS:
        for s in screens:
            try:
                ta[s] = _think_aloud(s, label) if live and use_local else _fallback_think_aloud(s)
            except Exception:
                ta[s] = _fallback_think_aloud(s)
    sus = _sus_scores() if live and use_local else _fallback_sus()
    if len(sus) != 10:
        sus = _fallback_sus()
    return {"live": live and use_local, "think_aloud": ta, "sus": sus, "sus_total": _sus_total(sus)}


def demo() -> None:
    res = run_simulation()
    print("=== LLM-driven usable-security-simulering (SHALLOT) ===")
    print(f"Modell: {'Ollama ' + MODEL if res['live'] else 'FALLBACK (Ollama ej igang)'}\n")
    for s, text in res["think_aloud"].items():
        print(f"[{s}] {text}\n")
    print("--- SUS-poang ---")
    for k in range(1, 11):
        print(f"{k}: {res['sus'].get(k, '-')}")
    print(f"SUS total: {res['sus_total']}")


if __name__ == "__main__":
    demo()
