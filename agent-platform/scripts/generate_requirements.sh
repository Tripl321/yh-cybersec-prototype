#!/bin/bash

############################################################################
#
#    Agno Requirements Generator
#
#    Usage:
#      ./scripts/generate_requirements.sh           # Generate
#      ./scripts/generate_requirements.sh upgrade   # Generate with upgrade
#      ./scripts/generate_requirements.sh <pkg>...  # Refresh only these pins
#
#    The Dockerfile installs from requirements.txt (the pinned lockfile), while
#    the local venv installs the project editable (-e .). Run this whenever you
#    change a dependency in pyproject.toml so the container builds.
#
############################################################################

set -e

CURR_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "${CURR_DIR}")"

# Colors
ORANGE='\033[38;5;208m'
DIM='\033[2m'
BOLD='\033[1m'
NC='\033[0m'

echo ""
echo -e "    ${ORANGE}▸${NC} ${BOLD}Generating requirements.txt${NC}"
echo ""

if [[ "$1" = "upgrade" ]]; then
    echo -e "    ${DIM}Mode: upgrade${NC}"
    uv pip compile "${REPO_ROOT}/pyproject.toml" --no-cache --upgrade -o "${REPO_ROOT}/requirements.txt"
elif [[ $# -gt 0 ]]; then
    UPGRADE_FLAGS=()
    for pkg in "$@"; do
        UPGRADE_FLAGS+=("--upgrade-package" "$pkg")
    done
    echo -e "    ${DIM}Mode: refresh ($*)${NC}"
    uv pip compile "${REPO_ROOT}/pyproject.toml" --no-cache "${UPGRADE_FLAGS[@]}" -o "${REPO_ROOT}/requirements.txt"
else
    echo -e "    ${DIM}Mode: standard${NC}"
    uv pip compile "${REPO_ROOT}/pyproject.toml" --no-cache -o "${REPO_ROOT}/requirements.txt"
fi

echo ""
echo -e "    ${BOLD}Done.${NC}"
echo ""
