# Remote Watcher Configuration

## Overview
Configure local watchers to send data to the remote ActivityWatch server via Nginx Proxy Manager subdomain.

## Server Information
- **API Subdomain**: `https://api.yourdomain.com` (configure in Nginx Proxy Manager)
- **WebUI Subdomain**: `https://activitywatch.yourdomain.com` (configure in Nginx Proxy Manager)
- **API Endpoint**: `https://api.yourdomain.com/api/0/info`

## Configuration Complete ✅

The watcher configuration has been updated at:
**macOS**: `~/Library/Application Support/activitywatch/aw-watchers/aw-client.toml`

### Current Configuration:
```toml
[server]
hostname = "api.yourdomain.com"
port = "443"
protocol = "https"
api_key = ""
verify_ssl = true

[client]
commit_interval = 10
```

**Note**: Replace `api.yourdomain.com` with your actual API subdomain configured in Nginx Proxy Manager.

## Next Steps

### 1. Restart ActivityWatch Watchers

The watchers need to be restarted to pick up the new configuration:

**Option A: Restart via ActivityWatch App**
- Quit ActivityWatch app completely
- Restart ActivityWatch app
- Watchers will automatically reconnect to the remote server

**Option B: Restart via Command Line**
```bash
# Stop existing watchers
killall aw-watcher-window aw-watcher-afk

# Restart ActivityWatch (watchers will start automatically)
open -a ActivityWatch
```

### 2. Verify Connection

After restarting, verify the connection:

```bash
# Check if buckets are being created on remote server
curl https://api.yourdomain.com/api/0/buckets | python3 -m json.tool

# Check watcher logs
tail -f ~/Library/Logs/activitywatch/aw-watcher-window.log
```

### 3. View Data in WebUI

Open the remote WebUI to see your window activity:
**https://activitywatch.yourdomain.com/#/timeline**

**Note**: Replace `activitywatch.yourdomain.com` with your actual WebUI subdomain.

## Testing Connection

1. **Test API connectivity**:
   ```bash
   curl https://api.yourdomain.com/api/0/info
   ```

2. **Check buckets on server** (should show your machine's bucket after restart):
   ```bash
   curl https://api.yourdomain.com/api/0/buckets | python3 -m json.tool
   ```

3. **Expected bucket name**: `aw-watcher-window_<your-hostname>`
   - Example: `aw-watcher-window_YOUR_HOSTNAME`

## Alternative Configuration Methods

### Method 1: Command Line Arguments (Temporary)
Run watcher with explicit host (overrides config):

```bash
aw-watcher-window --host api.yourdomain.com --port 443
aw-watcher-afk --host api.yourdomain.com --port 443
```

**Note**: Use port 443 for HTTPS or port 80 for HTTP (if not using SSL).

### Method 2: Environment Variables
```bash
export API_HOST=api.yourdomain.com
export API_PORT=443
```

## Security Notes

✅ **Recommended Setup**: HTTPS via Nginx Proxy Manager
- Use HTTPS subdomains (port 443) for encrypted connections
- Enable API key authentication: Set `API_KEY_AUTH_ENABLED=true` on server
- Generate API keys and configure in config file
- SSL certificates managed automatically by Nginx Proxy Manager

## Troubleshooting

- **Connection refused**: 
  - Verify Nginx Proxy Manager is running and configured correctly
  - Check that API subdomain points to `http://api:8080` in Nginx Proxy Manager
  - Ensure Nginx Proxy Manager is on the same Docker network (`activitywatch-network`)
- **SSL errors**: 
  - Verify SSL certificate is valid in Nginx Proxy Manager
  - Check `verify_ssl = true` in config matches your certificate setup
  - For self-signed certificates, set `verify_ssl = false` (not recommended for production)
- **No data appearing**: 
  - Verify watcher is running: `ps aux | grep aw-watcher-window`
  - Check logs: `tail -f ~/Library/Logs/activitywatch/aw-watcher-window.log`
  - Ensure config file was saved correctly
  - Test API connectivity: `curl https://api.yourdomain.com/api/0/info`
- **Watcher still connecting to localhost**: 
  - Make sure ActivityWatch app was fully restarted
  - Check config file location matches: `~/Library/Application Support/activitywatch/aw-watchers/aw-client.toml`

## Reverting to Local Server

To switch back to local server (for local development), change config to:
```toml
[server]
hostname = "127.0.0.1"
port = "5600"
protocol = "http"
```

Then restart ActivityWatch.
