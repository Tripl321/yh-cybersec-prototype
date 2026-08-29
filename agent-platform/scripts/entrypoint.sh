#!/bin/bash

############################################################################
#
#    Agno Container Entrypoint
#
############################################################################

# Colors
ORANGE='\033[38;5;208m'
DIM='\033[2m'
BOLD='\033[1m'
NC='\033[0m'

echo ""
echo -e "${ORANGE}"
cat << 'BANNER'
     █████╗  ██████╗ ███╗   ██╗ ██████╗
    ██╔══██╗██╔════╝ ████╗  ██║██╔═══██╗
    ███████║██║  ███╗██╔██╗ ██║██║   ██║
    ██╔══██║██║   ██║██║╚██╗██║██║   ██║
    ██║  ██║╚██████╔╝██║ ╚████║╚██████╔╝
    ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝ ╚═════╝
BANNER
echo -e "${NC}"

if [[ "${WAIT_FOR_DB:-}" = true || "${WAIT_FOR_DB:-}" = True ]]; then
    echo -e "    ${DIM}Waiting for database at ${DB_HOST}:${DB_PORT}...${NC}"
    HOST="${DB_HOST:-localhost}"
    PORT="${DB_PORT:-5432}"
    TIMEOUT=300
    elapsed=0
    while ! (exec 3<>"/dev/tcp/${HOST}/${PORT}") 2>/dev/null; do
        if [[ "$elapsed" -ge "$TIMEOUT" ]]; then
            echo -e "    ${BOLD}Timed out waiting for the database.${NC}"
            exit 1
        fi
        sleep 1
        elapsed=$((elapsed + 1))
    done
    exec 3>&- 2>/dev/null || true
    echo -e "    ${BOLD}Database ready.${NC}"
    echo ""
fi

case "$1" in
    chill)
        echo -e "    ${DIM}Mode: chill${NC}"
        echo -e "    ${BOLD}Container running.${NC}"
        echo ""
        while true; do sleep 18000; done
        ;;
    *)
        # `$*` for the echo, `"$@"` for the exec — the echo wants one display string,
        # and only "$@" keeps an argument that contains spaces a single argument.
        echo -e "    ${DIM}> $*${NC}"
        echo ""
        exec "$@"
        ;;
esac
