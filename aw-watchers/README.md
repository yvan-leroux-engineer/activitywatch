# Client Components

This directory contains all client-side watchers that run on user machines.

## Structure

- **watcher-window/** - Window activity watcher
  - Tracks currently active application and window title
  - Sends heartbeats to API server

- **watcher-afk/** - AFK status watcher
  - Tracks user active/inactive state from keyboard and mouse input
  - Sends AFK status heartbeats to API server

- **watcher-input/** - Input activity watcher (optional)
  - Tracks keypresses and mouse movements
  - Experimental/optional component

## Dependencies

All watchers depend on the `aw-lib/client` library (Python `aw-client`) for:
- API communication
- Request queuing (offline support)
- Heartbeat optimization
- Configuration management

## Installation

Each watcher can be installed independently using Poetry:

```bash
cd aw-watchers/watcher-window
poetry install
poetry run aw-watcher-window
```

## Configuration

Watchers read configuration from ActivityWatch config files and environment variables.
They connect to the API server specified in the configuration.

