#!/bin/bash
# scripts/complete-startup.sh
# Complete startup script for Enterprise Modeling Platform
# Handles all initialization, database setup, and service startup

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0;m' # No Color

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
echo "║                                                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# Step 1: Prerequisites
print_header "Step 1: Checking Prerequisites"

print_step "Checking Docker..."
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed!"
    exit 1
fi
print_success "Docker is installed"

print_step "Checking Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed!"
    exit 1
fi
print_success "Docker Compose is installed"

# Step 2: Clean up
print_header "Step 2: Cleaning Up Old Containers"

print_step "Stopping all existing containers..."
docker-compose -f docker-compose.dev.yml down -v 2>/dev/null || true
print_success "Old containers stopped and volumes removed"

# Step 3: Setup directory structure
print_header "Step 3: Setting Up Directory Structure"

print_step "Creating database directories..."
mkdir -p database/postgres/init
mkdir -p database/postgres/schema
mkdir -p database/falkordb/init
mkdir -p database/redis
mkdir -p backend/logs
print_success "Directories created"

# Step 4: Copy schema files
print_step "Ensuring schema files are in place..."
if [ ! -f "database/postgres/init/01-init-db.sql" ]; then
    print_error "Missing database/postgres/init/01-init-db.sql"
    print_error "Please ensure all SQL schema files are in place"
    exit 1
fi
print_success "Schema files verified"

# Step 5: Build images
print_header "Step 4: Building Docker Images"

print_step "Building all services (this may take 3-5 minutes)..."
docker-compose -f docker-compose.dev.yml build --no-cache

if [ $? -eq 0 ]; then
    print_success "All images built successfully!"
else
    print_error "Build failed! Check the output above."
    exit 1
fi

# Step 6: Start PostgreSQL
print_header "Step 5: Starting PostgreSQL"

print_step "Starting PostgreSQL service..."
docker-compose -f docker-compose.dev.yml up -d postgres
sleep 5

print_step "Waiting for PostgreSQL to initialize..."
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

# Step 7: Verify database setup
print_step "Verifying databases and user..."
sleep 3

# Check if modeling user exists
if docker exec modeling-postgres psql -U postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname='modeling'" | grep -q 1; then
    print_success "User 'modeling' exists"
else
    print_error "User 'modeling' was not created!"
    print_error "Check database/postgres/init/01-init-db.sql"
    exit 1
fi

# Check if databases exist
if docker exec modeling-postgres psql -U postgres -lqt | cut -d \| -f 1 | grep -qw modeling_platform; then
    print_success "Database 'modeling_platform' exists"
else
    print_error "Database 'modeling_platform' was not created!"
    exit 1
fi

# Step 8: Apply database schemas in correct order
print_header "Step 6: Applying Database Schemas"

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
        docker exec -i modeling-postgres psql -U modeling -d modeling_platform < "$schema_path" 2>&1 | grep -v "NOTICE"
        if [ $? -eq 0 ]; then
            print_success "$schema_file applied"
        else
            print_warning "$schema_file had warnings (may be okay if tables exist)"
        fi
    else
        print_error "Schema file not found: $schema_path"
        exit 1
    fi
done
print_success "All schemas applied"

# Step 9: Start FalkorDB
print_header "Step 7: Starting FalkorDB"

print_step "Starting FalkorDB service..."
docker-compose -f docker-compose.dev.yml up -d falkordb
sleep 5

print_step "Waiting for FalkorDB to be ready..."
COUNTER=0
until docker exec modeling-falkordb redis-cli -p 6379 PING > /dev/null 2>&1; do
    if [ $COUNTER -gt 30 ]; then
        print_error "FalkorDB failed to start!"
        docker-compose -f docker-compose.dev.yml logs falkordb
        exit 1
    fi
    echo -n "."
    sleep 2
    COUNTER=$((COUNTER + 1))
done
echo ""
print_success "FalkorDB is ready!"

# Initialize FalkorDB graph
print_step "Initializing FalkorDB graph..."
docker exec modeling-falkordb redis-cli -p 6379 GRAPH.QUERY modeling_graph "CREATE (:SystemNode {id: 'system-root', name: 'System Root', created_at: timestamp()})" > /dev/null 2>&1
docker exec modeling-falkordb redis-cli -p 6379 GRAPH.QUERY modeling_graph "MATCH (n:SystemNode) DELETE n" > /dev/null 2>&1
print_success "FalkorDB graph initialized"

# Step 10: Start Redis
print_header "Step 8: Starting Redis"

print_step "Starting Redis service..."
docker-compose -f docker-compose.dev.yml up -d redis
sleep 3

print_step "Waiting for Redis to be ready..."
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

# Step 11: Start Backend
print_header "Step 9: Starting Backend API"

print_step "Starting backend service..."
docker-compose -f docker-compose.dev.yml up -d backend

print_step "Waiting for backend to start..."
sleep 10

# Wait for backend health check
COUNTER=0
until curl -f http://localhost:8000/health > /dev/null 2>&1; do
    if [ $COUNTER -gt 60 ]; then
        print_error "Backend failed to start!"
        echo ""
        echo "Backend logs:"
        docker-compose -f docker-compose.dev.yml logs backend | tail -50
        exit 1
    fi
    echo -n "."
    sleep 2
    COUNTER=$((COUNTER + 1))
done
echo ""
print_success "Backend is ready!"

# Step 12: Initialize database with test data
print_header "Step 10: Initializing Database with Test Data"

print_step "Running database initialization script..."
docker exec modeling-backend python init_database.py

if [ $? -eq 0 ]; then
    print_success "Database initialized successfully"
else
    print_error "Database initialization failed!"
    echo ""
    echo "Please check the output above for errors."
    exit 1
fi

# Step 13: Start Frontend
print_header "Step 11: Starting Frontend"

print_step "Starting frontend service..."
docker-compose -f docker-compose.dev.yml up -d frontend
sleep 5
print_success "Frontend is starting..."

# Step 14: Final verification
print_header "Step 12: Final Verification"

echo ""
print_step "Checking all services..."
docker-compose -f docker-compose.dev.yml ps

echo ""
print_step "Testing service endpoints..."

# Test PostgreSQL
if docker exec modeling-postgres psql -U modeling -d modeling_platform -c "SELECT 1;" > /dev/null 2>&1; then
    print_success "PostgreSQL: ✓ Connected"
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

# Test Backend
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    print_success "Backend API: ✓ Running"
else
    print_warning "Backend API: Still starting..."
fi

# Test Frontend
sleep 2
if curl -f http://localhost:5173 > /dev/null 2>&1; then
    print_success "Frontend: ✓ Running"
else
    print_warning "Frontend: Still starting..."
fi

# Summary
print_header "🎉 Startup Complete!"

echo -e "${GREEN}All services are running!${NC}"
echo ""
echo -e "${CYAN}Access URLs:${NC}"
echo "  Frontend (React):     ${BLUE}http://localhost:5173${NC}"
echo "  Backend API:          ${BLUE}http://localhost:8000${NC}"
echo "  API Documentation:    ${BLUE}http://localhost:8000/docs${NC}"
echo "  FalkorDB Browser:     ${BLUE}http://localhost:3000${NC}"
echo ""
echo -e "${CYAN}Test Account:${NC}"
echo "  Email:                test@example.com"
echo "  Password:             password123"
echo ""
echo -e "${CYAN}Database Info:${NC}"
echo "  PostgreSQL:           localhost:5432"
echo "  Database:             modeling_platform"
echo "  Username:             modeling"
echo "  Password:             modeling_dev"
echo ""
echo -e "${CYAN}Useful Commands:${NC}"
echo "  View logs:            ${YELLOW}docker-compose -f docker-compose.dev.yml logs -f${NC}"
echo "  View backend logs:    ${YELLOW}docker-compose -f docker-compose.dev.yml logs -f backend${NC}"
echo "  Stop services:        ${YELLOW}docker-compose -f docker-compose.dev.yml stop${NC}"
echo "  Restart services:     ${YELLOW}docker-compose -f docker-compose.dev.yml restart${NC}"
echo "  Stop and remove:      ${YELLOW}docker-compose -f docker-compose.dev.yml down${NC}"
echo "  Re-initialize DB:     ${YELLOW}docker exec modeling-backend python init_database.py${NC}"
echo ""

# Ask if user wants to view logs
read -p "View live logs now? (y/N) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_step "Starting log viewer (Press Ctrl+C to exit)..."
    docker-compose -f docker-compose.dev.yml logs -f
fi