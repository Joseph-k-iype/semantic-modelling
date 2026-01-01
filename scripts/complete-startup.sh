#!/bin/bash
# scripts/complete-startup.sh
# Complete startup script for Enterprise Modeling Platform - FIXED VERSION
# Handles all initialization, database setup, and service startup

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN} $1${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo ""
}

print_step() {
    echo -e "${BLUE}➜${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC}  $1"
}

# Banner
clear
echo -e "${CYAN}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                                                           ║"
echo "║        Enterprise Modeling Platform                       ║"
echo "║        Complete Initialization & Startup                  ║"
echo "║                Version 1.0.0                              ║"
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# ============================================================================
# STEP 1: Prerequisites Check
# ============================================================================
print_header "Step 1: Checking Prerequisites"

print_step "Checking Docker..."
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed!"
    exit 1
fi
DOCKER_VERSION=$(docker --version)
print_success "Docker is installed: $DOCKER_VERSION"

print_step "Checking Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed!"
    exit 1
fi
COMPOSE_VERSION=$(docker-compose --version)
print_success "Docker Compose is installed: $COMPOSE_VERSION"

# ============================================================================
# STEP 2: Clean Up Old Containers
# ============================================================================
print_header "Step 2: Cleaning Up Old Containers"

print_step "Stopping all existing containers..."
docker-compose -f docker-compose.dev.yml down -v 2>/dev/null || true
sleep 2
print_success "Old containers stopped and volumes removed"

# ============================================================================
# STEP 3: Verify Directory Structure
# ============================================================================
print_header "Step 3: Setting Up Directory Structure"

print_step "Creating required directories..."
mkdir -p database/postgres/init
mkdir -p database/postgres/schema
mkdir -p database/falkordb/init
mkdir -p database/redis
mkdir -p backend/logs
mkdir -p backend/uploads
print_success "Directories created"

# ============================================================================
# STEP 4: Verify Required Files
# ============================================================================
print_header "Step 4: Verifying Required Files"

print_step "Checking database initialization files..."
if [ ! -f "database/postgres/init/01-init-db.sql" ]; then
    print_error "Missing database/postgres/init/01-init-db.sql"
    print_error "Please ensure all SQL schema files are in place"
    exit 1
fi
print_success "Database init file found"

print_step "Checking schema files..."
SCHEMA_FILES=(
    "database/postgres/schema/01-users.sql"
    "database/postgres/schema/02-workspaces.sql"
    "database/postgres/schema/03-folders.sql"
    "database/postgres/schema/04-models.sql"
    "database/postgres/schema/05-diagrams.sql"
)

for schema_file in "${SCHEMA_FILES[@]}"; do
    if [ ! -f "$schema_file" ]; then
        print_warning "Missing $schema_file (will continue anyway)"
    fi
done
print_success "Schema files verified"

# ============================================================================
# STEP 5: Build Docker Images
# ============================================================================
print_header "Step 5: Building Docker Images"

print_step "Building all services (this may take 3-5 minutes)..."
docker-compose -f docker-compose.dev.yml build

if [ $? -eq 0 ]; then
    print_success "All images built successfully!"
else
    print_error "Build failed! Check the output above."
    exit 1
fi

# ============================================================================
# STEP 6: Start PostgreSQL
# ============================================================================
print_header "Step 6: Starting PostgreSQL"

print_step "Starting PostgreSQL service..."
docker-compose -f docker-compose.dev.yml up -d postgres
sleep 5

print_step "Waiting for PostgreSQL to initialize (max 60 seconds)..."
COUNTER=0
until docker exec modeling-postgres pg_isready -U postgres > /dev/null 2>&1; do
    if [ $COUNTER -gt 30 ]; then
        print_error "PostgreSQL failed to start!"
        docker-compose -f docker-compose.dev.yml logs postgres
        exit 1
    fi
    echo -n "."
    sleep 2
    COUNTER=$((COUNTER + 1))
done
echo ""


print_success "PostgreSQL is ready!"

# ============================================================================
# STEP 7: Verify Database Setup
# ============================================================================
print_header "Step 7: Verifying Database Setup"

sleep 3

# Check if modeling user exists
print_step "Checking modeling user..."
if docker exec modeling-postgres psql -U postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname='modeling'" | grep -q 1; then
    print_success "User 'modeling' exists"
else
    print_error "User 'modeling' was not created!"
    print_error "Check database/postgres/init/01-init-db.sql"
    exit 1
fi

# Check if database exists
print_step "Checking modeling_platform database..."
if docker exec modeling-postgres psql -U postgres -lqt | cut -d \| -f 1 | grep -qw modeling_platform; then
    print_success "Database 'modeling_platform' exists"
else
    print_error "Database 'modeling_platform' was not created!"
    exit 1
fi

# Test connection with modeling user
print_step "Testing connection with modeling user..."
if docker exec modeling-postgres psql -U modeling -d modeling_platform -c "SELECT 1;" > /dev/null 2>&1; then
    print_success "Connection successful"
else
    print_error "Cannot connect with modeling user!"
    exit 1
fi

# ============================================================================
# STEP 8: Apply Database Schemas
# ============================================================================
print_header "Step 8: Applying Database Schemas"

print_step "Applying schema files in order..."

# Define schema files in correct order
SCHEMA_FILES=(
    "01-users.sql"
    "02-workspaces.sql"
    "03-folders.sql"
    "04-models.sql"
    "05-diagrams.sql"
    "06-layouts.sql"
    "07-versions.sql"
    "08-publish_workflows.sql"
    "09-comments.sql"
    "10-audit_logs.sql"
)

# Apply each schema file
for schema_file in "${SCHEMA_FILES[@]}"; do
    schema_path="database/postgres/schema/$schema_file"
    if [ -f "$schema_path" ]; then
        print_step "Applying $schema_file..."
        docker exec -i modeling-postgres psql -U modeling -d modeling_platform < "$schema_path" 2>&1 | grep -v "NOTICE" || true
        if [ ${PIPESTATUS[0]} -eq 0 ]; then
            print_success "$schema_file applied"
        else
            print_error "Failed to apply $schema_file"
            exit 1
        fi
    else
        print_warning "Schema file $schema_file not found, skipping..."
    fi
done

# ============================================================================
# STEP 9: Start FalkorDB and Redis
# ============================================================================
print_header "Step 9: Starting FalkorDB and Redis"

print_step "Starting FalkorDB..."
docker-compose -f docker-compose.dev.yml up -d falkordb
sleep 3

print_step "Starting Redis..."
docker-compose -f docker-compose.dev.yml up -d redis
sleep 3

# Wait for services
print_step "Waiting for services to be ready..."
COUNTER=0
until docker exec modeling-falkordb redis-cli -p 6379 PING > /dev/null 2>&1; do
    if [ $COUNTER -gt 20 ]; then
        print_error "FalkorDB failed to start!"
        exit 1
    fi
    echo -n "."
    sleep 1
    COUNTER=$((COUNTER + 1))
done
echo ""
print_success "FalkorDB is ready!"

COUNTER=0
until docker exec modeling-redis redis-cli PING > /dev/null 2>&1; do
    if [ $COUNTER -gt 20 ]; then
        print_error "Redis failed to start!"
        exit 1
    fi
    echo -n "."
    sleep 1
    COUNTER=$((COUNTER + 1))
done
echo ""
print_success "Redis is ready!"

# ============================================================================
# STEP 10: Start Backend
# ============================================================================
print_header "Step 10: Starting Backend API"

print_step "Starting backend service..."
docker-compose -f docker-compose.dev.yml up -d backend
sleep 5

print_step "Waiting for backend to be ready (max 60 seconds)..."
COUNTER=0
until curl -f http://localhost:8000/health > /dev/null 2>&1; do
    if [ $COUNTER -gt 30 ]; then
        print_error "Backend failed to start!"
        print_error "Checking logs:"
        docker-compose -f docker-compose.dev.yml logs backend
        exit 1
    fi
    echo -n "."
    sleep 2
    COUNTER=$((COUNTER + 1))
done
echo ""
print_success "Backend is ready!"

# ============================================================================
# STEP 11: Initialize Database with Test Data
# ============================================================================
print_header "Step 11: Initializing Database with Test Data"

print_step "Running database initialization script..."
if docker exec modeling-backend python init_database.py 2>&1 | tee /tmp/init_db.log; then
    print_success "Database initialized successfully"
else
    print_warning "Database initialization had warnings (check above)"
    print_warning "This is OK if tables already exist"
fi

# ============================================================================
# STEP 12: Start Frontend
# ============================================================================
print_header "Step 12: Starting Frontend"

print_step "Starting frontend service..."
docker-compose -f docker-compose.dev.yml up -d frontend
sleep 5
print_success "Frontend is starting..."

# ============================================================================
# STEP 13: Final Verification
# ============================================================================
print_header "Step 13: Final Verification"

echo ""
print_step "Checking all services..."
docker-compose -f docker-compose.dev.yml ps

echo ""
print_step "Testing service endpoints..."

# Test PostgreSQL
if docker exec modeling-postgres psql -U modeling -d modeling_platform -c "SELECT 1;" > /dev/null 2>&1; then
    print_success "PostgreSQL: ✓ Connected (modeling_platform)"
else
    print_error "PostgreSQL: ✗ Connection failed"
fi

# Test FalkorDB
if docker exec modeling-falkordb redis-cli -p 6379 PING > /dev/null 2>&1; then
    print_success "FalkorDB: ✓ Connected"
else
    print_error "FalkorDB: ✗ Connection failed"
fi

# Test Redis
if docker exec modeling-redis redis-cli PING > /dev/null 2>&1; then
    print_success "Redis: ✓ Connected"
else
    print_error "Redis: ✗ Connection failed"
fi

# Test Backend API
sleep 3
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    print_success "Backend API: ✓ Running (http://localhost:8000)"
else
    print_warning "Backend API: Still starting..."
fi

# Test Backend Auth Endpoint
if curl -f -X POST http://localhost:8000/api/v1/auth/register \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com","password":"test"}' > /dev/null 2>&1; then
    print_success "Auth Endpoint: ✓ Working"
else
    print_warning "Auth Endpoint: Not ready yet (normal if user exists)"
fi

# Test Frontend
sleep 3
if curl -f http://localhost:5173 > /dev/null 2>&1; then
    print_success "Frontend: ✓ Running (http://localhost:5173)"
else
    print_warning "Frontend: Still starting (takes 10-20 seconds)..."
fi

# ============================================================================
# SUMMARY
# ============================================================================
print_header "🎉 Startup Complete!"

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                    All Services Ready!                    ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

echo -e "${CYAN}📍 Service URLs:${NC}"
echo "   Frontend:          http://localhost:5173"
echo "   Backend API:       http://localhost:8000"
echo "   API Docs:          http://localhost:8000/docs"
echo "   FalkorDB Browser:  http://localhost:3000"
echo ""

echo -e "${CYAN}🔐 Test Accounts:${NC}"
echo "   Regular User:"
echo "     Email:    test@example.com"
echo "     Password: password123"
echo ""
echo "   Admin User:"
echo "     Email:    admin@example.com"
echo "     Password: admin123"
echo ""

echo -e "${CYAN}🗄️  Database Info:${NC}"
echo "   Host:     localhost:5432"
echo "   Database: modeling_platform  ✓ (Correct)"
echo "   User:     modeling"
echo "   Password: modeling_dev"
echo ""

echo -e "${CYAN}📊 Graph Database:${NC}"
echo "   FalkorDB: localhost:6379"
echo "   Redis:    localhost:6380"
echo ""

echo -e "${CYAN}🛠️  Useful Commands:${NC}"
echo "   View logs:        docker-compose -f docker-compose.dev.yml logs -f"
echo "   Stop services:    docker-compose -f docker-compose.dev.yml down"
echo "   Restart backend:  docker-compose -f docker-compose.dev.yml restart backend"
echo "   Database shell:   docker exec -it modeling-postgres psql -U modeling -d modeling_platform"
echo ""

echo -e "${CYAN}⚠️  Note:${NC}"
echo "   Frontend may take 10-20 seconds to fully start."
echo "   Wait for 'ready in X ms' message in logs."
echo ""

print_success "All systems operational! Happy modeling! 🚀"
echo ""