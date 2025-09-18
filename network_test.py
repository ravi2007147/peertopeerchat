#!/usr/bin/env python3
"""
Network Diagnostic Script for Peer-to-Peer Chat
This script helps debug network connectivity issues
"""

import socket
import json
import time
import threading
from datetime import datetime

def get_local_ip():
    """Get local IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"

def test_broadcast():
    """Test UDP broadcast functionality"""
    print("🔍 Testing UDP Broadcast...")
    
    # Get local IP
    local_ip = get_local_ip()
    print(f"📍 Local IP: {local_ip}")
    
    # Test message
    message = json.dumps({
        'type': 'test_announcement',
        'username': socket.gethostname(),
        'ip': local_ip,
        'timestamp': datetime.now().isoformat()
    })
    
    # Create broadcast socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    try:
        # Send broadcast
        sock.sendto(message.encode(), ('<broadcast>', 8888))
        print(f"✅ Broadcast sent to port 8888")
        print(f"📤 Message: {message}")
    except Exception as e:
        print(f"❌ Broadcast failed: {e}")
    finally:
        sock.close()

def test_listen():
    """Test UDP listen functionality"""
    print("🔍 Testing UDP Listen...")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    try:
        sock.bind(('', 8888))
        print("✅ Successfully bound to port 8888")
        sock.settimeout(5.0)
        
        print("👂 Listening for 5 seconds...")
        start_time = time.time()
        
        while time.time() - start_time < 5:
            try:
                data, addr = sock.recvfrom(1024)
                message = json.loads(data.decode())
                print(f"📥 Received from {addr[0]}: {message}")
            except socket.timeout:
                print("⏰ Timeout - no messages received")
                break
            except Exception as e:
                print(f"❌ Listen error: {e}")
                break
                
    except OSError as e:
        print(f"❌ Failed to bind to port 8888: {e}")
        print("💡 This might be because another instance is already running")
    finally:
        sock.close()

def test_network_info():
    """Display network information"""
    print("🌐 Network Information:")
    print(f"📍 Hostname: {socket.gethostname()}")
    print(f"📍 Local IP: {get_local_ip()}")
    
    # Test if we can resolve broadcast address
    try:
        broadcast_ip = socket.gethostbyname('<broadcast>')
        print(f"📍 Broadcast IP: {broadcast_ip}")
    except:
        print("📍 Broadcast IP: <broadcast>")
    
    # Test port availability
    print("\n🔌 Port Availability Test:")
    for port in [8888, 8765]:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('', port))
            sock.close()
            print(f"✅ Port {port}: Available")
        except OSError:
            print(f"❌ Port {port}: In use")

def main():
    print("🧪 Peer-to-Peer Chat Network Diagnostic")
    print("=" * 50)
    
    # Network info
    test_network_info()
    
    print("\n" + "=" * 50)
    
    # Test listen first
    test_listen()
    
    print("\n" + "=" * 50)
    
    # Test broadcast
    test_broadcast()
    
    print("\n" + "=" * 50)
    print("💡 Troubleshooting Tips:")
    print("1. Ensure both devices are on the same network")
    print("2. Check firewall settings - allow ports 8888 and 8765")
    print("3. Try running as administrator/root if needed")
    print("4. Check if antivirus is blocking network traffic")
    print("5. Verify network adapter settings")

if __name__ == "__main__":
    main()
