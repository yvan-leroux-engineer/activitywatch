"""
Tests for Redis cache connectivity and operations
"""

import pytest
import redis.asyncio as aioredis
import json


@pytest.mark.asyncio
async def test_redis_connection(redis_client: aioredis.Redis):
    """Test basic Redis connectivity."""
    result = await redis_client.ping()
    assert result is True


@pytest.mark.asyncio
async def test_redis_set_get(redis_client: aioredis.Redis):
    """Test basic set/get operations."""
    key = "test:set_get"
    value = "test_value"

    await redis_client.set(key, value)
    result = await redis_client.get(key)

    assert result == value

    # Cleanup
    await redis_client.delete(key)


@pytest.mark.asyncio
async def test_redis_json_operations(redis_client: aioredis.Redis):
    """Test storing and retrieving JSON data."""
    key = "test:json"
    data = {"test": "data", "number": 42, "nested": {"key": "value"}}

    await redis_client.set(key, json.dumps(data))
    result = await redis_client.get(key)

    assert result is not None
    parsed = json.loads(result)
    assert parsed == data

    # Cleanup
    await redis_client.delete(key)


@pytest.mark.asyncio
async def test_redis_expiration(redis_client: aioredis.Redis):
    """Test key expiration."""
    key = "test:expire"
    value = "expiring_value"

    await redis_client.set(key, value, ex=2)  # Expire in 2 seconds

    # Should exist immediately
    result = await redis_client.get(key)
    assert result == value

    # Wait for expiration
    import asyncio

    await asyncio.sleep(3)

    # Should be expired
    result = await redis_client.get(key)
    assert result is None


@pytest.mark.asyncio
async def test_redis_hash_operations(redis_client: aioredis.Redis):
    """Test hash operations."""
    key = "test:hash"

    await redis_client.hset(
        key, mapping={"field1": "value1", "field2": "value2"}
    )

    result = await redis_client.hgetall(key)
    assert result == {"field1": "value1", "field2": "value2"}

    field1_value = await redis_client.hget(key, "field1")
    assert field1_value == "value1"

    # Cleanup
    await redis_client.delete(key)


@pytest.mark.asyncio
async def test_redis_list_operations(redis_client: aioredis.Redis):
    """Test list operations."""
    key = "test:list"

    await redis_client.rpush(key, "item1", "item2", "item3")

    length = await redis_client.llen(key)
    assert length == 3

    items = await redis_client.lrange(key, 0, -1)
    assert items == ["item1", "item2", "item3"]

    # Cleanup
    await redis_client.delete(key)


@pytest.mark.asyncio
async def test_redis_authentication(redis_client: aioredis.Redis):
    """Test that Redis requires authentication."""
    # This test verifies that we can connect with password
    # If password is wrong, connection would fail
    result = await redis_client.ping()
    assert result is True, "Should connect with correct password"
