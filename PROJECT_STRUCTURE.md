# Project Structure

This document describes the complete project structure after refactoring.

## Root Level

```
activitywatch/
├── docker-compose.yml      # Docker Compose configuration
├── README.md               # Main project README
├── TODO.md                 # Project TODO list
├── .gitignore              # Git ignore rules
├── pytest.ini              # Pytest configuration (if at root)
│
├── aw-server/              # Server-side components
│   ├── db/                 # Database service
│   ├── api/                # REST API server (Rust)
│   ├── query/              # Query service (reserved)
│   ├── sync/               # Sync tool (aw-sync)
│   └── webui/              # Web frontend (Vue.js)
│
├── aw-watchers/            # Client-side watchers
│   ├── watcher-window/     # Window activity watcher
│   ├── watcher-afk/        # AFK status watcher
│   └── watcher-input/      # Input activity watcher
│
├── aw-lib/              # Shared libraries
│   ├── client/             # Python client library
│   ├── client-rust/        # Rust client library
│   └── core/               # Python core library (aw-core)
│
├── docs/                   # Documentation
│   ├── ARCHITECTURE.md
│   ├── SECURITY.md
│   ├── CHANGELOG.md
│   ├── REFACTORING.md
│   └── deployment/         # Deployment guides
│
├── scripts/                # Utility scripts
│   ├── docker/             # Docker-related scripts
│   └── dev/                # Development scripts
│
└── tests/                  # Test suite
    ├── api/
    ├── client/
    ├── database/
    ├── integration/
    └── webui/
```

## Key Directories

### `aw-server/`
All server-side components:
- **db/** - PostgreSQL + TimescaleDB with migrations
- **api/** - Rust API server (workspace with multiple crates)
- **webui/** - Vue.js frontend served via Nginx

### `aw-watchers/`
Standalone watcher applications that run on user machines:
- Each watcher is independent and connects to the API server
- Dependencies on `aw-client` and `aw-core` from PyPI

### `aw-lib/`
Reusable libraries:
- **client/** - Python client library (used by all watchers)
- **client-rust/** - Rust client library (for future use)
- **core/** - Python core library (aw-core) - for local development

### `docs/`
All project documentation:
- Architecture and security documentation
- Deployment guides and scripts
- Refactoring notes

### `scripts/`
Utility scripts organized by purpose:
- **docker/** - Docker testing and validation
- **dev/** - Development utilities

### `tests/`
Comprehensive test suite:
- API tests
- Client tests
- Database tests
- Integration tests
- WebUI tests

## File Locations

### Configuration Files
- `docker-compose.yml` - Root level (standard practice)
- `.env` - Root level (not in git)
- `pytest.ini` - Root or `tests/` directory

### Documentation
- All documentation in `docs/`
- Deployment guides in `docs/deployment/`

### Database
- Initialization: `aw-server/db/init-db.sql`
- Migrations: `aw-server/db/migrations/`
- Test data: `aw-server/db/insert-fake-data.sql`

## Old Structure

## Note

The old `activitywatch/` directory has been removed. All useful code has been extracted to the new structure.

