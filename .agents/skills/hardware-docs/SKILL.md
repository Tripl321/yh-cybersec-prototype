---
name: hardware-docs
description: Add hardware documentation, datasheets, and component info to the SHALLOT components database. Use when the user says "add this", "save this datasheet", "document this component", "lägg till", or shares a URL/file for hardware documentation.
---

# Skill: hardware-docs

Add materials to the SHALLOT components database in a conversational way.

## When to use

Trigger on phrases like:
- "Add this PDF to the docs"
- "Save this datasheet"
- "Document this component"
- "Lägg till denna PDF"
- "Spara denna datasheet"
- "Add to hardware docs"
- User shares a URL to a PDF/datasheet
- User shares a local file path

## Workflow

### 1. Identify the content

Determine what the user wants to add:
- **URL** → Download the file
- **Local file** → Use the file directly
- **Text description** → Create a markdown note
- **Image** → Download and optionally OCR

### 2. Identify the component

Ask or infer which component this relates to:
- ESP32-S3-nano (PicoFIDO)
- RP2350 (Field node)
- Arduino UNO Q (Gateway)
- LoRa SX1262 (Radio)
- E-paper (Display)
- LiPo (Battery)
- MOSFET/Fläkt (Thermal)
- Other (specify)

If unclear, ask: "Vilken komponent gäller detta?"

### 3. Process the material

#### For URLs:
```bash
# Create temp directory
mkdir -p /tmp/shalot-material

# Download the file
curl -L -o /tmp/shalot-material/<filename> "<url>"

# Copy to material directory
cp /tmp/shalot-material/<filename> docs/hardware/material/

# Process with script
cd docs/hardware
python process-material.py material/<filename> --component "<component_name>"
```

#### For local files:
```bash
# Copy to material directory
cp <source_path> docs/hardware/material/

# Process with script
cd docs/hardware
python process-material.py material/<filename> --component "<component_name>"
```

#### For text descriptions:
```bash
# Create a markdown file
cat > docs/hardware/material/<component>-notes.md << 'EOF'
# <Component> Notes

<user's description>

## Key Specifications
- [Extract from description]

## Notes
- Added by user on <date>
EOF

# Process with script
cd docs/hardware
python process-material.py material/<component>-notes.md --component "<component_name>"
```

### 4. Confirm to user

After processing, confirm:
- File was saved
- Component was tagged
- Index was updated
- Any extracted text preview

Example confirmation:
```
Sparat: sx1262-datasheet.pdf
Komponent: LoRa SX1262
Hash: abc123def456
Extraherad text: 2347 tecken
```

### 5. Update components.md (if needed)

If the material contains significant new information (new pinout, specs, corrections), update `docs/hardware/components.md` accordingly.

## File naming convention

Use descriptive names:
- `<component>-datasheet.pdf`
- `<component>-photo.jpg`
- `<component>-notes.md`
- `<component>-wiring.png`

## Tips

- Always ask for component name if not clear
- For PDFs, mention if text extraction worked
- For images, mention if OCR was performed
- Remind user they can run `python process-material.py --list` to see all materials
- If the material contains pinouts or specs, suggest updating components.md

## Example interactions

**User:** "Lägg till denna PDF: https://cdn-learn.adafruit.com/downloads/pdf/adafruit-feather-rp2350.pdf"

**Agent:**
1. Downloads PDF to `docs/hardware/material/adafruit-feather-rp2350.pdf`
2. Processes with `python process-material.py material/adafruit-feather-rp2350.pdf --component "RP2350"`
3. Confirms: "Sparat och indexarat. Innehåller 4500 tecken text. Vill du att jag uppdaterar components.md med några nya specifikationer?"

---

**User:** "Spara denna bild på min anslutning"

**Agent:**
1. Asks for file path or URL
2. Downloads/copies to material directory
3. Processes with appropriate component tag
4. Confirms save

---

**User:** "Jag hittade bra info om SX1262's strömförbrukning"

**Agent:**
1. Asks for the information (URL, file, or text)
2. Processes accordingly
3. Updates components.md §6 (LoRa SX1262) with new power specs if relevant
