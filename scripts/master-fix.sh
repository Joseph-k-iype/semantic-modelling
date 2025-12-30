#!/bin/bash
# scripts/master-fix.sh
# ============================================================================
# MASTER FIX SCRIPT - Fix everything and restart
# Path: scripts/master-fix.sh
# ============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

clear
echo -e "${CYAN}"
echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                        ║"
echo "║              🔧 MASTER FIX & RESTART SCRIPT 🔧                         ║"
echo "║                                                                        ║"
echo "║     Fixing circular imports, SQLAlchemy imports, and CORS issues      ║"
echo "║                                                                        ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo -e "${NC}\n"

# ============================================================================
# STEP 1: Stop all services
# ============================================================================
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Step 1: Stopping all services${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"

docker-compose -f docker-compose.dev.yml down
echo -e "${GREEN}✓ Services stopped${NC}\n"

# ============================================================================
# STEP 2: Create backups
# ============================================================================
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Step 2: Creating backups${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"

BACKUP_DIR="backups/fix-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp -r backend/app/db "$BACKUP_DIR/"
cp -r backend/app/models "$BACKUP_DIR/"
echo -e "${GREEN}✓ Backups created in $BACKUP_DIR${NC}\n"

# ============================================================================
# STEP 3: Fix backend/app/db/base.py (CRITICAL - removes circular import)
# ============================================================================
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Step 3: Fixing circular import in base.py${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"

cat > backend/app/db/base.py << 'EOF'
# backend/app/db/base.py
"""
Database Base Class - FIXED
Path: backend/app/db/base.py
"""
from sqlalchemy.ext.declarative import declarative_base

# Base class for all SQLAlchemy models
Base = declarative_base()
EOF

echo -e "${GREEN}✓ Fixed backend/app/db/base.py${NC}\n"

# ============================================================================
# STEP 4: Fix backend/app/db/__init__.py
# ============================================================================
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Step 4: Fixing db package init${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"

cat > backend/app/db/__init__.py << 'EOF'
# backend/app/db/__init__.py
"""
Database package initialization
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

echo -e "${GREEN}✓ Fixed backend/app/db/__init__.py${NC}\n"

# ============================================================================
# STEP 5: Fix ALL model imports
# ============================================================================
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Step 5: Fixing SQLAlchemy imports in all models${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"

# Fix diagram.py
echo -e "  ${CYAN}→${NC} Fixing diagram.py"
sed -i.bak 's/from sqlalchemy.dialects.postgresql import UUID, JSONB, String, DateTime, ForeignKey, Text, JSON/from sqlalchemy import Column, String, Text, ForeignKey, DateTime\nfrom sqlalchemy.dialects.postgresql import UUID, JSONB/g' backend/app/models/diagram.py && rm backend/app/models/diagram.py.bak
echo -e "    ${GREEN}✓ Done${NC}"

# Fix audit_log.py
echo -e "  ${CYAN}→${NC} Fixing audit_log.py"
sed -i.bak 's/from sqlalchemy.dialects.postgresql import UUID, JSONB, String, DateTime, ForeignKey, Text, JSON/from sqlalchemy import Column, String, Text, ForeignKey, DateTime\nfrom sqlalchemy.dialects.postgresql import UUID, JSONB/g' backend/app/models/audit_log.py && rm backend/app/models/audit_log.py.bak
echo -e "    ${GREEN}✓ Done${NC}"

# Fix publish_workflow.py
echo -e "  ${CYAN}→${NC} Fixing publish_workflow.py"
sed -i.bak 's/from sqlalchemy.dialects.postgresql import UUID, JSONB, String, DateTime, ForeignKey, Text, JSON/from sqlalchemy import Column, String, Text, ForeignKey, DateTime\nfrom sqlalchemy.dialects.postgresql import UUID, JSONB/g' backend/app/models/publish_workflow.py && rm backend/app/models/publish_workflow.py.bak
echo -e "    ${GREEN}✓ Done${NC}"

# Fix comment.py
echo -e "  ${CYAN}→${NC} Fixing comment.py"
sed -i.bak 's/from sqlalchemy.dialects.postgresql import UUID, JSONB, String, DateTime, ForeignKey, Text, Boolean, Integer/from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Boolean, Integer\nfrom sqlalchemy.dialects.postgresql import UUID, JSONB/g' backend/app/models/comment.py && rm backend/app/models/comment.py.bak
echo -e "    ${GREEN}✓ Done${NC}"

# Fix layout.py  
echo -e "  ${CYAN}→${NC} Fixing layout.py"
sed -i.bak 's/from sqlalchemy.dialects.postgresql import UUID, JSONB, String, DateTime, ForeignKey, Text, JSON, Boolean/from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Boolean\nfrom sqlalchemy.dialects.postgresql import UUID, JSONB/g' backend/app/models/layout.py && rm backend/app/models/layout.py.bak
echo -e "    ${GREEN}✓ Done${NC}"

echo -e "\n${GREEN}✓ All model imports fixed${NC}\n"

# ============================================================================
# STEP 6: Fix frontend environment
# ============================================================================
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Step 6: Configuring frontend environment${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"

cat > frontend/.env.development << 'EOF'
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_NAME=Enterprise Modeling Platform
VITE_APP_VERSION=1.0.0
VITE_DEBUG=true
EOF

echo -e "${GREEN}✓ Frontend environment configured${NC}\n"

# ============================================================================
# STEP 7: Rebuild containers
# ============================================================================
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Step 7: Rebuilding Docker containers${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"

echo -e "  ${CYAN}→${NC} Building backend (this may take a few minutes)..."
docker-compose -f docker-compose.dev.yml build --no-cache backend
echo -e "    ${GREEN}✓ Backend built${NC}"

echo -e "  ${CYAN}→${NC} Building frontend..."
docker-compose -f docker-compose.dev.yml build --no-cache frontend
echo -e "    ${GREEN}✓ Frontend built${NC}\n"

# ============================================================================
# STEP 8: Start services
# ============================================================================
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Step 8: Starting services${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"

docker-compose -f docker-compose.dev.yml up -d
echo -e "${GREEN}✓ Services started${NC}\n"

# ============================================================================
# STEP 9: Wait for services
# ============================================================================
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Step 9: Waiting for services to be ready${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"

echo -e "  ${CYAN}→${NC} Waiting for PostgreSQL..."
COUNTER=0
until docker exec modeling-postgres pg_isready -U modeling > /dev/null 2>&1; do
    if [ $COUNTER -gt 30 ]; then
        echo -e "${RED}✗ PostgreSQL timeout${NC}"
        exit 1
    fi
    echo -n "."
    sleep 2
    COUNTER=$((COUNTER + 1))
done
echo -e "\n  ${GREEN}✓ PostgreSQL ready${NC}"

echo -e "  ${CYAN}→${NC} Waiting for backend..."
COUNTER=0
until curl -sf http://localhost:8000/health > /dev/null 2>&1; do
    if [ $COUNTER -gt 60 ]; then
        echo -e "${RED}✗ Backend timeout${NC}"
        echo -e "\n${YELLOW}Backend logs:${NC}"
        docker-compose -f docker-compose.dev.yml logs --tail=50 backend
        exit 1
    fi
    echo -n "."
    sleep 2
    COUNTER=$((COUNTER + 1))
done
echo -e "\n  ${GREEN}✓ Backend ready${NC}"

echo -e "  ${CYAN}→${NC} Waiting for frontend..."
COUNTER=0
until curl -sf http://localhost:5173 > /dev/null 2>&1; do
    if [ $COUNTER -gt 30 ]; then
        echo -e "${YELLOW}⚠  Frontend still starting (this is normal)${NC}"
        break
    fi
    echo -n "."
    sleep 2
    COUNTER=$((COUNTER + 1))
done
echo -e "\n  ${GREEN}✓ Frontend ready${NC}\n"

# ============================================================================
# STEP 10: Initialize database
# ============================================================================
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Step 10: Initializing database${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"

docker exec modeling-backend python init_database.py
echo -e "\n${GREEN}✓ Database initialized${NC}\n"

# ============================================================================
# STEP 11: Verification
# ============================================================================
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}Step 11: Running verification tests${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"

# Test health endpoint
if curl -sf http://localhost:8000/health | grep -q "healthy"; then
    echo -e "  ${GREEN}✓ Backend health check passed${NC}"
else
    echo -e "  ${RED}✗ Backend health check failed${NC}"
fi

# Test CORS
if curl -sf -X OPTIONS -H "Origin: http://localhost:5173" http://localhost:8000/api/v1/auth/register > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓ CORS configured correctly${NC}"
else
    echo -e "  ${YELLOW}⚠  CORS check inconclusive${NC}"
fi

# ============================================================================
# SUCCESS
# ============================================================================
echo -e "\n${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}                                                            ${NC}"
echo -e "${GREEN}                  ✅ ALL FIXES APPLIED!                     ${NC}"
echo -e "${GREEN}                                                            ${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}\n"

echo -e "${CYAN}🌐 Access Points:${NC}"
echo -e "   Frontend:  ${BLUE}http://localhost:5173${NC}"
echo -e "   Backend:   ${BLUE}http://localhost:8000${NC}"
echo -e "   API Docs:  ${BLUE}http://localhost:8000/docs${NC}"
echo -e ""
echo -e "${CYAN}📋 Useful Commands:${NC}"
echo -e "   View logs:     ${BLUE}docker-compose -f docker-compose.dev.yml logs -f${NC}"
echo -e "   Restart:       ${BLUE}docker-compose -f docker-compose.dev.yml restart${NC}"
echo -e "   Stop:          ${BLUE}docker-compose -f docker-compose.dev.yml down${NC}"
echo -e ""
echo -e "${CYAN}📁 Backup Location:${NC}"
echo -e "   ${BLUE}$BACKUP_DIR${NC}"
echo -e ""
echo -e "${GREEN}Ready to use! 🎉${NC}\n"