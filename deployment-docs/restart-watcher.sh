#!/bin/bash

# Script to restart ActivityWatch and verify connection to remote server

set -e

# Configuration - Update these with your actual values
API_SUBDOMAIN="${API_SUBDOMAIN:-api.yourdomain.com}"
WEBUI_SUBDOMAIN="${WEBUI_SUBDOMAIN:-activitywatch.yourdomain.com}"
API_URL="https://${API_SUBDOMAIN}"

echo "🔄 Restarting ActivityWatch..."
echo ""

# Step 1: Quit ActivityWatch if running
echo "1. Stopping ActivityWatch..."
if pgrep -f "ActivityWatch" > /dev/null; then
    echo "   ActivityWatch is running, quitting..."
    osascript -e 'quit app "ActivityWatch"' 2>/dev/null || killall ActivityWatch 2>/dev/null || true
    sleep 2
    echo "   ✅ ActivityWatch stopped"
else
    echo "   ℹ️  ActivityWatch was not running"
fi

# Step 2: Wait a moment
sleep 2

# Step 3: Start ActivityWatch
echo ""
echo "2. Starting ActivityWatch..."
open -a ActivityWatch
echo "   ✅ ActivityWatch started"
echo ""

# Step 4: Wait for watchers to initialize
echo "3. Waiting for watchers to initialize (15 seconds)..."
sleep 15

# Step 5: Verify connection
echo ""
echo "4. Verifying connection to remote server..."
echo "   Server: ${API_URL}"
echo ""

# Check API is accessible
if curl -s -f "${API_URL}/api/0/info" > /dev/null; then
    echo "   ✅ API server is accessible"
else
    echo "   ❌ API server is not accessible"
    exit 1
fi

# Check API key authentication status
echo ""
echo "5. Checking API key authentication..."
API_KEY=$(grep -A 5 "^\[server\]" ~/Library/Application\ Support/activitywatch/aw-client/aw-client.toml 2>/dev/null | grep "api_key" | head -1 | cut -d'"' -f2)
if [ -n "$API_KEY" ]; then
    echo "   ✅ API key found in config: ${API_KEY:0:20}..."
    echo "   Testing API key authentication..."
    TEST_RESULT=$(curl -s -X POST "${API_URL}/api/0/buckets/test-auth" \
        -H "Content-Type: application/json" \
        -H "X-API-Key: ${API_KEY}" \
        -d '{"id": "test-auth", "type": "test"}' 2>&1)
    if echo "$TEST_RESULT" | grep -q "Unauthorized\|401"; then
        echo "   ⚠️  API key authentication failed - check server logs"
    else
        echo "   ✅ API key authentication working"
        # Clean up test bucket
        curl -s -X DELETE "${API_URL}/api/0/buckets/test-auth" -H "X-API-Key: ${API_KEY}" > /dev/null 2>&1
    fi
else
    echo "   ⚠️  No API key found in config file"
fi

# Check buckets
echo ""
echo "6. Checking buckets on remote server..."
BUCKETS=$(curl -s "${API_URL}/api/0/buckets" 2>/dev/null)

if [ -z "$BUCKETS" ] || [ "$BUCKETS" = "{}" ]; then
    echo "   ⚠️  No buckets found yet (watcher may still be connecting)"
    echo "   Waiting additional 10 seconds..."
    sleep 10
    BUCKETS=$(curl -s "${API_URL}/api/0/buckets" 2>/dev/null)
fi

if [ -z "$BUCKETS" ] || [ "$BUCKETS" = "{}" ]; then
    echo "   ⚠️  No buckets found - checking watcher status..."
else
    echo "   ✅ Buckets found on remote server:"
    echo "$BUCKETS" | python3 -m json.tool 2>/dev/null || echo "$BUCKETS"
fi

# Step 7: Check watcher processes
echo ""
echo "7. Checking watcher processes..."
if pgrep -f "aw-watcher-window" > /dev/null; then
    echo "   ✅ aw-watcher-window is running"
    WINDOW_PID=$(pgrep -f "aw-watcher-window" | head -1)
    echo "   PID: $WINDOW_PID"
else
    echo "   ❌ aw-watcher-window is NOT running"
fi

if pgrep -f "aw-watcher-afk" > /dev/null; then
    echo "   ✅ aw-watcher-afk is running"
    AFK_PID=$(pgrep -f "aw-watcher-afk" | head -1)
    echo "   PID: $AFK_PID"
else
    echo "   ⚠️  aw-watcher-afk is not running (optional)"
fi

# Step 8: Check watcher logs for errors
echo ""
echo "8. Checking watcher logs for errors..."
LATEST_LOG=$(ls -t ~/Library/Logs/activitywatch/aw-watcher-window/*.log 2>/dev/null | head -1)
if [ -n "$LATEST_LOG" ]; then
    ERROR_COUNT=$(tail -50 "$LATEST_LOG" 2>/dev/null | grep -c "401\|Unauthorized\|Error" || echo "0")
    if [ "$ERROR_COUNT" -gt 0 ]; then
        echo "   ⚠️  Found $ERROR_COUNT error(s) in logs"
        echo "   Recent errors:"
        tail -50 "$LATEST_LOG" 2>/dev/null | grep -E "401|Unauthorized|Error" | tail -3 | sed 's/^/      /'
        echo ""
        echo "   💡 If you see 401 errors, the macOS Swift watcher may not support API keys yet."
        echo "   Consider temporarily disabling API key auth for testing, or use Python watcher."
    else
        echo "   ✅ No recent errors found in logs"
    fi
else
    echo "   ℹ️  No log file found"
fi

# Step 9: Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ ActivityWatch restart complete!"
echo ""
if [ -z "$BUCKETS" ] || [ "$BUCKETS" = "{}" ]; then
    echo "⚠️  WARNING: No buckets found on server."
    echo "   The watcher may not be sending data due to API key authentication."
    echo "   Check logs: tail -f ~/Library/Logs/activitywatch/aw-watcher-window/*.log"
    echo ""
fi
echo "📊 View your data at:"
echo "   https://${WEBUI_SUBDOMAIN}/#/timeline"
echo ""
echo "🔍 Monitor watcher logs:"
echo "   tail -f ~/Library/Logs/activitywatch/aw-watcher-window/*.log"
echo ""
echo "🔑 API Key configured:"
if [ -n "$API_KEY" ]; then
    echo "   ${API_KEY:0:20}..."
else
    echo "   Not found in config"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
