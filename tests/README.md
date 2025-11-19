# ActivityWatch Integration Tests

Comprehensive pytest-based integration tests for verifying communication between all ActivityWatch services.

## Overview

This test suite verifies that all services (Database, Redis Cache, API, WebUI, Query) are properly communicating with each other. Tests are organized into focused categories with small, atomic test functions.

## Test Structure

Tests are organized into folders by component. Each test file contains small, focused tests that cover one specific scenario.

```
tests/
├── api/                           # API service tests (~30 tests)
│   ├── test_api.py                # Basic API endpoints (9 tests)
│   ├── test_api_edge_cases.py     # Edge cases and error scenarios (18 tests)
│   ├── test_api_concurrency.py    # Concurrency tests (6 tests)
│   └── test_api_performance.py    # Performance tests (6 tests)
├── database/                      # Database tests (~19 tests)
│   ├── test_database.py           # Basic database operations (8 tests)
│   ├── test_database_constraints.py  # Constraint tests (5 tests)
│   └── test_database_queries.py      # Query tests (6 tests)
├── integration/                   # Integration tests (~12 tests)
│   ├── test_integration.py        # Basic integration scenarios (7 tests)
│   └── test_integration_data_consistency.py  # Data consistency (5 tests)
├── webui/                         # WebUI tests (6 tests)
│   └── test_webui.py              # WebUI functionality
├── redis/                         # Redis tests (6 tests)
│   └── test_redis.py              # Redis cache operations
├── conftest.py                    # Shared fixtures and configuration
├── pytest.ini                     # Pytest configuration
├── requirements.txt               # Test dependencies
├── run_tests.sh                   # Test runner script
└── README.md                      # This file
```

**Total: ~83 focused tests** organized into clear categories.

## Prerequisites

1. **Docker services must be running:**

   ```bash
   docker-compose up -d
   ```

2. **Install test dependencies:**

   ```bash
   pip install -r tests/requirements.txt
   ```

3. **Environment variables** (can be set in `.env` file):
   - `DB_HOST` (default: localhost)
   - `DB_PORT` (default: 5432)
   - `POSTGRES_DB` (default: activitywatch)
   - `POSTGRES_USER` (default: aw_user)
   - `DB_PASSWORD` (default: activitywatch_password)
   - `REDIS_HOST` (default: localhost)
   - `REDIS_PORT` (default: 6379)
   - `REDIS_PASSWORD` (default: redis_password)
   - `API_URL` (default: http://localhost:5600)
   - `WEBUI_URL` (default: http://localhost:8080)
   - `QUERY_URL` (default: http://localhost:8082)

## Running Tests

### From VS Code

1. **Install Python extension** (VS Code will prompt you)
2. **Open any test file** (`test_*.py`)
3. **Click "Run Test"** or "Debug Test" above any test function
4. **Use Test Explorer panel** (beaker icon in sidebar)

**Quick Actions:**

- Click ▶️ above test functions to run individual tests
- Press `Ctrl+Shift+P` → "Python: Run All Tests"
- Use Tasks (`Ctrl+Shift+P` → "Tasks: Run Task") for predefined test runs
- Debug tests with breakpoints using F5

See `.vscode/README.md` for detailed VS Code setup.

### From Command Line

#### Run all tests:

```bash
pytest tests/
# or
python3 -m pytest tests/
```

#### Run specific category:

```bash
# API tests
pytest tests/api/ -v

# Database tests
pytest tests/database/ -v

# Integration tests
pytest tests/integration/ -v

# WebUI tests
pytest tests/webui/ -v

# Redis tests
pytest tests/redis/ -v
```

#### Run specific test file:

```bash
pytest tests/api/test_api.py -v
pytest tests/database/test_database.py -v
```

#### Run specific test:

```bash
pytest tests/api/test_api.py::test_api_health_check -v
```

#### Run with coverage:

```bash
pytest tests/ --cov=. --cov-report=html
```

#### Using the test script:

```bash
./tests/run_tests.sh              # Run all tests
./tests/run_tests.sh --api        # Run API tests only
./tests/run_tests.sh --database   # Run database tests only
./tests/run_tests.sh --coverage   # Run with coverage
```

## Test Categories

### API Tests (`tests/api/`)

**Basic Tests** (`test_api.py`):

- Health check endpoint
- Info endpoint
- Bucket CRUD operations
- Event creation
- Query endpoint
- Settings endpoints
- CORS headers
- Error handling

**Edge Cases** (`test_api_edge_cases.py`):

- Duplicate bucket creation
- Missing/invalid fields
- Invalid timestamp formats
- Empty arrays
- Large payloads
- Unicode data handling
- Special characters
- Time range queries

**Concurrency** (`test_api_concurrency.py`):

- Concurrent bucket creation
- Concurrent event creation
- Concurrent read/write operations
- Batch operations
- Data integrity under load

**Performance** (`test_api_performance.py`):

- Response time consistency
- Health check performance
- Bucket/event creation performance
- Batch creation performance
- Query performance

### Database Tests (`tests/database/`)

**Basic Tests** (`test_database.py`):

- Database connectivity
- TimescaleDB extension verification
- Table existence checks
- CRUD operations
- Event insertion
- Foreign key constraints
- Index verification

**Constraints** (`test_database_constraints.py`):

- Unique constraints
- Foreign key constraints
- Cascade deletes
- NULL value handling
- NOT NULL constraints

**Queries** (`test_database_queries.py`):

- JSONB path queries
- JSONB contains operator
- Time range queries
- Index usage verification
- Aggregation queries

### Integration Tests (`tests/integration/`)

**Basic Integration** (`test_integration.py`):

- API to Database integration
- WebUI to API integration
- Database to API read integration
- Redis cache integration
- Full workflow tests
- Concurrent operations

**Data Consistency** (`test_integration_data_consistency.py`):

- API/WebUI data consistency
- Error consistency
- Time range consistency
- Header preservation
- Error propagation

### WebUI Tests (`tests/webui/`)

- Health check
- Static file serving
- API proxying
- Security headers
- SPA routing
- Gzip compression

### Redis Tests (`tests/redis/`)

- Redis connectivity
- Basic operations (set/get)
- JSON operations
- Expiration
- Hash and list operations
- Authentication

## Test Principles

### Small Focused Tests

- Each test function tests exactly one scenario
- Clear, descriptive test names following pattern: `test_<component>_<scenario>_<expected>`
- Independent tests (no shared state)
- Automatic cleanup after each test

### Test Organization

- Tests grouped by component (API, Database, etc.)
- Related tests in same file
- Edge cases, concurrency, and performance in separate files
- Easy to find and run specific test categories

## Expected Test Results

All tests should pass when:

1. All Docker services are running and healthy
2. Database is initialized with proper schema
3. Redis is accessible with correct password
4. API server is running and connected to database
5. WebUI is running and proxying correctly

## Troubleshooting

### Connection Errors

- Verify Docker services: `docker-compose ps`
- Check service logs: `docker-compose logs`
- Verify environment variables match `.env` file

### Database Errors

- Check database: `docker-compose exec db psql -U aw_user -d activitywatch`
- Verify schema exists (check for `buckets`, `events`, `key_value` tables)

### Redis Errors

- Test Redis: `docker-compose exec redis redis-cli -a <password> ping`
- Verify password matches `.env` file

### API Errors

- Check API logs: `docker-compose logs api`
- Verify API health: `curl http://localhost:5600/health`
- Ensure API can connect to database

### WebUI Errors

- Check WebUI logs: `docker-compose logs webui`
- Verify WebUI health: `curl http://localhost:8080/health`
- Ensure WebUI can proxy to API

### Test Discovery Issues

- Check Python interpreter: `Ctrl+Shift+P` → "Python: Select Interpreter"
- Reload window: `Ctrl+Shift+P` → "Developer: Reload Window"
- Verify pytest: `python3 -m pytest --version`

## Continuous Integration

These tests are CI/CD friendly:

```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Start services
        run: docker-compose up -d
      - name: Wait for services
        run: sleep 30
      - name: Install dependencies
        run: pip install -r tests/requirements.txt
      - name: Run tests
        run: pytest tests/ -v
```

## Notes

- Tests use `test-` prefixed bucket IDs that are automatically cleaned up
- Some tests may require services to be fully initialized (wait 30-60 seconds after `docker-compose up`)
- Tests are idempotent and can be run multiple times safely
- Test data is automatically cleaned up after each test
- Tests are organized into folders for better maintainability
- Each test file focuses on a specific aspect (basic, edge cases, concurrency, performance, etc.)
