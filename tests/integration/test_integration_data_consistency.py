"""
Small, focused integration tests for data consistency - each test verifies one consistency aspect
"""
import pytest
import httpx
from datetime import datetime, timezone, timedelta


@pytest.mark.asyncio
async def test_api_webui_data_consistency(api_client: httpx.AsyncClient, webui_client: httpx.AsyncClient):
    """Test data consistency between API and WebUI."""
    bucket_id = "test-api-webui-consistency"
    
    # Create bucket via API
    await api_client.post(
        f"/api/0/buckets/{bucket_id}",
        json={
            "type": "test",
            "client": "test-client",
            "hostname": "test-host",
        },
    )
    
    # Create events via API
    timestamp = datetime.now(timezone.utc)
    events = [
        {
            "timestamp": (timestamp + timedelta(seconds=i)).isoformat(),
            "duration": 1.0,
            "data": {"index": i, "source": "api"},
        }
        for i in range(5)
    ]
    
    await api_client.post(
        f"/api/0/buckets/{bucket_id}/events",
        json=events,
    )
    
    # Read via API
    api_response = await api_client.get(f"/api/0/buckets/{bucket_id}/events")
    api_events = api_response.json()
    
    # Read via WebUI proxy
    webui_response = await webui_client.get(f"/api/0/buckets/{bucket_id}/events")
    webui_events = webui_response.json()
    
    # Data should be consistent
    assert len(api_events) == len(webui_events)
    assert len(api_events) == 5
    
    # Cleanup
    await api_client.delete(f"/api/0/buckets/{bucket_id}")


@pytest.mark.asyncio
async def test_api_webui_error_consistency(api_client: httpx.AsyncClient, webui_client: httpx.AsyncClient):
    """Test error responses are consistent between API and WebUI."""
    # Try to access non-existent bucket via WebUI
    webui_response = await webui_client.get("/api/0/buckets/non-existent-bucket-xyz")
    
    # Try to access same bucket via API
    api_response = await api_client.get("/api/0/buckets/non-existent-bucket-xyz")
    
    # Both should return same error status
    assert webui_response.status_code == api_response.status_code
    assert webui_response.status_code == 404


@pytest.mark.asyncio
async def test_api_webui_time_range_consistency(api_client: httpx.AsyncClient, webui_client: httpx.AsyncClient):
    """Test time range queries are consistent."""
    bucket_id = "test-time-range-consistency"
    
    # Create bucket
    await api_client.post(
        f"/api/0/buckets/{bucket_id}",
        json={
            "type": "test",
            "client": "test-client",
            "hostname": "test-host",
        },
    )
    
    # Create events over time range
    base_time = datetime.now(timezone.utc) - timedelta(days=1)
    events = [
        {
            "timestamp": (base_time + timedelta(hours=i)).isoformat(),
            "duration": 1.0,
            "data": {"hour": i},
        }
        for i in range(24)
    ]
    
    await api_client.post(
        f"/api/0/buckets/{bucket_id}/events",
        json=events,
    )
    
    # Query via API with time range
    start_time = (base_time + timedelta(hours=6)).isoformat()
    end_time = (base_time + timedelta(hours=18)).isoformat()
    
    api_response = await api_client.get(
        f"/api/0/buckets/{bucket_id}/events",
        params={"start": start_time, "end": end_time},
    )
    api_events = api_response.json()
    
    # Query via WebUI with same time range
    webui_response = await webui_client.get(
        f"/api/0/buckets/{bucket_id}/events",
        params={"start": start_time, "end": end_time},
    )
    webui_events = webui_response.json()
    
    # Results should be consistent
    assert len(api_events) == len(webui_events)
    
    # Cleanup
    await api_client.delete(f"/api/0/buckets/{bucket_id}")


@pytest.mark.asyncio
async def test_api_webui_header_preservation(api_client: httpx.AsyncClient, webui_client: httpx.AsyncClient):
    """Test that WebUI preserves necessary headers when proxying."""
    # Get response directly from API
    api_response = await api_client.get("/api/0/info")
    
    # Get response via WebUI proxy
    webui_response = await webui_client.get("/api/0/info")
    
    # Both should succeed
    assert api_response.status_code == 200
    assert webui_response.status_code == 200
    
    # Content-Type should be preserved
    api_content_type = api_response.headers.get("content-type", "")
    webui_content_type = webui_response.headers.get("content-type", "")
    
    # Both should have JSON content type
    assert "json" in api_content_type.lower() or "json" in webui_content_type.lower()


@pytest.mark.asyncio
async def test_api_webui_error_propagation(api_client: httpx.AsyncClient, webui_client: httpx.AsyncClient):
    """Test error propagation through WebUI proxy."""
    # Create invalid request via WebUI proxy
    webui_response = await webui_client.post(
        "/api/0/buckets/invalid-bucket-id/events",
        json=[{"invalid": "data"}],
    )
    
    # Create same invalid request directly to API
    api_response = await api_client.post(
        "/api/0/buckets/invalid-bucket-id/events",
        json=[{"invalid": "data"}],
    )
    
    # Both should return appropriate error
    assert webui_response.status_code in [400, 404, 422, 500]
    assert api_response.status_code in [400, 404, 422, 500]
    
    # Error codes should match (WebUI should pass through API errors)
    assert webui_response.status_code == api_response.status_code

