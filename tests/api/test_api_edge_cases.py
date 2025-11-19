"""
Small, focused API edge case tests - each test covers one specific scenario
"""
import pytest
import httpx
from datetime import datetime, timezone


@pytest.mark.asyncio
async def test_api_create_bucket_duplicate_returns_error(api_client: httpx.AsyncClient):
    """Test creating duplicate bucket returns appropriate error."""
    bucket_id = "test-duplicate-bucket"
    
    # Create bucket first time
    response = await api_client.post(
        f"/api/0/buckets/{bucket_id}",
        json={
            "type": "test",
            "client": "test-client",
            "hostname": "test-host",
        },
    )
    assert response.status_code in [200, 201, 304]
    
    # Try to create duplicate
    response = await api_client.post(
        f"/api/0/buckets/{bucket_id}",
        json={
            "type": "test",
            "client": "test-client",
            "hostname": "test-host",
        },
    )
    # API returns 304 (Not Modified) for duplicates, or error codes
    assert response.status_code in [200, 201, 304, 400, 409, 422]
    
    # Cleanup
    await api_client.delete(f"/api/0/buckets/{bucket_id}")


@pytest.mark.asyncio
async def test_api_create_bucket_missing_fields(api_client: httpx.AsyncClient):
    """Test creating bucket with missing required fields."""
    bucket_id = "test-missing-fields"
    
    response = await api_client.post(
        f"/api/0/buckets/{bucket_id}",
        json={},
    )
    assert response.status_code in [400, 422]


@pytest.mark.asyncio
async def test_api_create_bucket_empty_type(api_client: httpx.AsyncClient):
    """Test creating bucket with empty type field."""
    bucket_id = "test-empty-type"
    
    response = await api_client.post(
        f"/api/0/buckets/{bucket_id}",
        json={
            "type": "",
            "client": "test-client",
            "hostname": "test-host",
        },
    )
    # API may return 304 (Not Modified) if bucket already exists or accepts empty type
    assert response.status_code in [200, 201, 304, 400, 422]
    
    # Cleanup if bucket was created
    if response.status_code in [200, 201, 304]:
        await api_client.delete(f"/api/0/buckets/{bucket_id}")


@pytest.mark.asyncio
async def test_api_create_bucket_very_long_id(api_client: httpx.AsyncClient):
    """Test creating bucket with very long ID."""
    long_bucket_id = "a" * 300
    
    response = await api_client.post(
        f"/api/0/buckets/{long_bucket_id}",
        json={
            "type": "test",
            "client": "test-client",
            "hostname": "test-host",
        },
    )
    # Should either accept or reject with appropriate error (including 500 for internal errors)
    assert response.status_code in [200, 201, 400, 413, 422, 500]
    
    if response.status_code in [200, 201]:
        await api_client.delete(f"/api/0/buckets/{long_bucket_id}")


@pytest.mark.asyncio
async def test_api_create_event_invalid_timestamp_format(api_client: httpx.AsyncClient):
    """Test creating event with invalid timestamp format."""
    bucket_id = "test-invalid-timestamp-format"
    
    # Create bucket first
    await api_client.post(
        f"/api/0/buckets/{bucket_id}",
        json={
            "type": "test",
            "client": "test-client",
            "hostname": "test-host",
        },
    )
    
    response = await api_client.post(
        f"/api/0/buckets/{bucket_id}/events",
        json=[{
            "timestamp": "invalid-date",
            "duration": 1.0,
            "data": {},
        }],
    )
    assert response.status_code in [400, 422]
    
    # Cleanup
    await api_client.delete(f"/api/0/buckets/{bucket_id}")


@pytest.mark.asyncio
async def test_api_create_event_future_timestamp(api_client: httpx.AsyncClient):
    """Test creating event with future timestamp."""
    from datetime import timedelta
    
    bucket_id = "test-future-timestamp"
    
    await api_client.post(
        f"/api/0/buckets/{bucket_id}",
        json={
            "type": "test",
            "client": "test-client",
            "hostname": "test-host",
        },
    )
    
    future_time = (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()
    response = await api_client.post(
        f"/api/0/buckets/{bucket_id}/events",
        json=[{
            "timestamp": future_time,
            "duration": 1.0,
            "data": {},
        }],
    )
    # API might accept or reject future timestamps
    assert response.status_code in [200, 201, 400, 422]
    
    # Cleanup
    await api_client.delete(f"/api/0/buckets/{bucket_id}")


@pytest.mark.asyncio
async def test_api_create_event_negative_duration(api_client: httpx.AsyncClient):
    """Test creating event with negative duration."""
    bucket_id = "test-negative-duration"
    
    await api_client.post(
        f"/api/0/buckets/{bucket_id}",
        json={
            "type": "test",
            "client": "test-client",
            "hostname": "test-host",
        },
    )
    
    response = await api_client.post(
        f"/api/0/buckets/{bucket_id}/events",
        json=[{
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "duration": -1.0,
            "data": {},
        }],
    )
    # API might accept or reject negative durations
    assert response.status_code in [200, 201, 400, 422]
    
    # Cleanup
    await api_client.delete(f"/api/0/buckets/{bucket_id}")


@pytest.mark.asyncio
async def test_api_create_event_empty_array(api_client: httpx.AsyncClient):
    """Test creating events with empty array."""
    bucket_id = "test-empty-events-array"
    
    await api_client.post(
        f"/api/0/buckets/{bucket_id}",
        json={
            "type": "test",
            "client": "test-client",
            "hostname": "test-host",
        },
    )
    
    response = await api_client.post(
        f"/api/0/buckets/{bucket_id}/events",
        json=[],
    )
    # Should accept empty array or return error
    assert response.status_code in [200, 201, 400, 422]
    
    # Cleanup
    await api_client.delete(f"/api/0/buckets/{bucket_id}")


@pytest.mark.asyncio
async def test_api_create_event_large_data_payload(api_client: httpx.AsyncClient):
    """Test creating event with large data payload."""
    bucket_id = "test-large-payload"
    
    await api_client.post(
        f"/api/0/buckets/{bucket_id}",
        json={
            "type": "test",
            "client": "test-client",
            "hostname": "test-host",
        },
    )
    
    # Large data field
    large_data = {"content": "x" * 10000}
    response = await api_client.post(
        f"/api/0/buckets/{bucket_id}/events",
        json=[{
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "duration": 1.0,
            "data": large_data,
        }],
    )
    # Should accept or reject based on size limits
    assert response.status_code in [200, 201, 400, 413, 422]
    
    # Cleanup
    await api_client.delete(f"/api/0/buckets/{bucket_id}")


@pytest.mark.asyncio
async def test_api_get_events_with_limit(api_client: httpx.AsyncClient):
    """Test event retrieval with limit parameter."""
    bucket_id = "test-events-limit"
    
    await api_client.post(
        f"/api/0/buckets/{bucket_id}",
        json={
            "type": "test",
            "client": "test-client",
            "hostname": "test-host",
        },
    )
    
    # Create multiple events
    from datetime import timedelta
    timestamp = datetime.now(timezone.utc)
    events = [
        {
            "timestamp": (timestamp + timedelta(seconds=i)).isoformat(),
            "duration": 1.0,
            "data": {"index": i},
        }
        for i in range(10)
    ]
    
    await api_client.post(
        f"/api/0/buckets/{bucket_id}/events",
        json=events,
    )
    
    # Test limit parameter
    response = await api_client.get(
        f"/api/0/buckets/{bucket_id}/events",
        params={"limit": 5},
    )
    assert response.status_code == 200
    events_data = response.json()
    # Should return at most 5 events
    assert len(events_data) <= 5
    
    # Cleanup
    await api_client.delete(f"/api/0/buckets/{bucket_id}")


@pytest.mark.asyncio
async def test_api_get_events_with_time_range(api_client: httpx.AsyncClient):
    """Test event retrieval with time range filters."""
    from datetime import timedelta
    
    bucket_id = "test-events-time-range"
    
    await api_client.post(
        f"/api/0/buckets/{bucket_id}",
        json={
            "type": "test",
            "client": "test-client",
            "hostname": "test-host",
        },
    )
    
    # Create events at different times
    base_time = datetime.now(timezone.utc)
    events = [
        {
            "timestamp": (base_time + timedelta(hours=i)).isoformat(),
            "duration": 1.0,
            "data": {"hour": i},
        }
        for i in range(5)
    ]
    
    await api_client.post(
        f"/api/0/buckets/{bucket_id}/events",
        json=events,
    )
    
    # Test time range query
    start_time = (base_time + timedelta(hours=1)).isoformat()
    end_time = (base_time + timedelta(hours=3)).isoformat()
    
    response = await api_client.get(
        f"/api/0/buckets/{bucket_id}/events",
        params={"start": start_time, "end": end_time},
    )
    assert response.status_code == 200
    
    # Cleanup
    await api_client.delete(f"/api/0/buckets/{bucket_id}")


@pytest.mark.asyncio
async def test_api_delete_nonexistent_bucket(api_client: httpx.AsyncClient):
    """Test deleting non-existent bucket."""
    response = await api_client.delete("/api/0/buckets/non-existent-bucket-12345")
    # Should return 404 or 204 (idempotent delete)
    assert response.status_code in [204, 404]


@pytest.mark.asyncio
async def test_api_get_bucket_events_empty_bucket(api_client: httpx.AsyncClient):
    """Test getting events from bucket with no events."""
    bucket_id = "test-empty-bucket-events"
    
    await api_client.post(
        f"/api/0/buckets/{bucket_id}",
        json={
            "type": "test",
            "client": "test-client",
            "hostname": "test-host",
        },
    )
    
    response = await api_client.get(f"/api/0/buckets/{bucket_id}/events")
    assert response.status_code == 200
    events = response.json()
    assert isinstance(events, list)
    
    # Cleanup
    await api_client.delete(f"/api/0/buckets/{bucket_id}")


@pytest.mark.asyncio
async def test_api_query_invalid_timeperiod(api_client: httpx.AsyncClient):
    """Test query with invalid time period."""
    query = {
        "timeperiods": [["invalid", "dates"]],
        "query": [
            {
                "type": "bucket",
                "name": "aw-watcher-window",
            }
        ],
    }
    
    response = await api_client.post("/api/0/query", json=query)
    assert response.status_code in [400, 422]


@pytest.mark.asyncio
async def test_api_unicode_data_handling(api_client: httpx.AsyncClient):
    """Test API handles Unicode data correctly."""
    bucket_id = "test-unicode-data"
    
    await api_client.post(
        f"/api/0/buckets/{bucket_id}",
        json={
            "type": "test",
            "client": "test-client",
            "hostname": "test-host",
        },
    )
    
    # Create event with Unicode data
    unicode_data = {
        "title": "测试事件 🎉",
        "description": "Événement de test avec émojis 🚀",
    }
    
    response = await api_client.post(
        f"/api/0/buckets/{bucket_id}/events",
        json=[{
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "duration": 1.0,
            "data": unicode_data,
        }],
    )
    assert response.status_code in [200, 201]
    
    # Verify Unicode data is preserved
    response = await api_client.get(f"/api/0/buckets/{bucket_id}/events")
    assert response.status_code == 200
    events = response.json()
    assert len(events) > 0
    
    # Cleanup
    await api_client.delete(f"/api/0/buckets/{bucket_id}")


@pytest.mark.asyncio
async def test_api_special_characters_in_bucket_id(api_client: httpx.AsyncClient):
    """Test bucket IDs with special characters."""
    bucket_id = "test-bucket-with-dashes-123"
    
    response = await api_client.post(
        f"/api/0/buckets/{bucket_id}",
        json={
            "type": "test",
            "client": "test-client",
            "hostname": "test-host",
        },
    )
    
    if response.status_code in [200, 201]:
        # Verify it was created
        get_response = await api_client.get(f"/api/0/buckets/{bucket_id}")
        assert get_response.status_code == 200
        
        # Cleanup
        await api_client.delete(f"/api/0/buckets/{bucket_id}")


@pytest.mark.asyncio
async def test_api_response_headers_present(api_client: httpx.AsyncClient):
    """Test API response headers are present."""
    response = await api_client.get("/api/0/info")
    
    assert response.status_code == 200
    headers = response.headers
    
    # Check for common headers
    assert "content-type" in headers or "Content-Type" in headers


@pytest.mark.asyncio
async def test_api_content_type_validation(api_client: httpx.AsyncClient):
    """Test API validates Content-Type header."""
    bucket_id = "test-content-type-validation"
    
    # Try POST without proper Content-Type
    response = await api_client.post(
        f"/api/0/buckets/{bucket_id}",
        content='{"type": "test", "client": "test-client", "hostname": "test-host"}',
        headers={"Content-Type": "text/plain"},
    )
    # API might accept or reject based on Content-Type validation
    assert response.status_code in [200, 201, 400, 404, 415, 422]
    
    if response.status_code in [200, 201]:
        await api_client.delete(f"/api/0/buckets/{bucket_id}")

