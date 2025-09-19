#!/usr/bin/env python3
"""
Utility Functions for Peer-to-Peer Chat Application
"""

import socket
import uuid
import platform
from datetime import datetime

def get_local_ip():
    """Get local IP address with enhanced debugging"""
    try:
        # Connect to a remote address to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        print(f"🌐 Detected local IP: {local_ip}")
        
        # Additional network interface debugging
        try:
            if platform.system().lower() == "windows":
                print(f"🪟 Running on Windows - IP: {local_ip}")
            elif platform.system().lower() == "darwin":
                print(f"🍎 Running on macOS - IP: {local_ip}")
            else:
                print(f"🐧 Running on Linux - IP: {local_ip}")
        except:
            pass
            
        return local_ip
    except Exception as e:
        print(f"⚠️  Failed to detect local IP: {e}")
        # Fallback to localhost
        return "127.0.0.1"

def generate_user_uuid():
    """Generate a unique user UUID"""
    return str(uuid.uuid4())

def get_hostname():
    """Get system hostname"""
    try:
        return socket.gethostname()
    except:
        return "Unknown"

def format_timestamp(timestamp_str=None):
    """Format timestamp for display"""
    if timestamp_str:
        try:
            # Parse ISO timestamp
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return dt.strftime("%H:%M:%S")
        except:
            return datetime.now().strftime("%H:%M:%S")
    else:
        return datetime.now().strftime("%H:%M:%S")

def format_bytes(bytes_count):
    """Format bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_count < 1024.0:
            return f"{bytes_count:.1f} {unit}"
        bytes_count /= 1024.0
    return f"{bytes_count:.1f} TB"

def is_port_available(port, protocol='tcp'):
    """Check if a port is available"""
    try:
        if protocol.lower() == 'tcp':
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        sock.bind(('', port))
        sock.close()
        return True
    except OSError:
        return False

def get_available_port(start_port, max_attempts=100):
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        if is_port_available(port):
            return port
    return None

def validate_ip_address(ip):
    """Validate IP address format"""
    try:
        socket.inet_aton(ip)
        return True
    except socket.error:
        return False

def get_network_interfaces():
    """Get list of network interfaces"""
    interfaces = []
    try:
        import netifaces
        for interface in netifaces.interfaces():
            addrs = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in addrs:
                for addr in addrs[netifaces.AF_INET]:
                    ip = addr['addr']
                    if not ip.startswith('127.'):
                        interfaces.append({
                            'name': interface,
                            'ip': ip,
                            'netmask': addr.get('netmask', 'Unknown')
                        })
    except ImportError:
        # Fallback without netifaces
        interfaces.append({
            'name': 'default',
            'ip': get_local_ip(),
            'netmask': 'Unknown'
        })
    return interfaces

