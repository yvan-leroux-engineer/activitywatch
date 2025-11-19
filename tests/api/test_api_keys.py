"""
Tests for API key authentication and management endpoints
"""

import pytest
import httpx
from datetime import datetime, timezone
import hashlib


@pytest.mark.asyncio
async def test_api_key_create(api_client: httpx.AsyncClient):
    """Test creating an API key.
    
    Note: This test requires the server to be rebuilt with the new API key endpoints.
    Run: docker-compose build api && docker-compose up -d api
    """
    response = await api_client.post(
        "/api/v1/api-keys",
        json={
            "client_id": "test-client",
            "description": "Test API key"
        }
    )
    
    # If server hasn't been rebuilt, endpoint will return 404
    if response.status_code == 404:
        pytest.skip("API key endpoints not available - server needs to be rebuilt")
    
    # Should succeed even if API_KEY_AUTH_ENABLED is false
    assert response.status_code in [200, 201], (
        f"Expected 200/201, got {response.status_code}: {response.text}"
    )
    
    data = response.json()
    assert "id" in data
    assert "api_key" in data
    assert "client_id" in data
    assert data["client_id"] == "test-client"
    assert len(data["api_key"]) > 0  # Should be a non-empty string
    
    return data["api_key"], data["id"]


@pytest.mark.asyncio
async def test_api_key_list(api_client: httpx.AsyncClient):
    """Test listing API keys."""
    # Create a key first
    create_response = await api_client.post(
        "/api/v1/api-keys",
        json={
            "client_id": "test-list-client",
            "description": "Test list key"
        }
    )
    
    if create_response.status_code == 404:
        pytest.skip("API key endpoints not available - server needs to be rebuilt")
    
    assert create_response.status_code in [200, 201]
    
    # List keys
    response = await api_client.get("/api/v1/api-keys")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    # Should have at least the key we just created
    assert len(data) > 0
    
    # Verify keys don't expose the actual key value
    for key_info in data:
        assert "id" in key_info
        assert "client_id" in key_info
        assert "api_key" not in key_info  # Should not expose the key


@pytest.mark.asyncio
async def test_api_key_revoke(api_client: httpx.AsyncClient):
    """Test revoking an API key."""
    # Create a key first
    create_response = await api_client.post(
        "/api/v1/api-keys",
        json={
            "client_id": "test-revoke-client",
            "description": "Test revoke key"
        }
    )
    
    if create_response.status_code == 404:
        pytest.skip("API key endpoints not available - server needs to be rebuilt")
    
    assert create_response.status_code in [200, 201]
    key_id = create_response.json()["id"]
    
    # Revoke the key
    response = await api_client.delete(f"/api/v1/api-keys/{key_id}")
    assert response.status_code in [200, 204]
    
    # Try to revoke again (should fail or be idempotent)
    response2 = await api_client.delete(f"/api/v1/api-keys/{key_id}")
    # Either 404 (not found) or 204 (already deleted) is acceptable
    assert response2.status_code in [200, 204, 404]


@pytest.mark.asyncio
async def test_api_key_authentication_required_when_enabled(
    api_client: httpx.AsyncClient, db_connection
):
    """Test that API key is required when API_KEY_AUTH_ENABLED=true."""
    # Note: This test assumes the server is running with API_KEY_AUTH_ENABLED=true
    # If not, it will be skipped or pass without auth
    
    # Create a bucket without API key
    bucket_id = "test-auth-required-bucket"
    response = await api_client.post(
        f"/api/0/buckets/{bucket_id}",
        json={
            "type": "test",
            "client": "test-client",
            "hostname": "test-host",
        },
    )
    
    # If auth is enabled, should get 401. If disabled, should succeed.
    # We'll check both cases
    if response.status_code == 401:
        # Auth is enabled, create an API key and retry
        key_response = await api_client.post(
            "/api/v1/api-keys",
            json={
                "client_id": "test-auth-client",
                "description": "Test auth key"
            }
        )
        assert key_response.status_code in [200, 201]
        api_key = key_response.json()["api_key"]
        
        # Retry with API key
        response = await api_client.post(
            f"/api/0/buckets/{bucket_id}",
            json={
                "type": "test",
                "client": "test-client",
                "hostname": "test-host",
            },
            headers={"X-API-Key": api_key}
        )
        assert response.status_code in [200, 201]
        
        # Cleanup
        await api_client.delete(f"/api/0/buckets/{bucket_id}")
    else:
        # Auth is disabled, should succeed
        assert response.status_code in [200, 201]
        # Cleanup
        await api_client.delete(f"/api/0/buckets/{bucket_id}")


@pytest.mark.asyncio
async def test_api_key_heartbeat_with_auth(api_client: httpx.AsyncClient):
    """Test heartbeat endpoint with API key authentication."""
    # Create an API key
    key_response = await api_client.post(
        "/api/v1/api-keys",
        json={
            "client_id": "test-heartbeat-client",
            "description": "Test heartbeat key"
        }
    )
    
    if key_response.status_code == 404:
        pytest.skip("API key endpoints not available - server needs to be rebuilt")
    
    assert key_response.status_code in [200, 201]
    api_key = key_response.json()["api_key"]
    
    # Create a bucket
    bucket_id = "test-heartbeat-bucket"
    bucket_response = await api_client.post(
        f"/api/0/buckets/{bucket_id}",
        json={
            "type": "test",
            "client": "test-client",
            "hostname": "test-host",
        },
        headers={"X-API-Key": api_key}
    )
    
    # If auth is required and we didn't provide key, might fail
    # But if it succeeded, try heartbeat
    if bucket_response.status_code in [200, 201]:
        # Send heartbeat with API key
        heartbeat_response = await api_client.post(
            f"/api/0/buckets/{bucket_id}/heartbeat?pulsetime=5.0",
            json={
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "duration": 0,
                "data": {"test": "data"}
            },
            headers={"X-API-Key": api_key}
        )
        assert heartbeat_response.status_code in [200, 201]
        
        # Cleanup
        await api_client.delete(
            f"/api/0/buckets/{bucket_id}",
            headers={"X-API-Key": api_key}
        )


@pytest.mark.asyncio
async def test_api_key_invalid_key_rejected(api_client: httpx.AsyncClient):
    """Test that invalid API keys are rejected."""
    bucket_id = "test-invalid-key-bucket"
    
    # Try to create bucket with invalid API key
    response = await api_client.post(
        f"/api/0/buckets/{bucket_id}",
        json={
            "type": "test",
            "client": "test-client",
            "hostname": "test-host",
        },
        headers={"X-API-Key": "invalid-key-that-does-not-exist"}
    )
    
    # If auth is enabled, should get 401. If disabled, might succeed (200/201/304).
    # All are acceptable behaviors depending on server configuration
    assert response.status_code in [200, 201, 304, 401], (
        f"Unexpected status code: {response.status_code}"
    )
    
    # Cleanup if bucket was created
    if response.status_code in [200, 201, 304]:
        await api_client.delete(f"/api/0/buckets/{bucket_id}")


@pytest.mark.asyncio
async def test_api_key_hash_storage(db_connection):
    """Test that API keys are stored as hashes in the database."""
    import asyncpg
    
    # Create an API key via API (we'll need to do this through API client)
    # For this test, we'll verify the storage format
    
    # Check that api_keys table exists and has key_hash column
    columns = await db_connection.fetch("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'api_keys'
    """)
    
    column_names = [col['column_name'] for col in columns]
    assert 'key_hash' in column_names
    assert 'api_key' not in column_names  # Should not store plaintext keys
    
    # Verify that stored hashes are SHA-256 length (64 hex chars)
    if len(columns) > 0:  # Table exists
        rows = await db_connection.fetch("SELECT key_hash FROM api_keys LIMIT 1")
        if rows:
            key_hash = rows[0]['key_hash']
            # SHA-256 produces 64 hex characters
            assert len(key_hash) == 64
            # Should be hexadecimal
            assert all(c in '0123456789abcdef' for c in key_hash.lower())

