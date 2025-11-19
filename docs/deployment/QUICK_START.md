# Quick Start - Remote Watcher Test

## ✅ Configuration Complete!

Your local watcher is now configured to send data to the remote server via **https://api.yourdomain.com**.

## 🚀 Restart ActivityWatch

**IMPORTANT**: You need to restart ActivityWatch for the changes to take effect.

### Quick Restart:
1. **Quit ActivityWatch** completely (⌘Q or right-click dock icon → Quit)
2. **Restart ActivityWatch** from Applications
3. Watchers will automatically connect to the remote server

### Verify Connection:

After restarting, check that data is being sent:

```bash
# Check buckets on remote server (should show your machine)
curl https://api.yourdomain.com/api/0/buckets | python3 -m json.tool
```

You should see a bucket like: `aw-watcher-window_<your-hostname>`

**Note**: Replace `api.yourdomain.com` with your actual API subdomain.

## 📊 View Your Data

Open the remote WebUI to see your window activity:
**https://activitywatch.yourdomain.com/#/timeline**

**Note**: Replace `activitywatch.yourdomain.com` with your actual WebUI subdomain.

## 🔍 Troubleshooting

If no data appears:
1. Check watcher is running: `ps aux | grep aw-watcher-window`
2. Check logs: `tail -f ~/Library/Logs/activitywatch/aw-watcher-window.log`
3. Verify config: `cat ~/Library/Application\ Support/activitywatch/aw-watchers/aw-client.toml`

## 📝 Configuration Location

Config file: `~/Library/Application Support/activitywatch/aw-watchers/aw-client.toml`

Current settings:
- Host: api.yourdomain.com
- Port: 443
- Protocol: https

**Note**: Replace `api.yourdomain.com` with your actual API subdomain configured in Nginx Proxy Manager.


