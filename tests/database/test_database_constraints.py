"""
Small, focused database constraint tests - each test covers one constraint scenario
"""
import pytest
import asyncpg
from datetime import datetime, timezone
import json


@pytest.mark.asyncio
async def test_database_unique_constraint_bucket_id(db_connection: asyncpg.Connection):
    """Test unique constraint on bucket_id."""
    bucket_id = "test-unique-constraint"
    
    # Create first bucket
    await db_connection.execute(
        """
        INSERT INTO buckets (bucket_id, name, type, client, hostname, created)
        VALUES ($1, $2, $3, $4, $5, $6)
        """,
        bucket_id,
        "First Bucket",
        "test",
        "test-client",
        "test-host",
        datetime.now(timezone.utc),
    )
    
    # Try to create duplicate
    with pytest.raises(asyncpg.UniqueViolationError):
        await db_connection.execute(
            """
            INSERT INTO buckets (bucket_id, name, type, client, hostname, created)
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            bucket_id,
            "Duplicate Bucket",
            "test",
            "test-client",
            "test-host",
            datetime.now(timezone.utc),
        )
    
    # Cleanup
    await db_connection.execute(
        "DELETE FROM buckets WHERE bucket_id = $1", bucket_id
    )


@pytest.mark.asyncio
async def test_database_foreign_key_constraint_events(db_connection: asyncpg.Connection):
    """Test foreign key constraint on events table."""
    # Try to insert event with non-existent bucket_id
    with pytest.raises(asyncpg.ForeignKeyViolationError):
        await db_connection.execute(
            """
            INSERT INTO events (bucket_id, timestamp, duration, data)
            VALUES ($1, $2, $3, $4)
            """,
            "non-existent-bucket",
            datetime.now(timezone.utc),
            1000000,
            json.dumps({}),
        )


@pytest.mark.asyncio
async def test_database_cascade_delete_events(db_connection: asyncpg.Connection):
    """Test cascade delete - deleting bucket deletes events."""
    bucket_id = "test-cascade-delete"
    
    # Create bucket
    await db_connection.execute(
        """
        INSERT INTO buckets (bucket_id, name, type, client, hostname, created)
        VALUES ($1, $2, $3, $4, $5, $6)
        """,
        bucket_id,
        "Cascade Test Bucket",
        "test",
        "test-client",
        "test-host",
        datetime.now(timezone.utc),
    )
    
    # Create multiple events
    from datetime import timedelta
    timestamp = datetime.now(timezone.utc)
    for i in range(5):
        await db_connection.execute(
            """
            INSERT INTO events (bucket_id, timestamp, duration, data)
            VALUES ($1, $2, $3, $4)
            """,
            bucket_id,
            timestamp + timedelta(seconds=i),
            1000000,
            json.dumps({"index": i}),
        )
    
    # Verify events exist
    event_count = await db_connection.fetchval(
        "SELECT COUNT(*) FROM events WHERE bucket_id = $1", bucket_id
    )
    assert event_count == 5
    
    # Delete bucket
    await db_connection.execute(
        "DELETE FROM buckets WHERE bucket_id = $1", bucket_id
    )
    
    # Verify events were cascade deleted
    event_count = await db_connection.fetchval(
        "SELECT COUNT(*) FROM events WHERE bucket_id = $1", bucket_id
    )
    assert event_count == 0


@pytest.mark.asyncio
async def test_database_null_values_allowed(db_connection: asyncpg.Connection):
    """Test handling of NULL values in optional fields."""
    bucket_id = "test-null-values"
    
    # Create bucket with NULL name (if allowed)
    await db_connection.execute(
        """
        INSERT INTO buckets (bucket_id, name, type, client, hostname, created)
        VALUES ($1, $2, $3, $4, $5, $6)
        """,
        bucket_id,
        None,  # NULL name
        "test",
        "test-client",
        "test-host",
        datetime.now(timezone.utc),
    )
    
    # Verify bucket was created
    bucket = await db_connection.fetchrow(
        "SELECT * FROM buckets WHERE bucket_id = $1", bucket_id
    )
    assert bucket is not None
    assert bucket["name"] is None
    
    # Cleanup
    await db_connection.execute(
        "DELETE FROM buckets WHERE bucket_id = $1", bucket_id
    )


@pytest.mark.asyncio
async def test_database_not_null_constraints(db_connection: asyncpg.Connection):
    """Test NOT NULL constraints are enforced."""
    bucket_id = "test-not-null"
    
    # Try to create bucket with NULL required fields
    with pytest.raises(asyncpg.NotNullViolationError):
        await db_connection.execute(
            """
            INSERT INTO buckets (bucket_id, name, type, client, hostname, created)
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            bucket_id,
            "Test Bucket",
            None,  # NULL type (should fail)
            "test-client",
            "test-host",
            datetime.now(timezone.utc),
        )

