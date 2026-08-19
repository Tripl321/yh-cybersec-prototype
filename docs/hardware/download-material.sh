#!/usr/bin/env bash
# SHALLOT Material Downloader
# Download files from URLs and add to hardware documentation
#
# Usage:
#   ./download-material.sh <url> [--component <name>] [--filename <name>]
#
# Examples:
#   ./download-material.sh https://example.com/datasheet.pdf --component "LoRa SX1262"
#   ./download-material.sh https://example.com/photo.jpg --component "ESP32" --filename esp32-photo.jpg

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HARDWARE_DIR="$(dirname "$SCRIPT_DIR")"
MATERIAL_DIR="$HARDWARE_DIR/material"
TEMP_DIR="/tmp/shalot-material"

# Defaults
COMPONENT="Unknown"
FILENAME=""
URL=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --component|-c)
            COMPONENT="$2"
            shift 2
            ;;
        --filename|-f)
            FILENAME="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 <url> [--component <name>] [--filename <name>]"
            echo ""
            echo "Download a file and add it to SHALLOT hardware documentation."
            echo ""
            echo "Options:"
            echo "  --component, -c   Component name (default: Unknown)"
            echo "  --filename, -f    Custom filename (default: from URL)"
            echo "  --help, -h        Show this help"
            exit 0
            ;;
        -*)
            echo "Unknown option: $1"
            exit 1
            ;;
        *)
            URL="$1"
            shift
            ;;
    esac
done

if [[ -z "$URL" ]]; then
    echo "Error: URL is required"
    echo "Usage: $0 <url> [--component <name>] [--filename <name>]"
    exit 1
fi

# Create directories
mkdir -p "$MATERIAL_DIR" "$TEMP_DIR"

# Determine filename from URL if not provided
if [[ -z "$FILENAME" ]]; then
    FILENAME=$(basename "$URL" | sed 's/?.*//')  # Remove query params
    # Add extension if missing
    if [[ ! "$FILENAME" =~ \.[a-zA-Z]{2,4}$ ]]; then
        FILENAME="${FILENAME}.pdf"  # Default to PDF
    fi
fi

echo "Downloading: $URL"
echo "Saving as: $FILENAME"
echo "Component: $COMPONENT"

# Download
if command -v curl &> /dev/null; then
    curl -L -o "$TEMP_DIR/$FILENAME" "$URL"
elif command -v wget &> /dev/null; then
    wget -O "$TEMP_DIR/$FILENAME" "$URL"
else
    echo "Error: Neither curl nor wget found"
    exit 1
fi

# Check if download succeeded
if [[ ! -f "$TEMP_DIR/$FILENAME" ]]; then
    echo "Error: Download failed"
    exit 1
fi

# Copy to material directory
cp "$TEMP_DIR/$FILENAME" "$MATERIAL_DIR/"

# Process with Python script
echo "Processing..."
cd "$HARDWARE_DIR"
python3 process-material.py "material/$FILENAME" --component "$COMPONENT"

# Cleanup temp
rm -f "$TEMP_DIR/$FILENAME"

echo ""
echo "Done! File saved to: $MATERIAL_DIR/$FILENAME"
echo "Run 'python3 process-material.py --list' to see all materials."
