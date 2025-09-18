#!/bin/bash
# Test script for Peer-to-Peer Chat on single PC
# This script helps test the application by running multiple instances

echo "🧪 Peer-to-Peer Chat Single PC Testing"
echo "======================================"
echo ""

# Function to get available ports
get_available_port() {
    local port=$1
    while netstat -an | grep -q ":$port "; do
        port=$((port + 1))
    done
    echo $port
}

# Function to run test instance
run_test_instance() {
    local instance_name=$1
    local discovery_port=$2
    local websocket_port=$3
    
    echo "🚀 Starting $instance_name..."
    echo "   Discovery Port: $discovery_port"
    echo "   WebSocket Port: $websocket_port"
    
    # Create a temporary config file for this instance
    cat > "config_${instance_name}.py" << EOF
# Temporary config for $instance_name
DISCOVERY_PORT = $discovery_port
WEBSOCKET_PORT = $websocket_port
INSTANCE_NAME = "$instance_name"
EOF
    
    # Run the instance in background
    source ../myenv/bin/activate
    python index.py &
    local pid=$!
    echo "   PID: $pid"
    echo "$pid" > "${instance_name}.pid"
    echo ""
}

# Function to stop test instances
stop_test_instances() {
    echo "🛑 Stopping all test instances..."
    for pid_file in *.pid; do
        if [ -f "$pid_file" ]; then
            pid=$(cat "$pid_file")
            instance_name=$(basename "$pid_file" .pid)
            echo "   Stopping $instance_name (PID: $pid)..."
            kill $pid 2>/dev/null || echo "   $instance_name already stopped"
            rm "$pid_file"
        fi
    done
    
    # Clean up config files
    rm -f config_*.py
    echo "✅ All instances stopped"
}

# Function to show running instances
show_instances() {
    echo "📊 Currently running instances:"
    for pid_file in *.pid; do
        if [ -f "$pid_file" ]; then
            pid=$(cat "$pid_file")
            instance_name=$(basename "$pid_file" .pid)
            if ps -p $pid > /dev/null 2>&1; then
                echo "   ✅ $instance_name (PID: $pid) - Running"
            else
                echo "   ❌ $instance_name (PID: $pid) - Stopped"
                rm "$pid_file"
            fi
        fi
    done
}

# Main menu
case "$1" in
    "start")
        echo "Starting test instances..."
        
        # Find available ports
        discovery_port1=$(get_available_port 8888)
        discovery_port2=$(get_available_port $((discovery_port1 + 1)))
        websocket_port1=$(get_available_port 8765)
        websocket_port2=$(get_available_port $((websocket_port1 + 1)))
        
        # Start first instance
        run_test_instance "Alice" $discovery_port1 $websocket_port1
        
        # Wait a moment
        sleep 2
        
        # Start second instance
        run_test_instance "Bob" $discovery_port2 $websocket_port2
        
        echo "✅ Test instances started!"
        echo ""
        echo "📋 Instructions:"
        echo "   1. Two application windows should open"
        echo "   2. Look for peers in the left panel"
        echo "   3. Click on a peer to start chatting"
        echo "   4. Test sending messages between instances"
        echo ""
        echo "🛑 To stop all instances: ./test_single_pc.sh stop"
        ;;
        
    "stop")
        stop_test_instances
        ;;
        
    "status")
        show_instances
        ;;
        
    "quick")
        echo "🚀 Quick test - Starting 2 instances..."
        stop_test_instances 2>/dev/null
        
        # Start instances with default ports (they'll handle conflicts)
        source ../myenv/bin/activate
        python index.py &
        echo $! > "instance1.pid"
        
        sleep 3
        
        python index.py &
        echo $! > "instance2.pid"
        
        echo "✅ Quick test started!"
        echo "   Check for two application windows"
        echo "   Look for peers in the left panel"
        echo ""
        echo "🛑 To stop: ./test_single_pc.sh stop"
        ;;
        
    *)
        echo "Usage: $0 {start|stop|status|quick}"
        echo ""
        echo "Commands:"
        echo "  start  - Start 2 test instances with different ports"
        echo "  stop   - Stop all running test instances"
        echo "  status - Show status of running instances"
        echo "  quick  - Quick test with 2 instances (default ports)"
        echo ""
        echo "Examples:"
        echo "  $0 quick    # Quick test"
        echo "  $0 start    # Full test with custom ports"
        echo "  $0 status   # Check running instances"
        echo "  $0 stop     # Stop all instances"
        ;;
esac
