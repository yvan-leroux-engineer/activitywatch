# Refactoring Complete ✅

## New Directory Structure

```
activitywatch/
├── aw-server/              # Server-side components
│   ├── db/             # Database (PostgreSQL + TimescaleDB)
│   │   ├── init-db.sql
│   │   ├── migrations/
│   │   └── Dockerfile
│   ├── api/            # REST API server (Rust)
│   │   ├── aw-server/   # Main API server
│   │   ├── aw-datastore/
│   │   ├── aw-models/
│   │   ├── aw-query/   # Query library
│   │   ├── aw-transform/
│   │   ├── Cargo.toml
│   │   └── Dockerfile
│   ├── query/           # Reserved for future Python query service
│   └── webui/          # Web frontend (Vue.js + Nginx)
│       ├── src/
│       ├── dist/
│       ├── nginx.conf
│       └── Dockerfile
│
├── aw-watchers/             # Client-side watchers
│   ├── watcher-window/ # Window activity watcher
│   ├── watcher-afk/    # AFK status watcher
│   └── watcher-input/  # Input activity watcher (optional)
│
└── aw-lib/             # Shared libraries
    ├── aw-watchers/         # Python client library (aw-client)
    └── client-rust/    # Rust client library (aw-client-rust)
```

## Changes Made

### ✅ Server Components
- Moved database initialization and migrations to `aw-server/db/`
- Moved Rust API server to `aw-server/api/` with all workspace members
- Moved web UI to `aw-server/webui/`
- Created Dockerfile for database service

### ✅ Client Components
- Moved all watchers to `aw-watchers/` directory
- Watchers maintain their dependencies on PyPI packages (`aw-watchers`, `aw-core`)
- No code changes needed - imports work as-is

### ✅ Shared Libraries
- Moved `aw-watchers` (Python) to `aw-lib/aw-watchers/`
- Moved `aw-client-rust` to `aw-lib/client-rust/`
- Both libraries preserved for future use

### ✅ Docker Compose
- Updated all build contexts to new paths
- Database service now builds from `aw-server/db/`
- API service builds from `aw-server/api/`
- WebUI service builds from `aw-server/webui/`
- Query service commented out (not implemented yet)

### ✅ Documentation
- Created README files for each major directory
- Created REFACTORING.md with migration notes

## Next Steps

1. **Test the build:**
   ```bash
   docker-compose build
   docker-compose up -d
   ```

2. **Verify services:**
   - Check API health: `curl http://localhost:8080/health`
   - Check WebUI: Access via Nginx Proxy Manager
   - Verify database: Connect and check tables

3. **Update CI/CD** (if applicable):
   - Update build paths in CI configuration
   - Update deployment scripts

4. **Clean up old directories** (after verification):
   - The old `activitywatch/` directory can be removed once everything is verified
   - Keep as backup until confident everything works

## Notes

- **Watchers**: No changes needed - they use PyPI packages
- **API Server**: All Rust workspace members are in `aw-server/api/`
- **Database**: Migrations are run by API server on startup
- **WebUI**: Build assets should be generated before running docker-compose

## Dependencies

All watchers depend on:
- `aw-watchers` (from PyPI or `aw-lib/aw-watchers/`)
- `aw-core` (from PyPI, dependency of `aw-watchers`)

These are installed automatically when installing watchers via Poetry or pip.

