# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-12-19

### Added
- Docker Compose deployment infrastructure with full microservices stack
- PostgreSQL 15 + TimescaleDB integration for scalable time-series data storage
- Redis 7 caching layer for improved performance
- Rust API server (aw-server-rust) containerized deployment
- Query service (aw-query) as separate microservice
- WebUI service with Nginx reverse proxy
- Comprehensive Docker network architecture with internal-only services
- Nginx Proxy Manager integration for external access and TLS termination
- Database initialization scripts and migration support
- Environment-based configuration with `.env.example`
- API key authentication support for remote deployments
- JWT authentication support
- Comprehensive test suite (API, database, integration, Redis, WebUI, client tests)
- Deployment documentation in `deployment-docs/`:
  - Quick start guide
  - Remote watcher setup instructions
  - Security configuration guide
  - Server deployment information
  - Helper scripts for watcher management
- VS Code development configuration
- Comprehensive `.gitignore` file covering Python, Node.js, Rust, Docker, and IDE files

### Changed
- Repository structure: moved git root from `activitywatch/` to project root
- Migrated from SQLite-only to PostgreSQL-only architecture
- All services now use internal Docker networking (no host ports exposed)
- Updated all documentation to use Nginx Proxy Manager subdomains
- Security architecture updated to use reverse proxy for TLS/HTTPS
- Watcher configuration updated to support HTTPS via Nginx Proxy Manager

### Security
- Network isolation with Docker internal networks
- Password-protected Redis and PostgreSQL services
- API key authentication for remote access
- Security headers and rate limiting support
- All personal/server information sanitized from documentation

### Documentation
- Added `ARCHITECTURE.md` documenting microservices architecture
- Updated `README.md` with Docker deployment instructions
- Updated `SECURITY.md` with new security architecture details
- All documentation uses generic placeholders (no sensitive information)

[1.0.0]: https://github.com/yvan-leroux-engineer/activitywatch/releases/tag/v1.0.0

