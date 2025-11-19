#!/bin/bash

# Script to verify ActivityWatch is sending data to remote server

# Configuration - Update these with your actual values
API_KEY="${API_KEY:-YOUR_API_KEY_HERE}"
API_SUBDOMAIN="${API_SUBDOMAIN:-api.yourdomain.com}"
SERVER_URL="https://${API_SUBDOMAIN}"

echo "🔍 Verifying ActivityWatch Connection"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if watchers are running
echo "1. Checking if watchers are running..."
WATCHER_COUNT=$(ps aux | grep -E "aw-watcher-window|aw-watcher-afk|aw-watcher-input" | grep -v grep | wc -l | tr -d ' ')
if [ "$WATCHER_COUNT" -gt 0 ]; then
    echo "   ✅ Found $WATCHER_COUNT watcher process(es)"
    ps aux | grep -E "aw-watcher-window|aw-watcher-afk|aw-watcher-input" | grep -v grep | awk '{print "   - " $11 " " $12 " " $13 " " $14}'
else
    echo "   ❌ No watchers running"
fi
echo ""

# Check buckets on server
echo "2. Checking buckets on remote server..."
BUCKETS=$(curl -s -H "X-API-Key: $API_KEY" "$SERVER_URL/api/0/buckets")
BUCKET_COUNT=$(echo "$BUCKETS" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data))" 2>/dev/null || echo "0")

if [ "$BUCKET_COUNT" -gt 0 ]; then
    echo "   ✅ Found $BUCKET_COUNT bucket(s) on server:"
    echo "$BUCKETS" | python3 -m json.tool 2>/dev/null | grep -E '^\s+"[^"]+":' | sed 's/^/   /'
else
    echo "   ❌ No buckets found on server"
fi
echo ""

# Check for recent events
echo "3. Checking for recent events..."
WINDOW_BUCKET="${WINDOW_BUCKET:-aw-watcher-window_YOUR_HOSTNAME}"
EVENTS=$(curl -s -H "X-API-Key: $API_KEY" "$SERVER_URL/api/0/buckets/$WINDOW_BUCKET/events?limit=1")
EVENT_COUNT=$(echo "$EVENTS" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data))" 2>/dev/null || echo "0")

if [ "$EVENT_COUNT" -gt 0 ]; then
    echo "   ✅ Found $EVENT_COUNT recent event(s) in window watcher"
    LATEST=$(echo "$EVENTS" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data[0]['timestamp'] if data else 'None')" 2>/dev/null)
    echo "   Latest event timestamp: $LATEST"
else
    echo "   ⚠️  No events found yet (watcher may have just started)"
fi
echo ""

# Check bucket metadata
echo "4. Checking bucket metadata..."
BUCKET_INFO=$(curl -s -H "X-API-Key: $API_KEY" "$SERVER_URL/api/0/buckets/$WINDOW_BUCKET")
LAST_UPDATED=$(echo "$BUCKET_INFO" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('last_updated', 'Never'))" 2>/dev/null)

if [ "$LAST_UPDATED" != "Never" ] && [ "$LAST_UPDATED" != "None" ]; then
    echo "   ✅ Bucket last updated: $LAST_UPDATED"
else
    echo "   ⚠️  Bucket created but no updates yet"
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 Summary:"
echo ""
if [ "$WATCHER_COUNT" -gt 0 ] && [ "$BUCKET_COUNT" -gt 0 ]; then
    echo "✅ Watchers are running and buckets exist on server"
    if [ "$EVENT_COUNT" -gt 0 ] || [ "$LAST_UPDATED" != "Never" ]; then
        echo "✅ Data is being sent to the server"
    else
        echo "⚠️  Buckets exist but no events yet - wait a few minutes for heartbeats"
    fi
else
    echo "❌ Issue detected - check the details above"
fi
echo ""

