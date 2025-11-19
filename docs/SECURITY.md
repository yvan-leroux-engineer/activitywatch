# Security Architecture

## Network Security

- **Internal Network**: All services on Docker network (`aw-network`)
- **Port Exposure**: No ports exposed to host - all services internal only
- **Access**: Via Nginx Proxy Manager (must be on same Docker network)
- **Internal Services**: Use `expose` (not `ports`) - not accessible externally
- **Firewall**: Only Nginx Proxy Manager ports (80/443) need to be open on host

## Transport Security

- **TLS/HTTPS**: Can be configured via reverse proxy (Traefik/Nginx)
- **SSL Verification**: Configurable certificate validation (default: enabled)
- **Security Headers**: HSTS, CSP, X-Frame-Options, etc.

## Authentication & Authorization

- **JWT Tokens**: Optional authentication (enable via `AUTH_ENABLED=true`)
- **API Keys**: Optional authentication for watchers (enable via `API_KEY_AUTH_ENABLED=true`)
  - API keys are hashed using SHA-256 before storage
  - Keys are returned only once on creation
  - Can be revoked via API endpoint
  - Required for write operations when enabled
- **Rate Limiting**: Optional (enable via `RATE_LIMIT_ENABLED=true`)
- **Security Headers**: Always enabled

## Data Security

- **Database**: Password protected, internal only
- **Redis**: Password protected (`REDIS_PASSWORD`)
- **Secrets**: Stored in `.env` (not committed)
- **Encryption**: TLS for external, internal network isolation

## Remote Deployment Security

For remote deployments where watchers connect over the internet:

1. **Enable HTTPS**: Configure reverse proxy (Traefik/Nginx) with TLS certificates
2. **Enable API Key Authentication**: Set `API_KEY_AUTH_ENABLED=true`
3. **Generate API Keys**: Use `/api/v1/api-keys` endpoint to create keys
4. **Configure Watchers**: Update watcher config with:
   - `protocol = "https"`
   - `api_key = "your-key"`
   - `verify_ssl = true` (or false for self-signed certs)

### API Key Management

- **Create**: `POST /api/v1/api-keys` - Returns key only once
- **List**: `GET /api/v1/api-keys` - Lists keys without exposing them
- **Revoke**: `DELETE /api/v1/api-keys/<id>` - Deactivates a key

API keys are hashed using SHA-256 before storage. The plaintext key is returned only once on creation.
