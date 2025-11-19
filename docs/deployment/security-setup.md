# Security Configuration - ActivityWatch Server

## ✅ Security Measures Applied

### 1. API Key Authentication - ENABLED ✅

**Status**: Active  
**Configuration**: `API_KEY_AUTH_ENABLED=true` in `.env`

**API Key Created**:
- **Client ID**: `your-client-id`
- **API Key**: `YOUR_API_KEY_HERE` (generate via API endpoint)
- **Description**: Your watcher description
- **Created**: YYYY-MM-DD

**⚠️ IMPORTANT**: Store this API key securely. It's shown only once and cannot be retrieved later.

### 2. Strong Passwords ✅

All services use secure randomly generated passwords stored in `.env` file:

- **Database Password**: Generate a strong password
- **Redis Password**: Generate a strong password
- **JWT Secret**: Generate a strong secret key

**Location**: `.env` file (not committed to git)

### 3. Local Watcher Configuration ✅

**Config File**: `~/Library/Application Support/activitywatch/aw-watchers/aw-client.toml`

**Current Settings**:
```toml
[server]
hostname = "api.yourdomain.com"
port = "443"
protocol = "https"
api_key = "YOUR_API_KEY_HERE"
verify_ssl = true
```

**Note**: Replace `api.yourdomain.com` with your actual API subdomain configured in Nginx Proxy Manager.

**Next Step**: Restart ActivityWatch to apply the API key configuration.

## 🔒 Remaining Security Tasks

### 4. Firewall Configuration ⏳

**Recommended UFW Rules**:
```bash
# Allow SSH (required for management)
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS for WebUI
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# No need to open API port - access via Nginx Proxy Manager (ports 80/443)
# Database and Redis ports are internal only (not exposed externally)

# Enable firewall
sudo ufw enable
sudo ufw status verbose
```

**Alternative**: Use iptables or cloud provider firewall rules.

### 5. HTTPS/TLS Setup ✅

**Current Status**: HTTPS via Nginx Proxy Manager

**Configuration**:
- SSL certificates managed automatically by Nginx Proxy Manager
- Use Let's Encrypt for automatic certificate generation
- Configure subdomains in Nginx Proxy Manager:
  - API: `https://api.yourdomain.com` → `http://api:8080`
  - WebUI: `https://activitywatch.yourdomain.com` → `http://webui:80`
- Watcher config uses `protocol = "https"` and port `443`

### 6. Database Port Restriction ✅

**Current**: Database port is internal only (not exposed)

**Status**: No port mapping in docker-compose.yml - database is only accessible internally via Docker network.

### 7. Rate Limiting ⏳

**Optional**: Enable rate limiting to prevent abuse:
```bash
# Add to .env:
RATE_LIMIT_ENABLED=true
```

## 🔍 Testing Security

### Test API Key Authentication

1. **Without API Key** (should fail):
```bash
curl -X POST https://api.yourdomain.com/api/0/buckets \
  -H "Content-Type: application/json" \
  -d '{"id": "test", "type": "test"}'
```

2. **With API Key** (should succeed):
```bash
curl -X POST https://api.yourdomain.com/api/0/buckets \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY_HERE" \
  -d '{"id": "test", "type": "test"}'
```

**Note**: Replace `api.yourdomain.com` with your actual API subdomain.

### Verify Watcher Connection

After restarting ActivityWatch with the API key:
```bash
# Check watcher logs
tail -f ~/Library/Logs/activitywatch/aw-watcher-window.log

# Verify data is being sent
curl https://api.yourdomain.com/api/0/buckets | python3 -m json.tool
```

## 📋 Security Checklist

- [x] API key authentication enabled
- [x] Strong passwords configured
- [x] API key generated and configured locally
- [ ] Firewall rules configured
- [ ] HTTPS/TLS enabled
- [ ] Database port restricted
- [ ] Rate limiting enabled (optional)
- [ ] Regular security updates scheduled
- [ ] Backup strategy implemented

## 🚨 Important Notes

1. **API Key Storage**: The API key is stored in plaintext in the config file. For enhanced security, consider using environment variables or a secrets manager.

2. **HTTP vs HTTPS**: Currently using HTTP. For production, HTTPS is strongly recommended.

3. **Firewall**: Configure firewall rules to restrict access to necessary ports only.

4. **Monitoring**: Set up monitoring and alerting for suspicious activity.

5. **Backups**: Implement regular backups of the database and configuration.

## 📚 Additional Resources

- [SECURITY.md](../SECURITY.md) - Full security architecture documentation
- [API Key Management](../README.md#remote-deployment-with-https-and-api-keys) - API key usage guide


