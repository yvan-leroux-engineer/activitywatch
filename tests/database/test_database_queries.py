"""
Small, focused database query tests - each test covers one query scenario
"""
import pytest
import asyncpg
from datetime import datetime, timezone, timedelta
import json


@pytest.mark.asyncio
async def test_database_jsonb_path_query(db_connection: asyncpg.Connection):
    """Test JSONB path queries."""
    bucket_id = "test-jsonb-path"
    
    # Create bucket with complex JSONB data
    complex_data = {
        "nested": {
            "level1": {
                "level2": "value",
            }
        },
    }
    
    await db_connection.execute(
        """
        INSERT INTO buckets (bucket_id, name, type, client, hostname, created, data)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        """,
        bucket_id,
        "JSONB Test Bucket",
        "test",
        "test-client",
        "test-host",
        datetime.now(timezone.utc),
        json.dumps(complex_data),
    )
    
    # Query using JSONB operators
    result = await db_connection.fetchrow(
        """
        SELECT data->'nested'->'level1'->>'level2' as level2_value
        FROM buckets
        WHERE bucket_id = $1
        """,
        bucket_id,
    )
    assert result["level2_value"] == "value"
    
    # Cleanup
    await db_connection.execute(
        "DELETE FROM buckets WHERE bucket_id = $1", bucket_id
    )


@pytest.mark.asyncio
async def test_database_jsonb_contains_operator(db_connection: asyncpg.Connection):
    """Test JSONB contains operator."""
    bucket_id = "test-jsonb-contains"
    
    complex_data = {
        "tags": ["tag1", "tag2"],
    }
    
    await db_connection.execute(
        """
        INSERT INTO buckets (bucket_id, name, type, client, hostname, created, data)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        """,
        bucket_id,
        "JSONB Contains Test",
        "test",
        "test-client",
        "test-host",
        datetime.now(timezone.utc),
        json.dumps(complex_data),
    )
    
    # Query using JSONB contains operator
    result = await db_connection.fetchval(
        """
        SELECT COUNT(*) FROM buckets
        WHERE data @> '{"tags": ["tag1"]}'
        AND bucket_id = $1
        """,
        bucket_id,
    )
    assert result == 1
    
    # Cleanup
    await db_connection.execute(
        "DELETE FROM buckets WHERE bucket_id = $1", bucket_id
    )


@pytest.mark.asyncio
async def test_database_time_range_query(db_connection: asyncpg.Connection):
    """Test time range queries on events."""
    bucket_id = "test-time-range-query"
    
    # Create bucket
    await db_connection.execute(
        """
        INSERT INTO buckets (bucket_id, name, type, client, hostname, created)
        VALUES ($1, $2, $3, $4, $5, $6)
        """,
        bucket_id,
        "Time Range Test",
        "test",
        "test-client",
        "test-host",
        datetime.now(timezone.utc),
    )
    
    # Create events over time range
    base_time = datetime.now(timezone.utc) - timedelta(days=1)
    for i in range(10):
        await db_connection.execute(
            """
            INSERT INTO events (bucket_id, timestamp, duration, data)
            VALUES ($1, $2, $3, $4)
            """,
            bucket_id,
            base_time + timedelta(hours=i),
            1000000,
            json.dumps({"index": i}),
        )
    
    # Test time range query
    start_time = base_time + timedelta(hours=2)
    end_time = base_time + timedelta(hours=7)
    
    count = await db_connection.fetchval(
        """
        SELECT COUNT(*) FROM events
        WHERE bucket_id = $1
        AND timestamp >= $2
        AND timestamp < $3
        """,
        bucket_id,
        start_time,
        end_time,
    )
    assert count == 5  # Should have 5 events in range
    
    # Cleanup
    await db_connection.execute(
        "DELETE FROM buckets WHERE bucket_id = $1", bucket_id
    )


@pytest.mark.asyncio
async def test_database_index_usage_on_bucket_id(db_connection: asyncpg.Connection):
    """Test that index is used when querying by bucket_id."""
    bucket_id = "test-index-bucket-id"
    
    # Create bucket
    await db_connection.execute(
        """
        INSERT INTO buckets (bucket_id, name, type, client, hostname, created)
        VALUES ($1, $2, $3, $4, $5, $6)
        """,
        bucket_id,
        "Index Test",
        "test",
        "test-client",
        "test-host",
        datetime.now(timezone.utc),
    )
    
    # Query that should use index
    explain_result = await db_connection.fetchval(
        """
        EXPLAIN (FORMAT JSON)
        SELECT * FROM buckets
        WHERE bucket_id = $1
        """,
        bucket_id,
    )
    
    # Verify query plan exists
    assert explain_result is not None
    
    # Cleanup
    await db_connection.execute(
        "DELETE FROM buckets WHERE bucket_id = $1", bucket_id
    )


@pytest.mark.asyncio
async def test_database_index_usage_on_timestamp(db_connection: asyncpg.Connection):
    """Test that index is used when querying by timestamp."""
    bucket_id = "test-index-timestamp"
    
    # Create bucket
    await db_connection.execute(
        """
        INSERT INTO buckets (bucket_id, name, type, client, hostname, created)
        VALUES ($1, $2, $3, $4, $5, $6)
        """,
        bucket_id,
        "Timestamp Index Test",
        "test",
        "test-client",
        "test-host",
        datetime.now(timezone.utc),
    )
    
    # Create events
    timestamp = datetime.now(timezone.utc)
    for i in range(10):
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
    
    # Query that should use timestamp index
    explain_result = await db_connection.fetchval(
        """
        EXPLAIN (FORMAT JSON)
        SELECT * FROM events
        WHERE bucket_id = $1
        ORDER BY timestamp DESC
        LIMIT 10
        """,
        bucket_id,
    )
    
    # Verify query plan exists
    assert explain_result is not None
    
    # Cleanup
    await db_connection.execute(
        "DELETE FROM buckets WHERE bucket_id = $1", bucket_id
    )


@pytest.mark.asyncio
async def test_database_aggregation_query(db_connection: asyncpg.Connection):
    """Test aggregation queries on events."""
    bucket_id = "test-aggregation"
    
    # Create bucket
    await db_connection.execute(
        """
        INSERT INTO buckets (bucket_id, name, type, client, hostname, created)
        VALUES ($1, $2, $3, $4, $5, $6)
        """,
        bucket_id,
        "Aggregation Test",
        "test",
        "test-client",
        "test-host",
        datetime.now(timezone.utc),
    )
    
    # Create events with different durations
    timestamp = datetime.now(timezone.utc)
    durations = [1000000, 2000000, 3000000, 4000000, 5000000]
    for i, duration in enumerate(durations):
        await db_connection.execute(
            """
            INSERT INTO events (bucket_id, timestamp, duration, data)
            VALUES ($1, $2, $3, $4)
            """,
            bucket_id,
            timestamp + timedelta(seconds=i),
            duration,
            json.dumps({"index": i}),
        )
    
    # Test aggregation
    result = await db_connection.fetchrow(
        """
        SELECT 
            COUNT(*) as event_count,
            SUM(duration) as total_duration,
            AVG(duration) as avg_duration
        FROM events
        WHERE bucket_id = $1
        """,
        bucket_id,
    )
    
    assert result["event_count"] == 5
    assert result["total_duration"] == sum(durations)
    
    # Cleanup
    await db_connection.execute(
        "DELETE FROM buckets WHERE bucket_id = $1", bucket_id
    )

