"""
Tests for PostgreSQL database connectivity and operations
"""

import pytest
import asyncpg
from datetime import datetime, timezone
import json


@pytest.mark.asyncio
async def test_database_connection(db_connection: asyncpg.Connection):
    """Test basic database connectivity."""
    result = await db_connection.fetchval("SELECT 1")
    assert result == 1


@pytest.mark.asyncio
async def test_timescaledb_extension(db_connection: asyncpg.Connection):
    """Test that TimescaleDB extension is installed."""
    result = await db_connection.fetchval(
        "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'timescaledb')"
    )
    assert result is True, "TimescaleDB extension should be installed"


@pytest.mark.asyncio
async def test_tables_exist(db_connection: asyncpg.Connection):
    """Test that required tables exist."""
    tables = await db_connection.fetch(
        """
        SELECT tablename FROM pg_tables 
        WHERE schemaname = 'public' 
        AND tablename IN ('buckets', 'events', 'key_value')
        ORDER BY tablename
        """
    )
    table_names = [row["tablename"] for row in tables]
    assert "buckets" in table_names, "buckets table should exist"
    assert "events" in table_names, "events table should exist"
    assert "key_value" in table_names, "key_value table should exist"


@pytest.mark.asyncio
async def test_events_hypertable(db_connection: asyncpg.Connection):
    """Test that events table is a TimescaleDB hypertable."""
    result = await db_connection.fetchval(
        """
        SELECT EXISTS(
            SELECT 1 FROM timescaledb_information.hypertables 
            WHERE hypertable_name = 'events'
        )
        """
    )
    assert result is True, "events table should be a hypertable"


@pytest.mark.asyncio
async def test_bucket_crud_operations(db_connection: asyncpg.Connection):
    """Test CRUD operations on buckets table."""
    bucket_id = "test-bucket-crud"

    # Create bucket
    await db_connection.execute(
        """
        INSERT INTO buckets (bucket_id, name, type, client, hostname, created, data)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        """,
        bucket_id,
        "Test Bucket",
        "test",
        "test-client",
        "test-host",
        datetime.now(timezone.utc),
        json.dumps({"test": "data"}),
    )

    # Read bucket
    bucket = await db_connection.fetchrow(
        "SELECT * FROM buckets WHERE bucket_id = $1", bucket_id
    )
    assert bucket is not None, "Bucket should be created"
    assert bucket["name"] == "Test Bucket"
    assert bucket["type"] == "test"

    # Update bucket
    await db_connection.execute(
        "UPDATE buckets SET name = $1 WHERE bucket_id = $2",
        "Updated Test Bucket",
        bucket_id,
    )

    updated_bucket = await db_connection.fetchrow(
        "SELECT * FROM buckets WHERE bucket_id = $1", bucket_id
    )
    assert updated_bucket["name"] == "Updated Test Bucket"

    # Delete bucket
    await db_connection.execute(
        "DELETE FROM buckets WHERE bucket_id = $1", bucket_id
    )

    deleted_bucket = await db_connection.fetchrow(
        "SELECT * FROM buckets WHERE bucket_id = $1", bucket_id
    )
    assert deleted_bucket is None, "Bucket should be deleted"


@pytest.mark.asyncio
async def test_event_insertion(db_connection: asyncpg.Connection):
    """Test inserting events into the events table."""
    bucket_id = "test-event-bucket"

    # Create test bucket
    await db_connection.execute(
        """
        INSERT INTO buckets (bucket_id, name, type, client, hostname, created)
        VALUES ($1, $2, $3, $4, $5, $6)
        """,
        bucket_id,
        "Event Test Bucket",
        "test",
        "test-client",
        "test-host",
        datetime.now(timezone.utc),
    )

    # Insert event
    timestamp = datetime.now(timezone.utc)
    duration = 1000000  # 1 second in microseconds
    event_data = json.dumps({"title": "Test Event", "app": "test-app"})

    await db_connection.execute(
        """
        INSERT INTO events (bucket_id, timestamp, duration, data)
        VALUES ($1, $2, $3, $4)
        """,
        bucket_id,
        timestamp,
        duration,
        event_data,
    )

    # Verify event was inserted
    event = await db_connection.fetchrow(
        """
        SELECT * FROM events 
        WHERE bucket_id = $1 
        ORDER BY timestamp DESC 
        LIMIT 1
        """,
        bucket_id,
    )

    assert event is not None, "Event should be inserted"
    assert event["bucket_id"] == bucket_id
    assert event["duration"] == duration
    assert json.loads(event["data"])["title"] == "Test Event"

    # Cleanup
    await db_connection.execute(
        "DELETE FROM events WHERE bucket_id = $1", bucket_id
    )
    await db_connection.execute(
        "DELETE FROM buckets WHERE bucket_id = $1", bucket_id
    )


@pytest.mark.asyncio
async def test_foreign_key_constraint(db_connection: asyncpg.Connection):
    """Test that foreign key constraint works correctly."""
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
async def test_indexes_exist(db_connection: asyncpg.Connection):
    """Test that important indexes exist."""
    indexes = await db_connection.fetch(
        """
        SELECT indexname FROM pg_indexes 
        WHERE schemaname = 'public' 
        AND tablename IN ('buckets', 'events')
        """
    )
    index_names = [row["indexname"] for row in indexes]

    # Check for key indexes
    assert any("idx_buckets_bucket_id" in name for name in index_names)
    assert any("idx_events_bucket_timestamp" in name for name in index_names)
    assert any("idx_events_timestamp" in name for name in index_names)
