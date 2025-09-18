#!/bin/bash
# Cross-Platform Peer Discovery Test
# Run this on both Mac and Windows to test connectivity

echo "🔍 Cross-Platform Peer Discovery Test"
echo "====================================="
echo ""

# Get local IP
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)
    echo "🍎 Running on macOS"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    # Windows (Git Bash)
    LOCAL_IP=$(ipconfig | grep "IPv4" | head -1 | awk '{print $NF}')
    echo "🪟 Running on Windows (Git Bash)"
else
    # Linux or other
    LOCAL_IP=$(hostname -I | awk '{print $1}')
    echo "🐧 Running on Linux"
fi

echo "📍 Local IP: $LOCAL_IP"
echo ""

# Test 1: Check if ports are available
echo "🔌 Port Availability Test:"
echo "   Port 8080 (Discovery):"
if command -v lsof >/dev/null 2>&1; then
    # macOS/Linux
    if lsof -i :8080 >/dev/null 2>&1; then
        echo "   ❌ Port 8080 is in use"
        lsof -i :8080
    else
        echo "   ✅ Port 8080 is available"
    fi
elif command -v netstat >/dev/null 2>&1; then
    # Windows
    if netstat -an | grep ":8080" >/dev/null 2>&1; then
        echo "   ❌ Port 8080 is in use"
        netstat -an | grep ":8080"
    else
        echo "   ✅ Port 8080 is available"
    fi
else
    echo "   ⚠️  Cannot check port availability"
fi

echo ""

# Test 2: Send test broadcast
echo "📡 Broadcasting Test:"
echo "   Sending test message to 255.255.255.255:8080..."
if command -v nc >/dev/null 2>&1; then
    echo "{\"type\":\"test\",\"ip\":\"$LOCAL_IP\",\"platform\":\"$OSTYPE\"}" | nc -u -w1 255.255.255.255 8080 2>/dev/null
    echo "   ✅ Broadcast sent via nc"
elif command -v ncat >/dev/null 2>&1; then
    echo "{\"type\":\"test\",\"ip\":\"$LOCAL_IP\",\"platform\":\"$OSTYPE\"}" | ncat -u -w1 255.255.255.255 8080 2>/dev/null
    echo "   ✅ Broadcast sent via ncat"
else
    echo "   ❌ No netcat available (nc/ncat)"
fi

echo ""

# Test 3: Listen for broadcasts
echo "👂 Listening Test (5 seconds):"
echo "   Listening on port 8080 for incoming broadcasts..."
if command -v nc >/dev/null 2>&1; then
    timeout 5 nc -u -l 8080 2>/dev/null | head -3
elif command -v ncat >/dev/null 2>&1; then
    timeout 5 ncat -u -l 8080 2>/dev/null | head -3
else
    echo "   ❌ No netcat available for listening"
fi

echo ""

# Test 4: Network connectivity
echo "🌐 Network Connectivity:"
echo "   Testing connection to Google DNS (8.8.8.8)..."
if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
    echo "   ✅ Internet connectivity: OK"
else
    echo "   ❌ Internet connectivity: Failed"
fi

echo ""

# Test 5: Local network discovery
echo "🏠 Local Network Discovery:"
NETWORK=$(echo $LOCAL_IP | cut -d. -f1-3)
echo "   Network: $NETWORK.0/24"
echo "   Pinging common gateway addresses..."

for i in 1 2 254; do
    if ping -c 1 -W 1000 $NETWORK.$i >/dev/null 2>&1; then
        echo "   ✅ $NETWORK.$i is reachable"
    else
        echo "   ❌ $NETWORK.$i is not reachable"
    fi
done

echo ""
echo "🎯 Next Steps:"
echo "   1. Run this script on both Mac and Windows"
echo "   2. Compare the results"
echo "   3. Check if both devices can see each other's broadcasts"
echo "   4. Verify both are on the same network ($NETWORK.0/24)"
echo "   5. Check firewall settings on both devices"
echo ""
echo "💡 Manual Test:"
echo "   On Mac: nc -u -l 8080"
echo "   On Windows: echo 'hello' | nc -u $LOCAL_IP 8080"
