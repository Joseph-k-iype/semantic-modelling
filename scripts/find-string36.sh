#!/bin/bash
# scripts/find-string36.sh
# Find all Python files that still use String(36) instead of UUID

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║       Finding Files That Need UUID Fixes                 ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Search for String(36) in model files
echo -e "${YELLOW}Searching for String(36) in backend/app/models/...${NC}"
echo ""

FILES_FOUND=0

# Find all Python files in models directory
for file in backend/app/models/*.py; do
    if [ -f "$file" ]; then
        # Check if file contains String(36)
        if grep -q "String(36)" "$file"; then
            FILES_FOUND=$((FILES_FOUND + 1))
            echo -e "${RED}❌ $file${NC}"
            
            # Show lines with String(36)
            grep -n "String(36)" "$file" | while read line; do
                echo -e "${YELLOW}   Line: $line${NC}"
            done
            echo ""
        fi
    fi
done

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"

if [ $FILES_FOUND -eq 0 ]; then
    echo -e "${GREEN}✓ No files found with String(36)${NC}"
    echo -e "${GREEN}✓ All models are using UUID!${NC}"
else
    echo -e "${RED}Found $FILES_FOUND file(s) that need UUID fixes${NC}"
    echo ""
    echo -e "${YELLOW}To fix these files:${NC}"
    echo "1. Replace: String(36) → UUID(as_uuid=True)"
    echo "2. Add import: from sqlalchemy.dialects.postgresql import UUID"
    echo "3. Update defaults: default=lambda: str(uuid.uuid4()) → default=uuid.uuid4"
    echo "4. Restart backend: docker-compose -f docker-compose.dev.yml restart backend"
fi

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Also check for JSON (should be JSONB)
echo -e "${YELLOW}Checking for JSON columns (should use JSONB for PostgreSQL)...${NC}"
echo ""

JSON_FOUND=0
for file in backend/app/models/*.py; do
    if [ -f "$file" ]; then
        # Check if file contains Column(JSON without JSONB
        if grep -E "Column\(JSON[,)]" "$file" | grep -v "JSONB" > /dev/null; then
            JSON_FOUND=$((JSON_FOUND + 1))
            echo -e "${YELLOW}⚠ $file (uses JSON instead of JSONB)${NC}"
            grep -n -E "Column\(JSON[,)]" "$file" | grep -v "JSONB" | while read line; do
                echo -e "   $line"
            done
            echo ""
        fi
    fi
done

if [ $JSON_FOUND -gt 0 ]; then
    echo -e "${YELLOW}Note: $JSON_FOUND file(s) use JSON instead of JSONB${NC}"
    echo "Consider changing to JSONB for better PostgreSQL performance"
else
    echo -e "${GREEN}✓ All JSON columns already using JSONB or no JSON columns found${NC}"
fi

echo ""