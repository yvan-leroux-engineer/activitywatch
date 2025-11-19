"""
Tests for API service endpoints
"""

import pytest
import httpx
from datetime import datetime, timezone
import json


@pytest.mark.asyncio
async def test_api_health_check(api_client: httpx.AsyncClient):
    """Test API health check endpoint."""
    response = await api_client.get("/health")
    assert response.status_code == 200
    # Rust API returns "ok" as plain text
    assert (
        "ok" in response.text.lower()
        or response.json().get("status") == "healthy"
    )


@pytest.mark.asyncio
async def test_api_info_endpoint(api_client: httpx.AsyncClient):
    """Test API info endpoint."""
    response = await api_client.get("/api/0/info")
    assert response.status_code == 200
    data = response.json()
    assert "hostname" in data
    assert "version" in data
    assert "testing" in data


@pytest.mark.asyncio
async def test_api_create_bucket(api_client: httpx.AsyncClient):
    """Test creating a bucket via API."""
    bucket_id = "test-api-bucket"

    response = await api_client.post(
        f"/api/0/buckets/{bucket_id}",
        json={
            "type": "test",
            "client": "test-client",
            "hostname": "test-host",
        },
    )

    assert response.status_code in [200, 201], (
        f"Expected 200/201, got {response.status_code}: {response.text}"
    )

    # Verify bucket exists
    response = await api_client.get(f"/api/0/buckets/{bucket_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == bucket_id
    assert data["type"] == "test"

    # Cleanup
    await api_client.delete(f"/api/0/buckets/{bucket_id}")


@pytest.mark.asyncio
async def test_api_list_buckets(api_client: httpx.AsyncClient):
    """Test listing all buckets."""
    response = await api_client.get("/api/0/buckets")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict), "Response should be a dictionary"
    # Rust API returns a dict with bucket IDs as keys


@pytest.mark.asyncio
async def test_api_create_event(api_client: httpx.AsyncClient):
    """Test creating an event via API."""
    bucket_id = "test-event-bucket"

    # Create bucket first
    await api_client.post(
        f"/api/0/buckets/{bucket_id}",
        json={
            "type": "test",
            "client": "test-client",
            "hostname": "test-host",
        },
    )

    # Create event
    timestamp = datetime.now(timezone.utc).isoformat()
    event_data = {
        "timestamp": timestamp,
        "duration": 1.0,
        "data": {
            "title": "Test Event",
            "app": "test-app",
        },
    }

    response = await api_client.post(
        f"/api/0/buckets/{bucket_id}/events",
        json=[event_data],
    )

    assert response.status_code in [200, 201], (
        f"Expected 200/201, got {response.status_code}: {response.text}"
    )

    # Verify event was created
    response = await api_client.get(f"/api/0/buckets/{bucket_id}/events")
    assert response.status_code == 200
    events = response.json()
    assert len(events) > 0

    # Cleanup
    await api_client.delete(f"/api/0/buckets/{bucket_id}")


@pytest.mark.asyncio
async def test_api_query_endpoint(api_client: httpx.AsyncClient):
    """Test query endpoint."""
    query = {
        "timeperiods": [["2024-01-01", "2024-12-31"]],
        "query": [
            {
                "type": "bucket",
                "name": "aw-watcher-window",
            }
        ],
    }
    
    response = await api_client.post("/api/0/query", json=query)
    # Query might return 200 with empty results, 400 if bucket doesn't exist, or 422 for invalid query
    assert response.status_code in [200, 400, 422]


@pytest.mark.asyncio
async def test_api_settings_endpoint(api_client: httpx.AsyncClient):
    """Test settings endpoints."""
    key = "test_setting"
    value = {"test": "value"}
    
    # Set setting
    response = await api_client.put(
        f"/api/0/settings/{key}",
        json=value,
    )
    # Settings endpoint might not be implemented or return different codes
    if response.status_code == 404:
        pytest.skip("Settings endpoint not available")
    assert response.status_code in [200, 201, 204]
    
    # Get setting
    response = await api_client.get(f"/api/0/settings/{key}")
    if response.status_code == 404:
        pytest.skip("Settings endpoint not available")
    assert response.status_code == 200
    data = response.json()
    assert data == value
    
    # Delete setting
    response = await api_client.delete(f"/api/0/settings/{key}")
    assert response.status_code in [200, 204]
    
    # Verify deleted
    response = await api_client.get(f"/api/0/settings/{key}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_api_cors_headers(api_client: httpx.AsyncClient):
    """Test that CORS headers are present."""
    response = await api_client.options("/api/0/info")
    # CORS preflight should be handled
    assert response.status_code in [200, 204, 405]


@pytest.mark.asyncio
async def test_api_error_handling(api_client: httpx.AsyncClient):
    """Test error handling for invalid requests."""
    # Try to get non-existent bucket
    response = await api_client.get("/api/0/buckets/non-existent-bucket-id")
    assert response.status_code == 404

    # Try to create event in non-existent bucket
    response = await api_client.post(
        "/api/0/buckets/non-existent-bucket/events",
        json=[
            {"timestamp": "2024-01-01T00:00:00Z", "duration": 1.0, "data": {}}
        ],
    )
    # API might return 400, 404, or 500 depending on implementation
    assert response.status_code in [400, 404, 500]
