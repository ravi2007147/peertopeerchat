#!/usr/bin/env python3
"""
Dialog Classes for Peer-to-Peer Chat Application
"""

import platform
import subprocess
import socket
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QMessageBox, QDialogButtonBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class FirewallConfigDialog(QDialog):
    """Dialog for showing firewall configuration instructions"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Firewall Configuration")
        self.setModal(True)
        self.resize(600, 500)
        
        # Apply light theme to fix readability
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                color: #000000;
            }
            QLabel {
                color: #000000;
            }
            QTextEdit {
                background-color: #f8f8f8;
                color: #000000;
                border: 1px solid #cccccc;
            }
            QPushButton {
                background-color: #e0e0e0;
                color: #000000;
                border: 1px solid #cccccc;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
        """)
        
        self.current_platform = platform.system().lower()
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI"""
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Firewall Configuration Instructions")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(title_label)
        
        # Platform info
        platform_label = QLabel(f"Detected Platform: {self.current_platform.title()}")
        platform_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(platform_label)
        
        # Ports info
        ports_label = QLabel("Required Ports:")
        ports_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(ports_label)
        
        ports_info = QLabel("• UDP Port 8080 (Peer Discovery)\n• TCP Port 8081 (WebSocket Communication)")
        layout.addWidget(ports_info)
        
        # Instructions
        instructions_label = QLabel("Instructions:")
        instructions_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(instructions_label)
        
        self.instructions_text = QTextEdit()
        self.instructions_text.setReadOnly(True)
        self.instructions_text.setPlainText(self.get_platform_instructions())
        layout.addWidget(self.instructions_text)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        copy_button = QPushButton("Copy Instructions")
        copy_button.clicked.connect(self.copy_instructions)
        button_layout.addWidget(copy_button)
        
        test_button = QPushButton("Test Ports")
        test_button.clicked.connect(self.test_ports)
        button_layout.addWidget(test_button)
        
        auto_button = QPushButton("Auto-Configure Firewall")
        auto_button.clicked.connect(self.auto_configure_firewall)
        button_layout.addWidget(auto_button)
        
        cleanup_button = QPushButton("Cleanup Ports")
        cleanup_button.clicked.connect(self.cleanup_ports)
        button_layout.addWidget(cleanup_button)
        
        layout.addLayout(button_layout)
        
        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
        
        self.setLayout(layout)
    
    def get_platform_instructions(self):
        """Get platform-specific instructions"""
        if self.current_platform == "darwin":
            return self.get_macos_instructions()
        elif self.current_platform == "windows":
            return self.get_windows_instructions()
        else:
            return self.get_linux_instructions()
    
    def get_macos_instructions(self):
        """Get macOS firewall instructions"""
        return """
macOS Firewall Configuration:

1. Open System Preferences → Security & Privacy → Firewall
2. Click the lock icon and enter your password
3. Click "Firewall Options..."
4. Add Python to allowed applications:
   - Click "+" button
   - Navigate to /usr/bin/python3 or your Python installation
   - Select "Allow incoming connections"

Alternative (Terminal):
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/bin/python3
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblock /usr/bin/python3

Manual Port Opening:
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/bin/python3
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblock /usr/bin/python3

Note: You may need to restart the application after configuring the firewall.
"""
    
    def get_windows_instructions(self):
        """Get Windows firewall instructions"""
        return """
Windows Firewall Configuration:

Method 1 - Windows Firewall with Advanced Security:
1. Press Win + R, type "wf.msc" and press Enter
2. Click "Inbound Rules" → "New Rule"
3. Select "Port" → Next
4. Select "UDP" and enter port "8080" → Next
5. Select "Allow the connection" → Next
6. Check all profiles → Next
7. Name: "Peer Discovery" → Finish
8. Repeat for TCP port 8081

Method 2 - Command Line (Run as Administrator):
netsh advfirewall firewall add rule name="Peer Discovery UDP" dir=in action=allow protocol=UDP localport=8080
netsh advfirewall firewall add rule name="Peer Chat TCP" dir=in action=allow protocol=TCP localport=8081

Method 3 - Windows Defender Firewall:
1. Open Windows Defender Firewall
2. Click "Allow an app or feature through Windows Defender Firewall"
3. Click "Change settings" → "Allow another app..."
4. Browse to your Python executable
5. Check both "Private" and "Public" → OK

Note: You may need to restart the application after configuring the firewall.
"""
    
    def get_linux_instructions(self):
        """Get Linux firewall instructions"""
        return """
Linux Firewall Configuration:

For UFW (Ubuntu/Debian):
sudo ufw allow 8080/udp
sudo ufw allow 8081/tcp
sudo ufw reload

For iptables:
sudo iptables -A INPUT -p udp --dport 8080 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 8081 -j ACCEPT
sudo iptables-save > /etc/iptables/rules.v4

For firewalld (CentOS/RHEL/Fedora):
sudo firewall-cmd --permanent --add-port=8080/udp
sudo firewall-cmd --permanent --add-port=8081/tcp
sudo firewall-cmd --reload

For systemd-resolved (if using):
sudo systemctl stop systemd-resolved
sudo systemctl disable systemd-resolved

Note: Commands may vary based on your Linux distribution.
Make sure to restart the application after configuring the firewall.
"""
    
    def copy_instructions(self):
        """Copy instructions to clipboard"""
        from PyQt5.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self.instructions_text.toPlainText())
        QMessageBox.information(self, "Copied", "Instructions copied to clipboard!")
    
    def test_ports(self):
        """Test if ports are available"""
        results = []
        
        # Test UDP port 8080
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind(('', 8080))
            sock.close()
            results.append("UDP Port 8080 (Discovery): ✅ Available")
        except OSError:
            results.append("UDP Port 8080 (Discovery): ❌ IN USE")
        
        # Test TCP port 8081
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('', 8081))
            sock.close()
            results.append("TCP Port 8081 (WebSocket): ✅ Available")
        except OSError:
            results.append("TCP Port 8081 (WebSocket): ❌ IN USE")
        
        QMessageBox.information(self, "Port Test Results", "\n".join(results))
    
    def auto_configure_firewall(self):
        """Automatically configure firewall"""
        reply = QMessageBox.question(
            self, "Auto-Configure Firewall", 
            "This will attempt to automatically configure your firewall.\n"
            "You may be prompted for administrator/sudo password.\n\n"
            "Continue?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                if self.current_platform == "darwin":
                    self.configure_macos_firewall()
                elif self.current_platform == "windows":
                    self.configure_windows_firewall()
                else:
                    self.configure_linux_firewall()
                
                QMessageBox.information(self, "Success", "Firewall configuration completed!")
                self.test_ports()
                
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to configure firewall: {str(e)}")
    
    def configure_macos_firewall(self):
        """Configure macOS firewall"""
        subprocess.run([
            "sudo", "/usr/libexec/ApplicationFirewall/socketfilterfw", 
            "--add", "/usr/bin/python3"
        ], check=True)
        subprocess.run([
            "sudo", "/usr/libexec/ApplicationFirewall/socketfilterfw", 
            "--unblock", "/usr/bin/python3"
        ], check=True)
    
    def configure_windows_firewall(self):
        """Configure Windows firewall"""
        subprocess.run([
            "netsh", "advfirewall", "firewall", "add", "rule",
            "name=Peer Discovery UDP", "dir=in", "action=allow",
            "protocol=UDP", "localport=8080"
        ], check=True)
        subprocess.run([
            "netsh", "advfirewall", "firewall", "add", "rule",
            "name=Peer Chat TCP", "dir=in", "action=allow",
            "protocol=TCP", "localport=8081"
        ], check=True)
    
    def configure_linux_firewall(self):
        """Configure Linux firewall"""
        try:
            # Try UFW first
            subprocess.run(["sudo", "ufw", "allow", "8080/udp"], check=True)
            subprocess.run(["sudo", "ufw", "allow", "8081/tcp"], check=True)
            subprocess.run(["sudo", "ufw", "reload"], check=True)
        except subprocess.CalledProcessError:
            # Fallback to iptables
            subprocess.run([
                "sudo", "iptables", "-A", "INPUT", "-p", "udp", 
                "--dport", "8080", "-j", "ACCEPT"
            ], check=True)
            subprocess.run([
                "sudo", "iptables", "-A", "INPUT", "-p", "tcp", 
                "--dport", "8081", "-j", "ACCEPT"
            ], check=True)
    
    def cleanup_ports(self):
        """Clean up processes using the required ports"""
        reply = QMessageBox.question(
            self, "Cleanup Ports", 
            "This will kill any processes using ports 8080 and 8081.\n"
            "This may affect other applications.\n\n"
            "Continue?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                if self.current_platform == "darwin":
                    # macOS/Linux
                    subprocess.run(["lsof", "-ti:8080"], check=False)
                    subprocess.run(["lsof", "-ti:8081"], check=False)
                    subprocess.run(["kill", "-9", "$(lsof -ti:8080)"], shell=True, check=False)
                    subprocess.run(["kill", "-9", "$(lsof -ti:8081)"], shell=True, check=False)
                else:
                    # Windows
                    subprocess.run([
                        "for", "/f", "tokens=5", "%%a", "in", 
                        "('netstat -aon ^| findstr :8080')", "do", "taskkill", "/f", "/pid", "%%a"
                    ], shell=True, check=False)
                    subprocess.run([
                        "for", "/f", "tokens=5", "%%a", "in", 
                        "('netstat -aon ^| findstr :8081')", "do", "taskkill", "/f", "/pid", "%%a"
                    ], shell=True, check=False)
                
                QMessageBox.information(self, "Success", "Port cleanup completed!")
                self.test_ports()
                
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to cleanup ports: {str(e)}")

