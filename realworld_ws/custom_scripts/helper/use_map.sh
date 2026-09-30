#!/bin/bash

########################################
#### Locate root & setup enviroment ####
########################################

## Locate repository root and load environment
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

REPO_ROOT="$SCRIPT_DIR"
while [ ! -f "$REPO_ROOT/.env" ]; do
    if [ "$REPO_ROOT" = "/" ]; then
        echo "Error: could not find .env file in any parent directory of $SCRIPT_DIR" >&2
        exit 1
    fi
    REPO_ROOT="$(dirname "$REPO_ROOT")"
done

ENV_FILE="$REPO_ROOT/.env"

# Read .env and export variables (handles VAR=value and VAR=${OTHER_VAR})
set -a  # Automatically export all variables
source "$ENV_FILE"
set +a

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

if [ ! -d "$MAP_VAULT_DIR" ]; then
    echo -e "${RED}Error: $MAP_VAULT_DIR does not exist.${NC}"
    exit 1
fi

# List available map directories
echo -e "${YELLOW}Available maps:${NC}"
echo "---------------"
dirs=()
i=1
for dir in "$MAP_VAULT_DIR"/*/; do
    if [ -d "$dir" ]; then
        name=$(basename "$dir")
        dirs+=("$dir")
        echo "  [$i] $name"
        i=$((i + 1))
    fi
done

if [ ${#dirs[@]} -eq 0 ]; then
    echo -e "${RED}No maps found in $MAP_VAULT_DIR${NC}"
fi

echo ""
read -p "Select map [1-${#dirs[@]}]: " choice

if ! [[ "$choice" =~ ^[0-9]+$ ]] || [ "$choice" -lt 1 ] || [ "$choice" -gt ${#dirs[@]} ]; then
    echo -e "${RED}Invalid selection.${NC}"
fi

selected="${dirs[$((choice - 1))]}"
selected_name=$(basename "$selected")
echo ""
echo -e "${YELLOW}Selected: $selected_name${NC}"
echo ""

# Copy 2D map
if [ -f "${selected}yahboom_map.yaml" ] && [ -f "${selected}yahboom_map.pgm" ]; then
    if [ -d "$MAP_NAV_DIR" ]; then
        cp "${selected}yahboom_map.yaml" "$MAP_NAV_DIR/yahboom_map.yaml"
        cp "${selected}yahboom_map.pgm" "$MAP_NAV_DIR/yahboom_map.pgm"

        # Update the image path inside the yaml to match the new filename
        #sed -i 's|image:.*|image: yahboom_map.pgm|' "$MAP_NAV_DIR/yahboom_map.yaml"
    else
        echo -e "${YELLOW}[WARN] Navigation package not found at $MAP_NAV_DIR copying only to source map directory instead.${NC}"
    fi
    
    cp "${selected}yahboom_map.yaml" "$MAP_NAV_DIR_SRC/"
    cp "${selected}yahboom_map.pgm" "$MAP_NAV_DIR_SRC/"
    
    echo -e "${GREEN}[OK] 2D map copied${NC}"
else
    echo -e "${YELLOW}[--] No 2D map (yahboom_map.yaml + yahboom_map.pgm) found in $selected_name${NC}"
fi

# Copy 3D map
if [ -f "${selected}rtabmap.db" ]; then
    cp "${selected}rtabmap.db" "$RTABMAP_DB/rtabmap.db"
    echo -e "${GREEN}[OK] 3D map copied to $RTABMAP_DB/rtabmap.db${NC}"
else
    echo -e "${YELLOW}[--] No 3D map (rtabmap.db) found in $selected_name${NC}"
fi

# copy patrol path
if [ -f "${selected}route.json" ]; then
    cp "${selected}route.json" "$MAP_NAV_DIR/route.json"
    echo -e "${GREEN}[OK] Patrol path copied to $MAP_NAV_DIR/route.json${NC}"
else
    echo -e "${YELLOW}[--] No patrol path (route.json) found in $selected_name${NC}"
fi

echo ""
echo -e "${GREEN}Done. Restart the navigation stack to use the new map.${NC}"
