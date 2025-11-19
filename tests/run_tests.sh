#!/bin/bash
# Script to run integration tests with proper setup

set -e

echo "🧪 ActivityWatch Integration Tests"
echo "=================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}✗ Docker is not running${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Docker is running"
echo ""

# Check if services are running
echo "🔍 Checking Docker services..."
if ! docker-compose ps | grep -q "aw-db.*Up"; then
    echo -e "${YELLOW}⚠${NC} Database service not running. Starting services..."
    docker-compose up -d
    echo "⏳ Waiting for services to be ready..."
    sleep 30
else
    echo -e "${GREEN}✓${NC} Services are running"
fi

echo ""

# Check if test dependencies are installed
echo "📦 Checking test dependencies..."
if ! python3 -c "import pytest" 2>/dev/null; then
    echo -e "${YELLOW}⚠${NC} pytest not found. Installing dependencies..."
    pip install -r tests/requirements.txt
else
    echo -e "${GREEN}✓${NC} Test dependencies installed"
fi

echo ""

# Run tests
echo "🚀 Running tests..."
echo ""

if [ "$1" == "--verbose" ] || [ "$1" == "-v" ]; then
    pytest tests/api tests/database tests/integration tests/webui tests/redis -v
elif [ "$1" == "--coverage" ] || [ "$1" == "-c" ]; then
    pytest tests/api tests/database tests/integration tests/webui tests/redis --cov=. --cov-report=html --cov-report=term
elif [ "$1" == "--api" ]; then
    pytest tests/api -v
elif [ "$1" == "--database" ]; then
    pytest tests/database -v
elif [ "$1" == "--integration" ]; then
    pytest tests/integration -v
elif [ "$1" == "--webui" ]; then
    pytest tests/webui -v
elif [ "$1" == "--redis" ]; then
    pytest tests/redis -v
elif [ -n "$1" ]; then
    pytest tests/api tests/database tests/integration tests/webui tests/redis "$@"
else
    pytest tests/api tests/database tests/integration tests/webui tests/redis -v
fi

TEST_EXIT_CODE=$?

echo ""
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
else
    echo -e "${RED}✗ Some tests failed${NC}"
fi

exit $TEST_EXIT_CODE

