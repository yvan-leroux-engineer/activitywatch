"""
Pytest configuration and fixtures for integration tests
"""

import asyncio
import os
from typing import AsyncGenerator, Generator

import pytest

try:
    import asyncpg

    ASYNCPG_AVAILABLE = True
except ImportError:
    ASYNCPG_AVAILABLE = False
import httpx
import redis.asyncio as aioredis
from dotenv import load_dotenv

# Load environment variables from root directory
# Try loading from workspace root first, then current directory
env_paths = [
    os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
    os.path.join(os.path.dirname(__file__), ".env"),
    ".env"
]
for env_path in env_paths:
    if os.path.exists(env_path):
        load_dotenv(env_path)
        break
else:
    # Fallback to default .env loading
    load_dotenv()

# Test configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5433"))  # Default to 5433 to match docker-compose port mapping
DB_NAME = os.getenv("POSTGRES_DB", "activitywatch")
DB_USER = os.getenv("POSTGRES_USER", "aw_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "activitywatch_password")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "redis_password")

API_URL = os.getenv("API_URL", "http://localhost:8080")  # Updated to match docker-compose port
WEBUI_URL = os.getenv("WEBUI_URL", "http://localhost:80")  # Updated to match docker-compose port
QUERY_URL = os.getenv("QUERY_URL", "http://localhost:8082")


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def db_connection() -> AsyncGenerator:
    """Create a database connection for testing."""
    if not ASYNCPG_AVAILABLE:
        pytest.skip("asyncpg not available - skipping database tests")
    
    # Try to connect with timeout
    try:
        conn = await asyncio.wait_for(
            asyncpg.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                timeout=5,
            ),
            timeout=5.0,
        )
    except (asyncio.TimeoutError, ConnectionRefusedError, OSError) as e:
        # Skip tests if database is not accessible (e.g., running in Docker, not running)
        pytest.skip(f"Database not accessible from host (connection error): {e}")
    except Exception as e:
        # Catch other errors like InvalidPasswordError, etc.
        error_type = type(e).__name__
        pytest.skip(f"Database connection failed ({error_type}): {str(e)}")
    
    try:
        # Test connection
        await conn.fetchval("SELECT 1")
        yield conn
    finally:
        await conn.close()


@pytest.fixture(scope="session")
async def redis_client() -> AsyncGenerator[aioredis.Redis, None]:
    """Create a Redis client for testing."""
    redis_url = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0"
    client = aioredis.from_url(
        redis_url,
        decode_responses=True,
        password=REDIS_PASSWORD,
        socket_connect_timeout=5,
    )
    try:
        # Test connection - skip if Redis not accessible (running in Docker)
        try:
            await client.ping()
        except Exception:
            pytest.skip("Redis not accessible from host (running in Docker)")
        yield client
    finally:
        await client.aclose()


@pytest.fixture(scope="session")
def api_client() -> Generator[httpx.AsyncClient, None, None]:
    """Create an HTTP client for API testing."""
    client = httpx.AsyncClient(base_url=API_URL, timeout=30.0)
    yield client
    asyncio.run(client.aclose())


@pytest.fixture(scope="session")
def webui_client() -> Generator[httpx.AsyncClient, None, None]:
    """Create an HTTP client for WebUI testing."""
    client = httpx.AsyncClient(
        base_url=WEBUI_URL, timeout=30.0, follow_redirects=True
    )
    yield client
    asyncio.run(client.aclose())


@pytest.fixture(scope="session")
def query_client() -> Generator[httpx.AsyncClient, None, None]:
    """Create an HTTP client for Query service testing."""
    client = httpx.AsyncClient(base_url=QUERY_URL, timeout=30.0)
    yield client
    asyncio.run(client.aclose())


@pytest.fixture(autouse=True)
async def cleanup_test_data(request):
    """Clean up test data after each test."""
    yield
    # Clean up test buckets and events
    if ASYNCPG_AVAILABLE:
        try:
            # Only cleanup if db_connection fixture was used and is available
            if "db_connection" in request.fixturenames:
                try:
                    db_connection = request.getfixturevalue("db_connection")
                    # Events are deleted automatically via CASCADE when bucket is deleted
                    await db_connection.execute(
                        "DELETE FROM buckets WHERE bucket_id LIKE 'test-%'"
                    )
                    # Clean up test API keys
                    await db_connection.execute(
                        "DELETE FROM api_keys WHERE client_id LIKE 'test-%'"
                    )
                except (pytest.skip.Exception, AttributeError, RuntimeError):
                    # Skip exception means db_connection wasn't available, ignore
                    # RuntimeError can occur if event loop is closed
                    pass
        except Exception:
            pass  # Ignore cleanup errors
