#!/bin/bash
# Network Diagnostic Script for Peer-to-Peer Chat
# This script helps diagnose network connectivity issues

echo "🔍 Peer-to-Peer Chat Network Diagnostics"
echo "========================================"
echo ""

# Get local IP address
echo "📍 Local IP Address:"
LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)
echo "   $LOCAL_IP"
echo ""

# Check if ports are available
echo "🔌 Port Availability:"
echo "   Port 8080 (Discovery):"
if lsof -i :8080 > /dev/null 2>&1; then
    echo "   ❌ Port 8080 is in use:"
    lsof -i :8080
else
    echo "   ✅ Port 8080 is available"
fi

echo ""
echo "   Port 8081 (WebSocket):"
if lsof -i :8081 > /dev/null 2>&1; then
    echo "   ❌ Port 8081 is in use:"
    lsof -i :8081
else
    echo "   ✅ Port 8081 is available"
fi

echo ""

# Test UDP broadcast
echo "📡 Testing UDP Broadcast (Port 8080):"
echo "   Sending test broadcast..."
echo '{"type":"test_broadcast","message":"Hello from '$LOCAL_IP'"}' | nc -u -b 255.255.255.255 8080 2>/dev/null &
BROADCAST_PID=$!
sleep 1
kill $BROADCAST_PID 2>/dev/null
echo "   ✅ Broadcast sent (if no errors above)"

echo ""

# Test UDP listening
echo "👂 Testing UDP Listening (Port 8080):"
echo "   Starting listener for 5 seconds..."
timeout 5 nc -u -l 8080 &
LISTENER_PID=$!
sleep 5
kill $LISTENER_PID 2>/dev/null
echo "   ✅ Listener test completed"

echo ""

# Check network interfaces
echo "🌐 Network Interfaces:"
ifconfig | grep -A 1 "inet " | grep -v 127.0.0.1

echo ""

# Check firewall status (macOS)
echo "🔥 Firewall Status:"
if command -v /usr/libexec/ApplicationFirewall/socketfilterfw >/dev/null 2>&1; then
    FIREWALL_STATUS=$(sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo "   macOS Firewall: $FIREWALL_STATUS"
    else
        echo "   macOS Firewall: Unable to check (may need sudo)"
    fi
else
    echo "   macOS Firewall: Not available"
fi

echo ""

# Network connectivity test
echo "🌍 Network Connectivity Test:"
echo "   Testing connection to 8.8.8.8 (Google DNS)..."
if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
    echo "   ✅ Internet connectivity: OK"
else
    echo "   ❌ Internet connectivity: Failed"
fi

echo ""

# Local network scan
echo "🏠 Local Network Scan:"
echo "   Scanning local network for other devices..."
NETWORK=$(echo $LOCAL_IP | cut -d. -f1-3)
echo "   Network: $NETWORK.0/24"
echo "   Found devices:"
nmap -sn $NETWORK.0/24 2>/dev/null | grep "Nmap scan report" | head -5

echo ""
echo "🎯 Troubleshooting Tips:"
echo "   1. Ensure both devices are on the same network"
echo "   2. Check firewall settings on both devices"
echo "   3. Try running the application as administrator/sudo"
echo "   4. Verify no antivirus is blocking network traffic"
echo "   5. Check if both devices can ping each other"
echo ""
echo "💡 To test peer discovery manually:"
echo "   On Device 1: nc -u -l 8080"
echo "   On Device 2: echo 'test' | nc -u <device1_ip> 8080"
