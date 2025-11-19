#!/bin/bash
# Validation script for Docker infrastructure

set -e

echo "🔍 Validating Docker Infrastructure..."
echo ""

ERRORS=0
WARNINGS=0

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $1 exists"
        return 0
    else
        echo -e "${RED}✗${NC} $1 is missing"
        return 1
    fi
}

check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✓${NC} $1 exists"
        return 0
    else
        echo -e "${RED}✗${NC} $1 is missing"
        return 1
    fi
}

warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    WARNINGS=$((WARNINGS + 1))
}

error() {
    echo -e "${RED}✗${NC} $1"
    ERRORS=$((ERRORS + 1))
}

echo "📋 Checking required files..."
echo ""

# Check .env file
if ! check_file ".env"; then
    error ".env file missing - copy from .env.example"
fi

# Check docker-compose.yml
if ! check_file "docker-compose.yml"; then
    error "docker-compose.yml missing"
fi

# Check database init script
if ! check_file "scripts/init-db.sql"; then
    error "scripts/init-db.sql missing"
fi

echo ""
echo "🐳 Checking Dockerfiles..."
echo ""

# Check API Dockerfile (Rust)
if check_file "activitywatch/aw-server-rust/Dockerfile"; then
    if [ ! -f "activitywatch/aw-server-rust/Cargo.toml" ]; then
        error "activitywatch/aw-server-rust/Cargo.toml missing"
    fi
    if [ ! -d "activitywatch/aw-server-rust/aw-datastore/migrations" ]; then
        error "activitywatch/aw-server-rust/aw-datastore/migrations directory missing"
    fi
fi

# Check Query service
if check_file "aw-query/Dockerfile"; then
    if ! check_file "aw-query/requirements.txt"; then
        error "aw-query/requirements.txt missing"
    fi
    if [ ! -d "aw-query/app" ]; then
        warn "aw-query/app directory missing - service may not be implemented"
    fi
fi

# Watcher service removed - watchers are external applications, not Docker containers

# Check WebUI
if check_file "aw-webui/Dockerfile"; then
    if ! check_file "aw-webui/nginx.conf"; then
        error "aw-webui/nginx.conf missing"
    fi
    if [ ! -d "activitywatch/aw-server-rust/aw-webui/dist" ]; then
        warn "activitywatch/aw-server-rust/aw-webui/dist missing - frontend may need to be built"
    fi
fi

echo ""
echo "🔧 Checking Docker Compose configuration..."
echo ""

# Validate docker-compose.yml syntax
if command -v docker-compose &> /dev/null || command -v docker &> /dev/null; then
    if docker-compose config > /dev/null 2>&1 || docker compose config > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} docker-compose.yml syntax is valid"
    else
        error "docker-compose.yml has syntax errors"
        docker-compose config 2>&1 | head -20 || docker compose config 2>&1 | head -20
    fi
else
    warn "Docker not available - skipping docker-compose validation"
fi

echo ""
echo "📦 Checking environment variables..."
echo ""

# Check if .env has required variables
if [ -f ".env" ]; then
    source .env 2>/dev/null || true
    
    if [ -z "$DB_PASSWORD" ]; then
        warn "DB_PASSWORD not set in .env"
    fi
    
    if [ -z "$REDIS_PASSWORD" ]; then
        warn "REDIS_PASSWORD not set in .env"
    fi
    
    if [ -z "$JWT_SECRET" ] || [ "$JWT_SECRET" = "change_this_secret_in_production_use_long_random_string" ]; then
        warn "JWT_SECRET should be changed from default value"
    fi
fi

echo ""
echo "📊 Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ recent Docker images..."
echo ""

# Check if Docker is available
if command -v docker &> /dev/null; then
    if docker info > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Docker daemon is running"
        echo ""
        echo "To test the infrastructure, run:"
        echo "  docker-compose up -d db redis"
        echo "  docker-compose ps"
        echo "  docker-compose logs -f"
    else
        warn "Docker daemon is not running"
        echo ""
        echo "To start Docker:"
        echo "  - macOS: Open Docker Desktop"
        echo "  - Linux: sudo systemctl start docker"
    fi
else
    warn "Docker is not installed"
fi

echo ""
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ Validation completed with $WARNINGS warning(s)${NC}"
    exit 0
else
    echo -e "${RED}✗ Validation failed with $ERRORS error(s) and $WARNINGS warning(s)${NC}"
    exit 1
fi

