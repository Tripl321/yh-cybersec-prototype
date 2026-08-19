#!/usr/bin/env python3
"""
SHALLOT Material Processor
Process material (PDF, images, markdown) and add to components database.

Usage:
    python process-material.py <file> [--component <name>]
    python process-material.py --list
    python process-material.py --index

Examples:
    python process-material.py sx1262-datasheet.pdf --component "LoRa SX1262"
    python process-material.py esp32-photo.jpg --component "ESP32-S3-nano"
    python process-material.py notes.md --component "RP2350"
"""

import sys
import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional

# Paths
HARDWARE_DIR = Path(__file__).parent.parent
MATERIAL_DIR = HARDWARE_DIR / "material"
INDEX_FILE = HARDWARE_DIR / "material-index.json"
COMPONENTS_FILE = HARDWARE_DIR / "components.md"


def get_file_hash(filepath: Path) -> str:
    """Get SHA256 hash of file for deduplication."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()[:12]


def load_index() -> dict:
    """Load or create material index."""
    if INDEX_FILE.exists():
        with open(INDEX_FILE, "r") as f:
            return json.load(f)
    return {"materials": [], "last_updated": None}


def save_index(index: dict):
    """Save material index."""
    index["last_updated"] = datetime.now().isoformat()
    with open(INDEX_FILE, "w") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
    print(f"Index saved to {INDEX_FILE}")


def extract_text_from_pdf(filepath: Path) -> Optional[str]:
    """Extract text from PDF (requires PyMuPDF)."""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(str(filepath))
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text[:5000]  # First 5000 chars
    except ImportError:
        print("Warning: PyMuPDF not installed. Install with: pip install PyMuPDF")
        return None
    except Exception as e:
        print(f"Error extracting PDF text: {e}")
        return None


def extract_text_from_image(filepath: Path) -> Optional[str]:
    """Extract text from image using OCR (requires pytesseract)."""
    try:
        from PIL import Image
        import pytesseract
        img = Image.open(str(filepath))
        text = pytesseract.image_to_string(img)
        return text[:5000]  # First 5000 chars
    except ImportError:
        print("Warning: OCR not available. Install with: pip install pytesseract Pillow")
        return None
    except Exception as e:
        print(f"Error OCR'ing image: {e}")
        return None


def process_file(filepath: Path, component: str = "Unknown") -> dict:
    """Process a single file and return metadata."""
    filepath = Path(filepath)
    
    if not filepath.exists():
        print(f"Error: File not found: {filepath}")
        sys.exit(1)
    
    file_hash = get_file_hash(filepath)
    file_ext = filepath.suffix.lower()
    
    # Extract text based on file type
    extracted_text = None
    if file_ext == ".pdf":
        extracted_text = extract_text_from_pdf(filepath)
    elif file_ext in [".jpg", ".jpeg", ".png", ".tiff"]:
        extracted_text = extract_text_from_image(filepath)
    elif file_ext in [".md", ".txt"]:
        with open(filepath, "r") as f:
            extracted_text = f.read()[:5000]
    
    # Create entry
    try:
        filepath_str = str(filepath.relative_to(HARDWARE_DIR))
    except ValueError:
        filepath_str = filepath.name
    
    entry = {
        "filename": filepath.name,
        "filepath": filepath_str,
        "hash": file_hash,
        "component": component,
        "file_type": file_ext,
        "size_bytes": filepath.stat().st_size,
        "added_date": datetime.now().isoformat(),
        "extracted_text": extracted_text,
        "notes": ""
    }
    
    return entry


def add_to_index(entry: dict):
    """Add entry to index (deduplicate by hash)."""
    index = load_index()
    
    # Check for duplicates
    existing_hashes = [m["hash"] for m in index["materials"]]
    if entry["hash"] in existing_hashes:
        print(f"Warning: File already in index (hash: {entry['hash']})")
        return
    
    index["materials"].append(entry)
    save_index(index)
    print(f"Added: {entry['filename']} (component: {entry['component']})")


def list_materials():
    """List all materials in index."""
    index = load_index()
    if not index["materials"]:
        print("No materials in index.")
        return
    
    print(f"\nMaterials in index ({len(index['materials'])} files):")
    print("-" * 80)
    for m in index["materials"]:
        print(f"  {m['filename']}")
        print(f"    Component: {m['component']}")
        print(f"    Type: {m['file_type']}")
        print(f"    Added: {m['added_date'][:10]}")
        if m.get("notes"):
            print(f"    Notes: {m['notes']}")
        print()


def create_summary():
    """Create a summary of all materials."""
    index = load_index()
    if not index["materials"]:
        print("No materials to summarize.")
        return
    
    # Group by component
    by_component = {}
    for m in index["materials"]:
        comp = m["component"]
        if comp not in by_component:
            by_component[comp] = []
        by_component[comp].append(m)
    
    print("\n=== SHALLOT Material Summary ===\n")
    for comp, materials in sorted(by_component.items()):
        print(f"## {comp}")
        for m in materials:
            print(f"  - {m['filename']} ({m['file_type']})")
            if m.get("extracted_text"):
                # Show first 100 chars of extracted text
                preview = m["extracted_text"][:100].replace("\n", " ")
                print(f"    Preview: {preview}...")
        print()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="SHALLOT Material Processor")
    parser.add_argument("file", nargs="?", help="File to process")
    parser.add_argument("--component", "-c", default="Unknown", help="Component name")
    parser.add_argument("--list", "-l", action="store_true", help="List all materials")
    parser.add_argument("--index", "-i", action="store_true", help="Create summary")
    parser.add_argument("--notes", "-n", default="", help="Add notes to entry")
    
    args = parser.parse_args()
    
    # Ensure material directory exists
    MATERIAL_DIR.mkdir(exist_ok=True)
    
    if args.list:
        list_materials()
        return
    
    if args.index:
        create_summary()
        return
    
    if not args.file:
        parser.print_help()
        return
    
    # Process file
    filepath = Path(args.file)
    entry = process_file(filepath, args.component)
    entry["notes"] = args.notes
    
    # Add to index
    add_to_index(entry)
    
    print(f"\nProcessed: {filepath.name}")
    print(f"Component: {args.component}")
    print(f"Hash: {entry['hash']}")
    if entry.get("extracted_text"):
        print(f"Extracted text: {len(entry['extracted_text'])} chars")


if __name__ == "__main__":
    main()
