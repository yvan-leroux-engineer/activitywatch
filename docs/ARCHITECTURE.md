# ActivityWatch Architecture

## Overview

Microservices architecture with Docker, PostgreSQL, and Rust API server.

## Services

```
Internet
  │
  ▼
Nginx Proxy Manager
  │
  ├──► WebUI (webui:80) ──► API (api:8080) ──► PostgreSQL + TimescaleDB
  │                                        └──► Redis Cache
  │
  └──► API (api:8080) ──► PostgreSQL + TimescaleDB
                         └──► Redis Cache
                              │
                              └──► Watchers (External - Host Machine)
                                   └──► Connect via Nginx Proxy Manager subdomain
```

**Important**: Watchers are **NOT Docker containers**. They are standalone applications running on the host machine that connect to the API server via Nginx Proxy Manager subdomain.

## Data Flow

1. **User Request** → Nginx Proxy Manager → WebUI (webui:80) or API (api:8080)
2. **WebUI** → API (proxied via nginx)
3. **API** → PostgreSQL (queries) / Redis (cache)
4. **Watchers** → Nginx Proxy Manager → API (api:8080)
5. **Response** → User or Watcher

## Database Schema

- **buckets**: Bucket metadata (id, type, client, hostname, data)
- **events**: Time-series events (hypertable with timestamp partitioning)
- **key_value**: Settings and configuration

## Network Security

- All Docker services on internal Docker network (`aw-network`)
- No ports exposed to host - all services internal only
- Access via Nginx Proxy Manager (must be on same Docker network)
- Database and Redis password protected, not exposed externally
- Watchers run outside Docker and connect via Nginx Proxy Manager subdomain

## Technology Stack

- **API**: Rust (Rocket) + SQLx + PostgreSQL
- **Database**: PostgreSQL 15 + TimescaleDB
- **Cache**: Redis 7
- **Frontend**: Vue.js + Nginx
- **Container Runtime**: Docker Compose
