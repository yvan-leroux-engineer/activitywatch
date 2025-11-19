# ActivityWatch - Modernized Docker Deployment

Modernized ActivityWatch with PostgreSQL, microservices architecture, and Docker.

## Quick Start

### Prerequisites

- Docker and Docker Compose
- `.env` file (copy from `.env.example`)

### Start Services

```bash
# Copy environment file
cp .env.example .env
# Edit .env with your passwords

# Start all services
docker-compose up -d

# Check status
docker-compose ps
```

### Access

All services are exposed internally only. Access via **Nginx Proxy Manager**:

- **WebUI**: Configure subdomain pointing to `http://webui:80`
- **API**: Configure subdomain pointing to `http://api:8080`
- **Watchers**: Connect via API subdomain configured in Nginx Proxy Manager

## Architecture

- **Database**: PostgreSQL + TimescaleDB (time-series optimized)
- **Cache**: Redis (password protected)
- **API**: Rust (Rocket) - PostgreSQL-only, no SQLite
- **WebUI**: Nginx + Vue.js

All Docker services communicate internally via Docker network. Services are only exposed internally and accessed via Nginx Proxy Manager.

## Nginx Proxy Manager Setup

1. **Connect Nginx Proxy Manager to the Docker network**:
   ```bash
   docker network connect activitywatch-network <nginx-proxy-manager-container>
   ```

2. **Configure Proxy Hosts**:
   - **WebUI**: Forward to `http://webui:80`
   - **API**: Forward to `http://api:8080`

3. **Watchers**: Configure to connect via the API subdomain (e.g., `https://api.yourdomain.com`)

## Watchers

**Important**: Watchers are **NOT Docker containers**. They are standalone applications that run directly on your host machine and connect to the API server via the Nginx Proxy Manager subdomain.

## Environment Variables

Required in `.env`:

```bash
DATABASE_URL=postgresql://aw_user:password@db:5432/activitywatch
DB_PASSWORD=your_secure_password
REDIS_PASSWORD=your_redis_password
JWT_SECRET=your_jwt_secret_key

# Optional: Enable API key authentication for remote deployments
API_KEY_AUTH_ENABLED=false
```

## Services

| Service | Internal Port | Description |
|---------|---------------|-------------|
| `db` | 5432 | PostgreSQL + TimescaleDB (internal only) |
| `redis` | 6379 | Redis cache (internal only) |
| `api` | 8080 | Rust API server (access via Nginx Proxy Manager) |
| `webui` | 80 | Nginx + Vue.js frontend (access via Nginx Proxy Manager) |

## Documentation

- `ARCHITECTURE.md` - Architecture details
- `SECURITY.md` - Security architecture
- `deployment-docs/` - Deployment and configuration guides
