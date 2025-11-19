# Refactoring Summary

This document describes the new directory structure after the refactoring.

## New Structure

```
activitywatch/
├── aw-server/              # Server-side components
│   ├── db/             # Database service (PostgreSQL + TimescaleDB)
│   ├── api/            # REST API server (Rust)
│   ├── query/          # Query service (optional, reserved for future)
│   └── webui/          # Web frontend (Vue.js + Nginx)
│
├── aw-watchers/            # Client-side watchers
│   ├── watcher-window/     # Window activity watcher
│   ├── watcher-afk/        # AFK status watcher
│   └── watcher-input/      # Input activity watcher (optional)
│
└── aw-lib/              # Shared libraries
    ├── client/             # Python client library (aw-client)
    └── client-rust/        # Rust client library (aw-client-rust)
```

## Migration Notes

### Docker Compose

The `docker-compose.yml` has been updated with new paths:

- `./aw-server/db` - Database service
- `./aw-server/api` - API server
- `./aw-server/webui` - WebUI service
- Query service is commented out (not implemented yet)

### Watchers

Watchers continue to work as before. They depend on `aw-client` from PyPI, which can also be installed from `aw-lib/client` for local development.

### API Server

The API server is now in `aw-server/api/` and contains the Rust workspace with:

- `aw-server` - Main API server
- `aw-datastore` - Database layer
- `aw-models` - Data models
- `aw-query` - Query library
- `aw-transform` - Transformation utilities

### Old Structure

The old `activitywatch/` directory has been removed. All useful code has been extracted to the new structure.

## Next Steps

1. Test docker-compose build with new paths
2. Update any CI/CD pipelines
3. Update documentation references
4. Consider removing old `activitywatch/` directory after verification
