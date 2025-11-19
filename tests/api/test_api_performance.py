"""
Small, focused API performance tests - each test measures one performance aspect
"""
import pytest
import httpx
import time
from datetime import datetime, timezone


@pytest.mark.asyncio
async def test_api_response_time_consistency(api_client: httpx.AsyncClient):
    """Test API response times are consistent."""
    # Measure response times for multiple requests
    response_times = []
    
    for _ in range(10):
        start = time.time()
        response = await api_client.get("/api/0/info")
        end = time.time()
        
        assert response.status_code == 200
        response_times.append(end - start)
    
    # Response times should be reasonable (less than 1 second)
    assert all(rt < 1.0 for rt in response_times)
    
    # Response times should be relatively consistent
    avg_time = sum(response_times) / len(response_times)
    max_deviation = max(abs(rt - avg_time) for rt in response_times)
    # Max deviation should be less than average
    assert max_deviation < avg_time * 2


@pytest.mark.asyncio
async def test_api_health_check_performance(api_client: httpx.AsyncClient):
    """Test health check endpoint performance."""
    start = time.time()
    response = await api_client.get("/health")
    end = time.time()
    
    assert response.status_code == 200
    # Health check should be very fast (< 100ms)
    assert (end - start) < 0.1


@pytest.mark.asyncio
async def test_api_bucket_creation_performance(api_client: httpx.AsyncClient):
    """Test bucket creation performance."""
    bucket_id = "test-performance-bucket"
    
    start = time.time()
    response = await api_client.post(
        f"/api/0/buckets/{bucket_id}",
        json={
            "type": "test",
            "client": "test-client",
            "hostname": "test-host",
        },
    )
    end = time.time()
    
    assert response.status_code in [200, 201]
    # Bucket creation should be reasonably fast (< 500ms)
    assert (end - start) < 0.5
    
    # Cleanup
    await api_client.delete(f"/api/0/buckets/{bucket_id}")


@pytest.mark.asyncio
async def test_api_event_creation_performance(api_client: httpx.AsyncClient):
    """Test event creation performance."""
    bucket_id = "test-event-performance"
    
    await api_client.post(
        f"/api/0/buckets/{bucket_id}",
        json={
            "type": "test",
            "client": "test-client",
            "hostname": "test-host",
        },
    )
    
    start = time.time()
    response = await api_client.post(
        f"/api/0/buckets/{bucket_id}/events",
        json=[{
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "duration": 1.0,
            "data": {},
        }],
    )
    end = time.time()
    
    assert response.status_code in [200, 201]
    # Event creation should be reasonably fast (< 500ms)
    assert (end - start) < 0.5
    
    # Cleanup
    await api_client.delete(f"/api/0/buckets/{bucket_id}")


@pytest.mark.asyncio
async def test_api_batch_event_creation_performance(api_client: httpx.AsyncClient):
    """Test batch event creation performance."""
    bucket_id = "test-batch-performance"
    
    await api_client.post(
        f"/api/0/buckets/{bucket_id}",
        json={
            "type": "test",
            "client": "test-client",
            "hostname": "test-host",
        },
    )
    
    # Create 100 events in one batch
    from datetime import timedelta
    timestamp = datetime.now(timezone.utc)
    events = [
        {
            "timestamp": (timestamp + timedelta(milliseconds=i)).isoformat(),
            "duration": 1.0,
            "data": {"index": i},
        }
        for i in range(100)
    ]
    
    start = time.time()
    response = await api_client.post(
        f"/api/0/buckets/{bucket_id}/events",
        json=events,
    )
    end = time.time()
    
    assert response.status_code in [200, 201]
    # Batch creation should be efficient (< 2 seconds for 100 events)
    assert (end - start) < 2.0
    
    # Cleanup
    await api_client.delete(f"/api/0/buckets/{bucket_id}")


@pytest.mark.asyncio
async def test_api_query_performance(api_client: httpx.AsyncClient):
    """Test query endpoint performance."""
    query = {
        "timeperiods": [["2024-01-01", "2024-12-31"]],
        "query": [
            {
                "type": "bucket",
                "name": "aw-watcher-window",
            }
        ],
    }
    
    start = time.time()
    response = await api_client.post("/api/0/query", json=query)
    end = time.time()
    
    # Query should complete in reasonable time (< 2 seconds)
    assert (end - start) < 2.0
    assert response.status_code in [200, 400, 422]

