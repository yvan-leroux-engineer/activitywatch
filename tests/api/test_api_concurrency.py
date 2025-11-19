"""
Small, focused API concurrency tests - each test covers one concurrent scenario
"""
import pytest
import httpx
import asyncio
from datetime import datetime, timezone, timedelta


@pytest.mark.asyncio
async def test_api_concurrent_bucket_creation(api_client: httpx.AsyncClient):
    """Test creating multiple buckets concurrently."""
    bucket_ids = [f"test-concurrent-bucket-{i}" for i in range(5)]
    
    # Create multiple buckets concurrently
    tasks = [
        api_client.post(
            f"/api/0/buckets/{bid}",
            json={
                "type": "test",
                "client": "test-client",
                "hostname": "test-host",
            },
        )
        for bid in bucket_ids
    ]
    
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Check all succeeded
    success_count = sum(
        1 for r in responses
        if not isinstance(r, Exception) and r.status_code in [200, 201]
    )
    assert success_count == len(bucket_ids)
    
    # Cleanup
    cleanup_tasks = [
        api_client.delete(f"/api/0/buckets/{bid}")
        for bid in bucket_ids
    ]
    await asyncio.gather(*cleanup_tasks, return_exceptions=True)


@pytest.mark.asyncio
async def test_api_concurrent_event_creation_same_bucket(api_client: httpx.AsyncClient):
    """Test concurrent event creation to same bucket."""
    bucket_id = "test-concurrent-events-same-bucket"
    
    await api_client.post(
        f"/api/0/buckets/{bucket_id}",
        json={
            "type": "test",
            "client": "test-client",
            "hostname": "test-host",
        },
    )
    
    # Create events concurrently
    timestamp = datetime.now(timezone.utc)
    tasks = [
        api_client.post(
            f"/api/0/buckets/{bucket_id}/events",
            json=[{
                "timestamp": (timestamp + timedelta(milliseconds=i)).isoformat(),
                "duration": 1.0,
                "data": {"concurrent": i},
            }],
        )
        for i in range(10)
    ]
    
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    
    # All should succeed
    success_count = sum(
        1 for r in responses
        if not isinstance(r, Exception) and r.status_code in [200, 201]
    )
    assert success_count == len(tasks)
    
    # Verify all events were created
    response = await api_client.get(f"/api/0/buckets/{bucket_id}/events")
    assert response.status_code == 200
    events = response.json()
    assert len(events) >= 10
    
    # Cleanup
    await api_client.delete(f"/api/0/buckets/{bucket_id}")


@pytest.mark.asyncio
async def test_api_concurrent_read_write_operations(api_client: httpx.AsyncClient):
    """Test concurrent read and write operations."""
    bucket_id = "test-concurrent-rw"
    
    # Create bucket
    await api_client.post(
        f"/api/0/buckets/{bucket_id}",
        json={
            "type": "test",
            "client": "test-client",
            "hostname": "test-host",
        },
    )
    
    # Concurrent read and write
    async def write_events():
        timestamp = datetime.now(timezone.utc)
        for i in range(5):
            await api_client.post(
                f"/api/0/buckets/{bucket_id}/events",
                json=[{
                    "timestamp": (timestamp + timedelta(milliseconds=i)).isoformat(),
                    "duration": 1.0,
                    "data": {"write": i},
                }],
            )
            await asyncio.sleep(0.01)
    
    async def read_events():
        for _ in range(5):
            await api_client.get(f"/api/0/buckets/{bucket_id}/events")
            await asyncio.sleep(0.01)
    
    # Run concurrently
    await asyncio.gather(write_events(), read_events())
    
    # Verify final state
    response = await api_client.get(f"/api/0/buckets/{bucket_id}/events")
    events = response.json()
    assert len(events) >= 5
    
    # Cleanup
    await api_client.delete(f"/api/0/buckets/{bucket_id}")


@pytest.mark.asyncio
async def test_api_batch_event_creation(api_client: httpx.AsyncClient):
    """Test creating events in batches."""
    bucket_id = "test-batch-events"
    
    await api_client.post(
        f"/api/0/buckets/{bucket_id}",
        json={
            "type": "test",
            "client": "test-client",
            "hostname": "test-host",
        },
    )
    
    # Create events in batches
    timestamp = datetime.now(timezone.utc)
    batch_size = 20
    num_batches = 3
    
    for batch in range(num_batches):
        events = [
            {
                "timestamp": (
                    timestamp + timedelta(seconds=batch * batch_size + i)
                ).isoformat(),
                "duration": 1.0,
                "data": {"batch": batch, "index": i},
            }
            for i in range(batch_size)
        ]
        
        response = await api_client.post(
            f"/api/0/buckets/{bucket_id}/events",
            json=events,
        )
        assert response.status_code in [200, 201]
    
    # Verify all events were created
    response = await api_client.get(f"/api/0/buckets/{bucket_id}/events")
    events = response.json()
    assert len(events) == batch_size * num_batches
    
    # Cleanup
    await api_client.delete(f"/api/0/buckets/{bucket_id}")


@pytest.mark.asyncio
async def test_api_concurrent_bucket_operations(api_client: httpx.AsyncClient):
    """Test concurrent operations on multiple buckets."""
    bucket_ids = [f"test-concurrent-op-{i}" for i in range(5)]
    
    # Create buckets concurrently
    create_tasks = [
        api_client.post(
            f"/api/0/buckets/{bid}",
            json={
                "type": "test",
                "client": "test-client",
                "hostname": "test-host",
            },
        )
        for bid in bucket_ids
    ]
    
    create_responses = await asyncio.gather(*create_tasks, return_exceptions=True)
    assert all(
        not isinstance(r, Exception) and r.status_code in [200, 201]
        for r in create_responses
    )
    
    # Create events in all buckets concurrently
    event_tasks = []
    for bid in bucket_ids:
        event_tasks.append(
            api_client.post(
                f"/api/0/buckets/{bid}/events",
                json=[{
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "duration": 1.0,
                    "data": {"bucket": bid},
                }],
            )
        )
    
    event_responses = await asyncio.gather(*event_tasks, return_exceptions=True)
    assert all(
        not isinstance(r, Exception) and r.status_code in [200, 201]
        for r in event_responses
    )
    
    # Read from all buckets concurrently
    read_tasks = [
        api_client.get(f"/api/0/buckets/{bid}/events")
        for bid in bucket_ids
    ]
    
    read_responses = await asyncio.gather(*read_tasks, return_exceptions=True)
    assert all(
        not isinstance(r, Exception) and r.status_code == 200
        for r in read_responses
    )
    
    # Cleanup
    delete_tasks = [
        api_client.delete(f"/api/0/buckets/{bid}")
        for bid in bucket_ids
    ]
    await asyncio.gather(*delete_tasks, return_exceptions=True)


@pytest.mark.asyncio
async def test_api_data_integrity_under_concurrent_load(api_client: httpx.AsyncClient):
    """Test data integrity under concurrent load."""
    bucket_id = "test-load-integrity"
    
    # Create bucket
    await api_client.post(
        f"/api/0/buckets/{bucket_id}",
        json={
            "type": "test",
            "client": "test-client",
            "hostname": "test-host",
        },
    )
    
    # Create many events concurrently
    async def create_event_batch(start_index, count):
        timestamp = datetime.now(timezone.utc)
        events = [
            {
                "timestamp": (timestamp + timedelta(milliseconds=start_index + i)).isoformat(),
                "duration": 1.0,
                "data": {"batch": start_index // 10, "index": i},
            }
            for i in range(count)
        ]
        return await api_client.post(
            f"/api/0/buckets/{bucket_id}/events",
            json=events,
        )
    
    # Create 5 batches of 10 events each concurrently
    tasks = [
        create_event_batch(i * 10, 10)
        for i in range(5)
    ]
    
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    assert all(
        not isinstance(r, Exception) and r.status_code in [200, 201]
        for r in responses
    )
    
    # Verify all events were created
    response = await api_client.get(f"/api/0/buckets/{bucket_id}/events")
    events = response.json()
    assert len(events) == 50
    
    # Verify no duplicates (check unique timestamps)
    timestamps = [e.get("timestamp") for e in events]
    assert len(timestamps) == len(set(timestamps))
    
    # Cleanup
    await api_client.delete(f"/api/0/buckets/{bucket_id}")

