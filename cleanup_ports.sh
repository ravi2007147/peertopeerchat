#!/bin/bash
# Port Cleanup Script for Peer-to-Peer Chat
# This script helps identify and kill processes using ports 8080 and 8081

echo "🔍 Checking for processes using Peer-to-Peer Chat ports..."
echo ""

# Check port 8080
echo "📡 Port 8080 (Discovery):"
if lsof -i :8080 > /dev/null 2>&1; then
    echo "❌ Port 8080 is in use:"
    lsof -i :8080
    echo ""
    echo "🔧 To kill processes using port 8080:"
    lsof -ti :8080 | xargs kill -9
    echo "✅ Killed processes using port 8080"
else
    echo "✅ Port 8080 is available"
fi

echo ""

# Check port 8081
echo "🌐 Port 8081 (WebSocket):"
if lsof -i :8081 > /dev/null 2>&1; then
    echo "❌ Port 8081 is in use:"
    lsof -i :8081
    echo ""
    echo "🔧 To kill processes using port 8081:"
    lsof -ti :8081 | xargs kill -9
    echo "✅ Killed processes using port 8081"
else
    echo "✅ Port 8081 is available"
fi

echo ""
echo "🎯 Both ports should now be available for Peer-to-Peer Chat!"
echo "💡 Run this script whenever you get 'port already in use' errors."
