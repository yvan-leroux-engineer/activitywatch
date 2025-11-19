# ActivityWatch Deployment Documentation

Essential documentation for managing ActivityWatch deployment.

## Quick Reference

**API Subdomain**: https://api.yourdomain.com  
**WebUI Subdomain**: https://activitywatch.yourdomain.com

## Essential Files

### Scripts
- **`restart-watcher.sh`** - Restart ActivityWatch and verify connection to remote server
- **`verify-connection.sh`** - Check if watchers are running and sending data
- **`check-heartbeats.sh`** - Check heartbeat status and recent events

### Documentation
- **`QUICK_START.md`** - Quick start guide for remote watcher setup
- **`server-info.md`** - Server details, IP address, and port information
- **`remote-watcher-setup.md`** - Complete guide for configuring local watcher to point to remote server
- **`security-setup.md`** - Security configuration including API key authentication

## Quick Commands

### Restart and Verify Watcher
```bash
./restart-watcher.sh
```

### Verify Connection Status
```bash
./verify-connection.sh
```

### Check Heartbeats
```bash
./check-heartbeats.sh
```

## Configuration

**Local Watcher Config**: `~/Library/Application Support/activitywatch/aw-watchers/aw-client.toml`

## Getting Started

1. **First Time Setup**: See `QUICK_START.md` and `remote-watcher-setup.md`
2. **Security**: Review `security-setup.md` for API key configuration
3. **Troubleshooting**: Use `verify-connection.sh` to check status
