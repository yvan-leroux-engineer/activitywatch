# Testing API Key Functionality

## Prerequisites

Before running API key tests, the server must be rebuilt with the new code:

```bash
# Rebuild the API server
docker-compose build api

# Restart the API server
docker-compose up -d api

# Verify the server is running
curl http://localhost:5600/health
```

## Running Tests

### Database Tests (Migration Verification)

These tests verify the database migration worked correctly:

```bash
pytest tests/database/test_api_keys_table.py -v
```

**Requirements:**
- Database must be accessible
- Migration must have run (happens automatically on server start)

### API Endpoint Tests

These tests verify the API key management endpoints:

```bash
pytest tests/api/test_api_keys.py -v
```

**Requirements:**
- Server must be rebuilt with new code
- Server must be running on localhost:5600

### Client Tests

These tests verify client-side HTTPS and API key support:

```bash
pytest tests/client/test_client_https.py -v
```

**Requirements:**
- aw-client dependencies must be installed
- Can run without server (unit tests)

## Test Coverage

### Database Tests
- ✅ Table existence after migration
- ✅ Table structure (columns, types, constraints)
- ✅ Indexes for performance
- ✅ Insert and query operations
- ✅ Uniqueness constraints

### API Endpoint Tests
- ✅ Create API key
- ✅ List API keys (without exposing keys)
- ✅ Revoke API key
- ✅ Authentication required when enabled
- ✅ Heartbeat with API key
- ✅ Invalid key rejection

### Client Tests
- ✅ Session creation for connection pooling
- ✅ API key header addition
- ✅ HTTPS configuration
- ✅ SSL verification settings
- ✅ Session recreation on disconnect

## Expected Results

### After Server Rebuild

All API key endpoint tests should pass:
- `test_api_key_create` - Creates API key, returns it once
- `test_api_key_list` - Lists keys without exposing them
- `test_api_key_revoke` - Deactivates keys
- `test_api_key_authentication_required_when_enabled` - Enforces auth when enabled
- `test_api_key_heartbeat_with_auth` - Heartbeat works with API key

### Database Tests

Should pass if database is accessible:
- All table structure tests
- Insert/query tests
- Constraint tests

### Client Tests

Should pass if aw-client is importable:
- Session management tests
- Configuration tests
- Header management tests

## Troubleshooting

### Tests Skipping

If tests are being skipped:
1. **Database tests**: Check that `asyncpg` is installed and database is accessible
2. **API tests**: Check that server is rebuilt and running
3. **Client tests**: Check that aw-client can be imported

### 404 Errors

If API endpoints return 404:
- Server needs to be rebuilt: `docker-compose build api && docker-compose up -d api`
- Check server logs: `docker-compose logs api`
- Verify routes are mounted: Check server startup logs for route registration

### Import Errors

If client tests fail to import:
- Install aw-client dependencies: `cd activitywatch/aw-client && poetry install`
- Or install manually: `pip install requests persistqueue`


