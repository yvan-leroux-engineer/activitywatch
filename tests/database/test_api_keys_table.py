"""
Tests for API keys database table and migration
"""

import pytest

try:
    import asyncpg
    ASYNCPG_AVAILABLE = True
except ImportError:
    ASYNCPG_AVAILABLE = False


@pytest.mark.asyncio
@pytest.mark.skipif(not ASYNCPG_AVAILABLE, reason="asyncpg not available")
async def test_api_keys_table_exists(db_connection):
    """Test that api_keys table exists after migration."""
    # Check if table exists
    table_exists = await db_connection.fetchval("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'api_keys'
        )
    """)
    
    assert table_exists, "api_keys table should exist after migration"


@pytest.mark.asyncio
@pytest.mark.skipif(not ASYNCPG_AVAILABLE, reason="asyncpg not available")
async def test_api_keys_table_structure(db_connection):
    """Test that api_keys table has correct structure."""
    columns = await db_connection.fetch("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'api_keys'
        ORDER BY column_name
    """)
    
    column_names = {col['column_name']: col for col in columns}
    
    # Verify required columns exist
    assert 'id' in column_names
    assert column_names['id']['data_type'] == 'integer'
    
    assert 'key_hash' in column_names
    assert column_names['key_hash']['data_type'] in ['character varying', 'varchar', 'text']
    
    assert 'client_id' in column_names
    assert 'created_at' in column_names
    assert column_names['created_at']['data_type'] in ['timestamp with time zone', 'timestamptz']
    
    assert 'last_used_at' in column_names
    assert column_names['last_used_at']['is_nullable'] == 'YES'  # Can be NULL
    
    assert 'is_active' in column_names
    assert column_names['is_active']['data_type'] == 'boolean'
    
    # Verify key_hash is unique
    constraints = await db_connection.fetch("""
        SELECT constraint_name, constraint_type
        FROM information_schema.table_constraints
        WHERE table_name = 'api_keys'
    """)
    
    constraint_types = [c['constraint_type'] for c in constraints]
    assert 'UNIQUE' in constraint_types or 'PRIMARY KEY' in constraint_types


@pytest.mark.asyncio
@pytest.mark.skipif(not ASYNCPG_AVAILABLE, reason="asyncpg not available")
async def test_api_keys_indexes_exist(db_connection):
    """Test that indexes exist on api_keys table."""
    indexes = await db_connection.fetch("""
        SELECT indexname
        FROM pg_indexes
        WHERE tablename = 'api_keys'
    """)
    
    index_names = [idx['indexname'] for idx in indexes]
    
    # Should have indexes on key_hash and client_id for fast lookups
    key_hash_index = any('key_hash' in name for name in index_names)
    client_id_index = any('client_id' in name for name in index_names)
    is_active_index = any('is_active' in name for name in index_names)
    
    assert key_hash_index, "Should have index on key_hash"
    assert client_id_index, "Should have index on client_id"
    assert is_active_index, "Should have index on is_active"


@pytest.mark.asyncio
@pytest.mark.skipif(not ASYNCPG_AVAILABLE, reason="asyncpg not available")
async def test_api_keys_insert_and_query(db_connection):
    """Test inserting and querying API keys."""
    import hashlib
    from datetime import datetime, timezone
    
    # Generate a test key hash
    test_key = "test-key-12345"
    key_hash = hashlib.sha256(test_key.encode()).hexdigest()
    client_id = "test-db-client"
    
    # Insert a test API key
    key_id = await db_connection.fetchval("""
        INSERT INTO api_keys (key_hash, client_id, description, created_at, is_active)
        VALUES ($1, $2, $3, $4, TRUE)
        RETURNING id
    """, key_hash, client_id, "Test key", datetime.now(timezone.utc))
    
    assert key_id is not None
    
    # Query it back
    row = await db_connection.fetchrow("""
        SELECT id, key_hash, client_id, is_active
        FROM api_keys
        WHERE id = $1
    """, key_id)
    
    assert row is not None
    assert row['key_hash'] == key_hash
    assert row['client_id'] == client_id
    assert row['is_active'] is True
    
    # Cleanup
    await db_connection.execute("DELETE FROM api_keys WHERE id = $1", key_id)


@pytest.mark.asyncio
@pytest.mark.skipif(not ASYNCPG_AVAILABLE, reason="asyncpg not available")
async def test_api_keys_hash_uniqueness(db_connection):
    """Test that key_hash must be unique."""
    import hashlib
    from datetime import datetime, timezone
    
    test_key = "test-unique-key"
    key_hash = hashlib.sha256(test_key.encode()).hexdigest()
    
    # Insert first key
    key_id1 = await db_connection.fetchval("""
        INSERT INTO api_keys (key_hash, client_id, created_at, is_active)
        VALUES ($1, $2, $3, TRUE)
        RETURNING id
    """, key_hash, "client1", datetime.now(timezone.utc))
    
    # Try to insert duplicate key_hash (should fail)
    with pytest.raises(asyncpg.UniqueViolationError):
        await db_connection.fetchval("""
            INSERT INTO api_keys (key_hash, client_id, created_at, is_active)
            VALUES ($1, $2, $3, TRUE)
            RETURNING id
        """, key_hash, "client2", datetime.now(timezone.utc))
    
    # Cleanup
    await db_connection.execute("DELETE FROM api_keys WHERE id = $1", key_id1)


