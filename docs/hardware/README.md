# SHALLOT Hardware Documentation

> Kunskapsbas för all hårdvara i SHALLOT-prototypen.

## Struktur

```
docs/hardware/
├── components.md          # Strukturerad kunskapsbas (opencode läser här)
├── process-material.py    # Script för att processa material
├── download-material.sh   # Snabb nedladdning från URL
├── material-index.json    # Index över allt material (auto-genererad)
├── README.md              # Denna fil
└── material/              # Råmaterial (PDF, bilder, datasheets)
    ├── template-datasheet.md
    └── [dina filer här]
```

## Snabbstart

### 1. Lägg till material via URL
```bash
./download-material.sh https://example.com/datasheet.pdf --component "LoRa SX1262"
```

### 2. Lägg till lokala filer
```bash
cp ~/Downloads/manual.pdf material/rp2350-manual.pdf
python process-material.py material/rp2350-manual.pdf --component "RP2350"
```

### 3. Lägg till textnoteringar
```bash
python process-material.py material/my-notes.md --component "Arduino UNO Q"
```

### 4. Se allt material
```bash
python process-material.py --list
python process-material.py --index
```

## Konversationellt (via opencode)

Använd `hardware-docs`-skillet för att lägga till material i konversationell stil:

> "Lägg till denna PDF: https://cdn-learn.adafruit.com/downloads/pdf/adafruit-feather-rp2350.pdf"

> "Spara denna datasheet för SX1262"

> "Dokumentera denna komponent"

opencode hanterar nedladdning, processning och indexering.

## Formát som stöds

- **PDF:** Extraherar text (kräver PyMuPDF: `pip install PyMuPDF`)
- **Bilder (JPG/PNG):** OCR med Tesseract (kräver: `pip install pytesseract Pillow`)
- **Markdown/Txt:** Läser direkt

## Underhåll

- Uppdatera `components.md` när du får ny kunskap om komponenter
- Lägg till nya filer i `material/` och kör scriptet
- Kommentarer och noteringar sparas i indexet
