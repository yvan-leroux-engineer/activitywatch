#!/bin/bash

# Script to check if heartbeats are being sent to the server

# Configuration - Update these with your actual values
API_KEY="${API_KEY:-YOUR_API_KEY_HERE}"
API_SUBDOMAIN="${API_SUBDOMAIN:-api.yourdomain.com}"
SERVER_URL="https://${API_SUBDOMAIN}"
BUCKET="${BUCKET:-aw-watcher-window_YOUR_HOSTNAME}"

echo "🔍 Checking Heartbeat Status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if watcher is running
echo "1. Watcher Process Status:"
WATCHER_RUNNING=$(ps aux | grep "aw-watcher-window-macos" | grep -v grep | wc -l | tr -d ' ')
if [ "$WATCHER_RUNNING" -gt 0 ]; then
    echo "   ✅ Watcher is running"
    ps aux | grep "aw-watcher-window-macos" | grep -v grep | awk '{print "   PID: " $2 " | Started: " $9}'
else
    echo "   ❌ Watcher is NOT running"
    echo "   → Restart ActivityWatch: open -a ActivityWatch"
fi
echo ""

# Check latest event
echo "2. Latest Event on Server:"
LATEST_EVENT=$(curl -s -H "X-API-Key: $API_KEY" "$SERVER_URL/api/0/buckets/$BUCKET/events?limit=1")
EVENT_COUNT=$(echo "$LATEST_EVENT" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data))" 2>/dev/null || echo "0")

if [ "$EVENT_COUNT" -gt 0 ]; then
    TIMESTAMP=$(echo "$LATEST_EVENT" | python3 -c "import sys, json; from datetime import datetime; data=json.load(sys.stdin); print(data[0]['timestamp'])" 2>/dev/null)
    APP=$(echo "$LATEST_EVENT" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data[0]['data']['app'])" 2>/dev/null)
    TITLE=$(echo "$LATEST_EVENT" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data[0]['data']['title'])" 2>/dev/null)
    
    # Calculate age
    AGE=$(python3 -c "
from datetime import datetime, timezone
import sys
ts = '$TIMESTAMP'
if ts:
    event_time = datetime.fromisoformat(ts.replace('Z', '+00:00'))
    now = datetime.now(timezone.utc)
    age_seconds = (now - event_time).total_seconds()
    print(f'{int(age_seconds)}')
else:
    print('0')
" 2>/dev/null || echo "0")
    
    echo "   ✅ Latest event found:"
    echo "      App: $APP"
    echo "      Title: $TITLE"
    echo "      Timestamp: $TIMESTAMP"
    
    if [ "$AGE" -lt 60 ]; then
        echo "      ⏰ Age: ${AGE} seconds ago (✅ Recent)"
    elif [ "$AGE" -lt 300 ]; then
        echo "      ⏰ Age: ${AGE} seconds ago (⚠️  ${AGE} seconds old)"
    else
        echo "      ⏰ Age: ${AGE} seconds ago (❌ ${AGE} seconds old - watcher may have stopped)"
    fi
else
    echo "   ❌ No events found on server"
fi
echo ""

# Check bucket metadata
echo "3. Bucket Status:"
BUCKET_INFO=$(curl -s -H "X-API-Key: $API_KEY" "$SERVER_URL/api/0/buckets/$BUCKET")
LAST_UPDATED=$(echo "$BUCKET_INFO" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('last_updated', 'Never'))" 2>/dev/null)
CREATED=$(echo "$BUCKET_INFO" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('created', 'Unknown'))" 2>/dev/null)

echo "   Created: $CREATED"
echo "   Last updated: $LAST_UPDATED"
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 Summary:"
echo ""

if [ "$WATCHER_RUNNING" -eq 0 ]; then
    echo "❌ Watcher is not running - restart ActivityWatch"
elif [ "$EVENT_COUNT" -eq 0 ]; then
    echo "⚠️  Watcher running but no events yet - wait a minute"
elif [ "$AGE" -gt 300 ]; then
    echo "⚠️  Watcher running but last event is old (${AGE}s) - check logs"
else
    echo "✅ Watcher is running and sending heartbeats"
fi
echo ""

