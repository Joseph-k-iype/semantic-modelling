#!/bin/bash
# scripts/fix-all-imports.sh
# ============================================================================
# COMPREHENSIVE FIX SCRIPT - Fix ALL import issues
# Path: scripts/fix-all-imports.sh
# ============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}============================================================================${NC}"
echo -e "${BLUE}🔧 Comprehensive Import Fix Script${NC}"
echo -e "${BLUE}============================================================================${NC}"

# Step 1: Fix backend/app/db/base.py (CRITICAL - removes circular import)
echo -e "\n${YELLOW}Step 1: Fixing backend/app/db/base.py (removing circular imports)${NC}"

cat > backend/app/db/base.py << 'EOF'
# backend/app/db/base.py
"""
Database Base Class - FIXED to prevent circular imports
Path: backend/app/db/base.py

CRITICAL: This file should ONLY contain the Base class definition.
DO NOT import any models here - that creates circular dependencies.
"""
from sqlalchemy.ext.declarative import declarative_base

# Base class for all SQLAlchemy models
Base = declarative_base()
EOF

echo -e "${GREEN}✓ backend/app/db/base.py fixed${NC}"

# Step 2: Fix backend/app/db/__init__.py
echo -e "\n${YELLOW}Step 2: Fixing backend/app/db/__init__.py${NC}"

cat > backend/app/db/__init__.py << 'EOF'
# backend/app/db/__init__.py
"""
Database package initialization - FIXED
Path: backend/app/db/__init__.py
"""
from app.db.base import Base
from app.db.session import (
    get_db,
    init_db,
    close_db,
    engine,
    AsyncSessionLocal,
    SessionLocal,
)

__all__ = [
    "Base",
    "get_db",
    "init_db",
    "close_db",
    "engine",
    "AsyncSessionLocal",
    "SessionLocal",
]
EOF

echo -e "${GREEN}✓ backend/app/db/__init__.py fixed${NC}"

# Step 3: Fix all model files with incorrect imports
echo -e "\n${YELLOW}Step 3: Fixing model file imports${NC}"

# Function to fix imports in a file
fix_imports() {
    local file=$1
    echo -e "  ${BLUE}→${NC} Fixing $file"
    
    # Backup
    cp "$file" "${file}.backup"
    
    # Fix: Replace incorrect PostgreSQL imports with correct SQLAlchemy imports
    sed -i.tmp 's/from sqlalchemy.dialects.postgresql import UUID, JSONB, String, DateTime, ForeignKey, Text, JSON, Boolean, Integer/from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Boolean, Integer\nfrom sqlalchemy.dialects.postgresql import UUID, JSONB/g' "$file"
    sed -i.tmp 's/from sqlalchemy.dialects.postgresql import UUID, JSONB, String, DateTime, ForeignKey, Text, JSON, Boolean/from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Boolean\nfrom sqlalchemy.dialects.postgresql import UUID, JSONB/g' "$file"
    sed -i.tmp 's/from sqlalchemy.dialects.postgresql import UUID, JSONB, String, DateTime, ForeignKey, Text, JSON/from sqlalchemy import Column, String, Text, ForeignKey, DateTime\nfrom sqlalchemy.dialects.postgresql import UUID, JSONB/g' "$file"
    sed -i.tmp 's/from sqlalchemy.dialects.postgresql import UUID, JSONB, String, DateTime, ForeignKey, Text, Boolean, Integer/from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Boolean, Integer\nfrom sqlalchemy.dialects.postgresql import UUID, JSONB/g' "$file"
    sed -i.tmp 's/from sqlalchemy.dialects.postgresql import UUID, String, DateTime, ForeignKey, Text, Boolean/from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Boolean\nfrom sqlalchemy.dialects.postgresql import UUID/g' "$file"
    
    # Remove Column from postgresql imports if it exists
    sed -i.tmp 's/from sqlalchemy.dialects.postgresql import Column, UUID/from sqlalchemy import Column\nfrom sqlalchemy.dialects.postgresql import UUID/g' "$file"
    
    # Clean up temp file
    rm -f "${file}.tmp"
    
    echo -e "    ${GREEN}✓ Fixed${NC}"
}

# Fix each model file
for model_file in backend/app/models/*.py; do
    if [ -f "$model_file" ] && [ "$(basename "$model_file")" != "__init__.py" ] && [ "$(basename "$model_file")" != "base.py" ]; then
        fix_imports "$model_file"
    fi
done

# Step 4: Verify all fixes
echo -e "\n${YELLOW}Step 4: Verifying fixes${NC}"

echo -e "  ${BLUE}→${NC} Checking for remaining incorrect imports..."

# Check for any remaining incorrect imports
if grep -r "from sqlalchemy.dialects.postgresql import.*String" backend/app/models/*.py 2>/dev/null; then
    echo -e "    ${RED}✗ Found remaining incorrect imports${NC}"
    exit 1
else
    echo -e "    ${GREEN}✓ All imports fixed${NC}"
fi

# Check that base.py doesn't import models
if grep "from app.models" backend/app/db/base.py 2>/dev/null; then
    echo -e "    ${RED}✗ base.py still imports models (circular dependency)${NC}"
    exit 1
else
    echo -e "    ${GREEN}✓ No circular imports in base.py${NC}"
fi

echo -e "\n${GREEN}============================================================================${NC}"
echo -e "${GREEN}✅ All import fixes applied successfully!${NC}"
echo -e "${GREEN}============================================================================${NC}"

echo -e "\n${YELLOW}Next steps:${NC}"
echo -e "  1. Rebuild the backend container:"
echo -e "     ${BLUE}docker-compose -f docker-compose.dev.yml build --no-cache backend${NC}"
echo -e ""
echo -e "  2. Start the backend:"
echo -e "     ${BLUE}docker-compose -f docker-compose.dev.yml up -d backend${NC}"
echo -e ""
echo -e "  3. Check logs:"
echo -e "     ${BLUE}docker-compose -f docker-compose.dev.yml logs -f backend${NC}"
echo -e ""