# Shared Libraries

This directory contains shared libraries used by both server and client components.

## Structure

- **client/** - Python client library (`aw-client`)
  - **ESSENTIAL** - Used by all Python watchers
  - Provides API wrapper with:
    - Connection management
    - Request queuing (offline support)
    - Heartbeat optimization
    - Configuration management
    - Single instance enforcement
  - Install via: `pip install aw-client` or `poetry install` in this directory

- **client-rust/** - Rust client library (`aw-client-rust`)
  - Rust implementation of the client library
  - Work in progress
  - Useful for future Rust-based watchers or tools

## Usage

### Python Client

```python
from aw_client import ActivityWatchClient

client = ActivityWatchClient("my-watcher", host="api.example.com", port=8080)
client.create_bucket("my-bucket", "my-type")
client.heartbeat("my-bucket", event, pulsetime=5.0, queued=True)
```

### Rust Client

```rust
use aw_client_rust::AwClient;

let client = AwClient::new("localhost", 8080, "my-watcher")?;
client.create_bucket_simple("my-bucket", "my-type").await?;
client.heartbeat("my-bucket", &event, 5.0).await?;
```

