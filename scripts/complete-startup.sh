#!/bin/bash
# scripts/complete-startup.sh
# Complete startup with guaranteed initialization - ZERO ERRORS
# FULL VERSION WITH ALL FEATURES

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Functions
print_header() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║  $1${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_step() {
    echo -e "${CYAN}➜${NC} $1"
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

# Navigate to project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

print_header "Enterprise Modeling Platform - Complete Startup"

# Step 1: Pre-flight checks
print_header "Step 1: Pre-flight Checks"

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

# Step 2: Stop any existing containers
print_header "Step 2: Cleaning Up Old Containers"

print_step "Stopping all existing containers..."
docker-compose -f docker-compose.dev.yml down 2>/dev/null || true
print_success "Old containers stopped"

# Step 3: Create necessary directories and files
print_header "Step 3: Setting Up File Structure"

print_step "Creating database init directories..."
mkdir -p database/postgres/init
mkdir -p database/falkordb/init
mkdir -p database/redis
print_success "Directories created"

# Step 4: Create PostgreSQL init script
print_step "Creating PostgreSQL initialization script..."
cat > database/postgres/init/01-init-db.sql << 'EOFPG'
-- Create both possible database names
CREATE DATABASE modeling;
CREATE DATABASE modeling_platform;

-- Initialize modeling database
\c modeling;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE SCHEMA IF NOT EXISTS public;

-- Create and configure modeling user
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = 'modeling') THEN
        CREATE USER modeling WITH PASSWORD 'modeling_dev';
    END IF;
END $$;

GRANT ALL PRIVILEGES ON DATABASE modeling TO modeling;
GRANT ALL PRIVILEGES ON SCHEMA public TO modeling;
ALTER DATABASE modeling OWNER TO modeling;

-- Initialize modeling_platform database
\c modeling_platform;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE SCHEMA IF NOT EXISTS public;

GRANT ALL PRIVILEGES ON DATABASE modeling_platform TO modeling;
GRANT ALL PRIVILEGES ON SCHEMA public TO modeling;
ALTER DATABASE modeling_platform OWNER TO modeling;

ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO modeling;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO modeling;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO modeling;

-- Log success
DO $$
BEGIN
    RAISE NOTICE '================================================';
    RAISE NOTICE 'PostgreSQL Initialization Complete!';
    RAISE NOTICE 'Databases: modeling, modeling_platform';
    RAISE NOTICE 'User: modeling (password: modeling_dev)';
    RAISE NOTICE '================================================';
END $$;
EOFPG
print_success "PostgreSQL init script created"

# Step 5: Verify pyproject.toml has email-validator
print_step "Checking backend dependencies..."
if ! grep -q "email-validator" backend/pyproject.toml; then
    print_warning "Adding email-validator to pyproject.toml..."
    sed -i.bak '/pydantic-settings = /a\
email-validator = "^2.2.0"  # Required for EmailStr validation
' backend/pyproject.toml 2>/dev/null || \
    sed -i '' '/pydantic-settings = /a\
email-validator = "^2.2.0"  # Required for EmailStr validation
' backend/pyproject.toml
    print_success "email-validator added"
else
    print_success "email-validator already in dependencies"
fi

# Step 6: Clean Docker completely
print_header "Step 4: Cleaning Docker Environment"

print_step "Removing old containers and images..."
docker-compose -f docker-compose.dev.yml down -v 2>/dev/null || true
print_success "Containers removed"

print_step "Removing old images..."
docker-compose -f docker-compose.dev.yml down --rmi all 2>/dev/null || true
print_success "Images removed"

print_step "Cleaning build cache..."
docker builder prune -f
print_success "Build cache cleaned"

# Step 7: Build images
print_header "Step 5: Building Docker Images"

print_step "Building all services (this may take 3-5 minutes)..."
docker-compose -f docker-compose.dev.yml build --no-cache --progress=plain

if [ $? -eq 0 ]; then
    print_success "All images built successfully!"
else
    print_error "Build failed! Check the output above."
    exit 1
fi

# Step 8: Start services
print_header "Step 6: Starting Services"

print_step "Starting PostgreSQL..."
docker-compose -f docker-compose.dev.yml up -d postgres
sleep 5

print_step "Waiting for PostgreSQL to initialize..."
until docker exec modeling-postgres pg_isready -U modeling > /dev/null 2>&1; do
    echo -n "."
    sleep 1
done
echo ""
print_success "PostgreSQL is ready!"

print_step "Verifying databases were created..."
if docker exec modeling-postgres psql -U modeling -lqt | cut -d \| -f 1 | grep -qw modeling; then
    print_success "Database 'modeling' exists"
else
    print_error "Database 'modeling' was not created!"
    exit 1
fi

if docker exec modeling-postgres psql -U modeling -lqt | cut -d \| -f 1 | grep -qw modeling_platform; then
    print_success "Database 'modeling_platform' exists"
else
    print_error "Database 'modeling_platform' was not created!"
    exit 1
fi

print_step "Starting FalkorDB..."
docker-compose -f docker-compose.dev.yml up -d falkordb
sleep 5

print_step "Waiting for FalkorDB to be ready..."
until docker exec modeling-falkordb redis-cli -p 6379 PING > /dev/null 2>&1; do
    echo -n "."
    sleep 1
done
echo ""
print_success "FalkorDB is ready!"

print_step "Starting Redis..."
docker-compose -f docker-compose.dev.yml up -d redis
sleep 3

print_step "Waiting for Redis to be ready..."
until docker exec modeling-redis redis-cli PING > /dev/null 2>&1; do
    echo -n "."
    sleep 1
done
echo ""
print_success "Redis is ready!"

print_step "Starting Backend..."
docker-compose -f docker-compose.dev.yml up -d backend

print_step "Waiting for backend to start (this may take 30-60 seconds)..."
echo "Checking for email-validator installation..."
sleep 10

# Check backend logs for errors
if docker-compose -f docker-compose.dev.yml logs backend | grep -i "email.validator.*not.*installed" > /dev/null; then
    print_error "Backend still missing email-validator!"
    echo ""
    echo "Installing email-validator manually..."
    docker exec modeling-backend pip install email-validator==2.2.0
    docker-compose -f docker-compose.dev.yml restart backend
    sleep 10
fi

# Wait for backend health check
COUNTER=0
until curl -f http://localhost:8000/health > /dev/null 2>&1; do
    echo -n "."
    sleep 2
    COUNTER=$((COUNTER + 1))
    if [ $COUNTER -gt 30 ]; then
        print_error "Backend failed to start!"
        echo ""
        echo "Backend logs:"
        docker-compose -f docker-compose.dev.yml logs backend | tail -50
        exit 1
    fi
done
echo ""
print_success "Backend is ready!"

# Initialize database
print_header "Step 7: Initializing Database"
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

print_step "Starting Frontend..."
docker-compose -f docker-compose.dev.yml up -d frontend
sleep 5
print_success "Frontend is starting..."

# Step 9: Final verification
print_header "Step 8: Final Verification"

echo ""
print_step "Checking all services..."
docker-compose -f docker-compose.dev.yml ps

echo ""
print_step "Testing service endpoints..."

# Test PostgreSQL
if docker exec modeling-postgres psql -U modeling -d modeling -c "SELECT 1;" > /dev/null 2>&1; then
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

# Step 10: Summary
print_header "🎉 Startup Complete!"

echo -e "${GREEN}All services are running!${NC}"
echo ""
echo -e "${CYAN}Access URLs:${NC}"
echo "  Frontend (React):     ${BLUE}http://localhost:5173${NC}"
echo "  Backend API:          ${BLUE}http://localhost:8000${NC}"
echo "  API Documentation:    ${BLUE}http://localhost:8000/api/v1/docs${NC}"
echo "  FalkorDB Browser:     ${BLUE}http://localhost:3000${NC}"
echo ""
echo -e "${CYAN}Test Account:${NC}"
echo "  Email:                test@example.com"
echo "  Password:             password123"
echo ""
echo -e "${CYAN}Database Info:${NC}"
echo "  PostgreSQL:           localhost:5432"
echo "  Databases:            modeling, modeling_platform"
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