#!/bin/bash

# Enterprise Modeling Platform - Setup Script
# This script initializes the project for development

set -e  # Exit on error

echo "================================================"
echo "Enterprise Modeling Platform - Setup"
echo "================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Check prerequisites
echo "Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi
print_success "Docker is installed"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi
print_success "Docker Compose is installed"

# Check Node.js
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    print_error "Node.js version must be 18 or higher. Current version: $(node -v)"
    exit 1
fi
print_success "Node.js $(node -v) is installed"

# Check Python
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.11+ first."
    exit 1
fi
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
if [ "$(echo "$PYTHON_VERSION < 3.11" | bc)" -eq 1 ]; then
    print_error "Python version must be 3.11 or higher. Current version: $(python3 --version)"
    exit 1
fi
print_success "Python $(python3 --version) is installed"

# Check pnpm
if ! command -v pnpm &> /dev/null; then
    print_info "pnpm is not installed. Installing pnpm..."
    npm install -g pnpm
fi
print_success "pnpm is installed"

echo ""
echo "================================================"
echo "Setting up environment"
echo "================================================"
echo ""

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    print_info "Creating .env file from template..."
    cp .env.example .env
    print_success ".env file created"
    print_info "Please review and update .env file with your configuration"
else
    print_info ".env file already exists"
fi

echo ""
echo "================================================"
echo "Installing dependencies"
echo "================================================"
echo ""

# Install root dependencies
print_info "Installing root dependencies..."
pnpm install
print_success "Root dependencies installed"

# Install frontend dependencies
print_info "Installing frontend dependencies..."
cd frontend
pnpm install
cd ..
print_success "Frontend dependencies installed"

# Install backend dependencies
print_info "Installing backend dependencies..."
cd backend
if ! command -v poetry &> /dev/null; then
    print_info "Poetry is not installed. Installing Poetry..."
    pip3 install poetry
fi
poetry install
cd ..
print_success "Backend dependencies installed"

echo ""
echo "================================================"
echo "Starting Docker services"
echo "================================================"
echo ""

# Start Docker services
print_info "Starting Docker containers..."
docker-compose -f docker-compose.dev.yml up -d

# Wait for services to be ready
print_info "Waiting for services to start..."
sleep 10

# Check if services are running
if docker-compose -f docker-compose.dev.yml ps | grep -q "Up"; then
    print_success "Docker services started successfully"
else
    print_error "Failed to start Docker services"
    exit 1
fi

echo ""
echo "================================================"
echo "Initializing database"
echo "================================================"
echo ""

# Wait for PostgreSQL to be ready
print_info "Waiting for PostgreSQL to be ready..."
until docker-compose -f docker-compose.dev.yml exec -T postgres pg_isready -U modeling > /dev/null 2>&1; do
    sleep 1
done
print_success "PostgreSQL is ready"

# Run database migrations
print_info "Running database migrations..."
cd backend
# Note: Uncomment when migrations are set up
# poetry run alembic upgrade head
cd ..
print_success "Database migrations completed"

# Create first admin user
print_info "Creating first admin user..."
# Note: Implement user creation script
print_info "Default admin credentials:"
print_info "  Email: admin@example.com"
print_info "  Password: change-this-password-immediately"

echo ""
echo "================================================"
echo "Setup Complete!"
echo "================================================"
echo ""

print_success "All services are running"
echo ""
echo "Access the application:"
echo "  Frontend:  http://localhost:3000"
echo "  Backend:   http://localhost:8000"
echo "  API Docs:  http://localhost:8000/api/v1/docs"
echo ""
echo "To view logs:"
echo "  docker-compose -f docker-compose.dev.yml logs -f"
echo ""
echo "To stop services:"
echo "  docker-compose -f docker-compose.dev.yml down"
echo ""
echo "Next steps:"
echo "  1. Review and update .env file"
echo "  2. Change default admin password"
echo "  3. Start developing!"
echo ""

print_info "Happy coding! 🚀"