# Server Components

This directory contains all server-side components of ActivityWatch.

## Structure

- **db/** - Database service (PostgreSQL + TimescaleDB)
  - `init-db.sql` - Database initialization script
  - `migrations/` - Database migration files (used by API server)
  - `Dockerfile` - Database container definition

- **api/** - REST API server (Rust)
  - Main API server implementation
  - Contains workspace with: `aw-server`, `aw-datastore`, `aw-models`, `aw-query`, `aw-transform`
  - Handles all API endpoints, authentication, and database operations

- **query/** - Query service (optional, currently not implemented)
  - Reserved for future Python-based query microservice
  - Query functionality is currently available via API server's `/api/0/query` endpoint

- **webui/** - Web frontend (Vue.js)
  - Vue.js application source code
  - Built assets served via Nginx
  - `nginx.conf` - Nginx configuration
  - `Dockerfile` - WebUI container definition

## Building

See root `docker-compose.yml` for building and running all services.

