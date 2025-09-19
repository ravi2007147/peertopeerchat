#!/usr/bin/env python3
"""
Peer-to-Peer Chat and File Sharing Application
Built with PyQt5, SQLite, SQLAlchemy, WebSockets, and Cryptography
"""

import sys
import os
import json
import socket
import threading
import asyncio
import websockets
import sqlite3
import uuid
import platform
import time
from datetime import datetime
from typing import Dict, List, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton, QListWidget, QLabel, QSplitter,
    QScrollArea, QFrame, QFileDialog, QMessageBox, QProgressBar,
    QTabWidget, QGroupBox, QGridLayout, QComboBox, QSpinBox,
    QDialog, QAction, QDialogButtonBox, QListWidgetItem, QSystemTrayIcon,
    QMenu, QCheckBox, QSlider
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize, QDateTime
from PyQt5.QtGui import QFont, QPixmap, QIcon, QPalette, QColor

class NotificationSettingsDialog(QDialog):
    """Dialog for notification settings"""
    
    def __init__(self, notification_manager, parent=None):
        super().__init__(parent)
        self.notification_manager = notification_manager
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI"""
        self.setWindowTitle("Notification Settings")
        self.setModal(True)
        self.resize(400, 200)
        
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Notification Settings")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(title_label)
        
        # Enable notifications checkbox
        self.enable_notifications = QCheckBox("Enable desktop notifications")
        self.enable_notifications.setChecked(self.notification_manager.notifications_enabled)
        self.enable_notifications.toggled.connect(self.toggle_notifications)
        layout.addWidget(self.enable_notifications)
        
        # Notification info
        info_label = QLabel("""
Notifications will appear when:
• You receive new messages
• Files are transferred
• The application is in the background

Click on notifications to bring the application to the front.
        """)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def toggle_notifications(self, enabled):
        """Toggle notification settings"""
        self.notification_manager.set_notifications_enabled(enabled)

# Notification Classes
class NotificationManager:
    """Manages desktop notifications and system tray"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.system_tray = None
        self.notifications_enabled = True
        self.init_system_tray()
    
    def init_system_tray(self):
        """Initialize system tray icon"""
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.system_tray = QSystemTrayIcon(self.main_window)
            
            # Create tray icon (using a simple icon for now)
            icon = QIcon()
            # You can replace this with a proper icon file
            pixmap = QPixmap(32, 32)
            pixmap.fill(QColor(100, 150, 200))
            icon.addPixmap(pixmap)
            self.system_tray.setIcon(icon)
            
            # Create context menu
            tray_menu = QMenu()
            
            show_action = QAction("Show", self.main_window)
            show_action.triggered.connect(self.main_window.show)
            tray_menu.addAction(show_action)
            
            quit_action = QAction("Quit", self.main_window)
            quit_action.triggered.connect(self.main_window.close)
            tray_menu.addAction(quit_action)
            
            self.system_tray.setContextMenu(tray_menu)
            self.system_tray.activated.connect(self.tray_icon_activated)
            self.system_tray.show()
    
    def tray_icon_activated(self, reason):
        """Handle system tray icon activation"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.main_window.show()
            self.main_window.raise_()
            self.main_window.activateWindow()
    
    def show_notification(self, title: str, message: str, sender: str = None):
        """Show desktop notification"""
        if not self.notifications_enabled:
            return
            
        if self.system_tray and self.system_tray.isVisible():
            # Show system tray notification
            self.system_tray.showMessage(
                title,
                message,
                QSystemTrayIcon.Information,
                5000  # 5 seconds
            )
        else:
            # Fallback: show message box
            QMessageBox.information(self.main_window, title, message)
    
    def show_message_notification(self, sender: str, message: str, message_type: str = "text"):
        """Show notification for incoming message"""
        if message_type == "text":
            title = f"New message from {sender}"
            preview = message[:50] + "..." if len(message) > 50 else message
        elif message_type == "file":
            title = f"File received from {sender}"
            preview = f"File: {message}"
        elif message_type == "image":
            title = f"Image received from {sender}"
            preview = f"Image: {message}"
        else:
            title = f"Message from {sender}"
            preview = message
        
        self.show_notification(title, preview, sender)
    
    def set_notifications_enabled(self, enabled: bool):
        """Enable or disable notifications"""
        self.notifications_enabled = enabled

# File Transfer Classes
class FileTransfer(QThread):
    """Thread for handling file transfers with progress tracking"""
    progress_updated = pyqtSignal(int, int, str)  # current, total, status
    transfer_completed = pyqtSignal(bool, str)  # success, message
    transfer_paused = pyqtSignal()
    transfer_resumed = pyqtSignal()
    
    def __init__(self, file_path: str, target_ip: str, websocket, transfer_id: str):
        super().__init__()
        self.file_path = file_path
        self.target_ip = target_ip
        self.websocket = websocket
        self.transfer_id = transfer_id
        self.file_size = os.path.getsize(file_path)
        self.chunk_size = 8192  # 8KB chunks
        self.paused = False
        self.cancelled = False
        self.bytes_sent = 0
        
    def run(self):
        """Execute file transfer"""
        try:
            self.progress_updated.emit(0, self.file_size, "Starting transfer...")
            
            with open(self.file_path, 'rb') as file:
                while self.bytes_sent < self.file_size and not self.cancelled:
                    # Check if paused
                    while self.paused and not self.cancelled:
                        self.msleep(100)
                    
                    if self.cancelled:
                        break
                    
                    # Read chunk
                    chunk_size = min(self.chunk_size, self.file_size - self.bytes_sent)
                    chunk = file.read(chunk_size)
                    
                    if not chunk:
                        break
                    
                    # Send chunk via WebSocket
                    message = {
                        'type': 'file_chunk',
                        'transfer_id': self.transfer_id,
                        'chunk_data': base64.b64encode(chunk).decode(),
                        'chunk_index': self.bytes_sent // self.chunk_size,
                        'total_chunks': (self.file_size + self.chunk_size - 1) // self.chunk_size,
                        'file_size': self.file_size,
                        'filename': os.path.basename(self.file_path)
                    }
                    
                    # Send asynchronously
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.websocket.send(json.dumps(message)))
                    loop.close()
                    
                    self.bytes_sent += len(chunk)
                    progress = int((self.bytes_sent / self.file_size) * 100)
                    self.progress_updated.emit(self.bytes_sent, self.file_size, f"Sending... {progress}%")
                    
                    # Small delay to prevent overwhelming the network
                    self.msleep(10)
            
            if not self.cancelled:
                self.transfer_completed.emit(True, "Transfer completed successfully")
            else:
                self.transfer_completed.emit(False, "Transfer cancelled")
                
        except Exception as e:
            self.transfer_completed.emit(False, f"Transfer failed: {str(e)}")
    
    def pause_transfer(self):
        """Pause the transfer"""
        self.paused = True
        self.transfer_paused.emit()
    
    def resume_transfer(self):
        """Resume the transfer"""
        self.paused = False
        self.transfer_resumed.emit()
    
    def cancel_transfer(self):
        """Cancel the transfer"""
        self.cancelled = True

class FileTransferDialog(QDialog):
    """Dialog for showing file transfer progress and controls"""
    
    def __init__(self, file_path: str, target_ip: str, websocket, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.target_ip = target_ip
        self.websocket = websocket
        self.transfer_id = str(uuid.uuid4())
        self.transfer_thread = None
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI"""
        self.setWindowTitle("File Transfer")
        self.setModal(False)
        self.resize(500, 200)
        
        layout = QVBoxLayout()
        
        # File info
        file_info = QLabel(f"File: {os.path.basename(self.file_path)}")
        file_info.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(file_info)
        
        target_info = QLabel(f"To: {self.target_ip}")
        layout.addWidget(target_info)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Preparing transfer...")
        layout.addWidget(self.status_label)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.pause_transfer)
        button_layout.addWidget(self.pause_button)
        
        self.resume_button = QPushButton("Resume")
        self.resume_button.clicked.connect(self.resume_transfer)
        self.resume_button.setEnabled(False)
        button_layout.addWidget(self.resume_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_transfer)
        button_layout.addWidget(self.cancel_button)
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        self.close_button.setEnabled(False)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # Start transfer
        self.start_transfer()
    
    def start_transfer(self):
        """Start the file transfer"""
        self.transfer_thread = FileTransfer(
            self.file_path, self.target_ip, self.websocket, self.transfer_id
        )
        self.transfer_thread.progress_updated.connect(self.update_progress)
        self.transfer_thread.transfer_completed.connect(self.transfer_finished)
        self.transfer_thread.transfer_paused.connect(self.transfer_paused)
        self.transfer_thread.transfer_resumed.connect(self.transfer_resumed)
        self.transfer_thread.start()
    
    def update_progress(self, current: int, total: int, status: str):
        """Update progress bar and status"""
        progress = int((current / total) * 100) if total > 0 else 0
        self.progress_bar.setValue(progress)
        self.status_label.setText(f"{status} ({self.format_bytes(current)} / {self.format_bytes(total)})")
    
    def transfer_paused(self):
        """Handle transfer pause"""
        self.pause_button.setEnabled(False)
        self.resume_button.setEnabled(True)
        self.status_label.setText("Transfer paused")
    
    def transfer_resumed(self):
        """Handle transfer resume"""
        self.pause_button.setEnabled(True)
        self.resume_button.setEnabled(False)
        self.status_label.setText("Transfer resumed")
    
    def transfer_finished(self, success: bool, message: str):
        """Handle transfer completion"""
        self.pause_button.setEnabled(False)
        self.resume_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        self.close_button.setEnabled(True)
        
        if success:
            self.status_label.setText("Transfer completed successfully")
            self.progress_bar.setValue(100)
        else:
            self.status_label.setText(f"Transfer failed: {message}")
    
    def pause_transfer(self):
        """Pause the transfer"""
        if self.transfer_thread:
            self.transfer_thread.pause_transfer()
    
    def resume_transfer(self):
        """Resume the transfer"""
        if self.transfer_thread:
            self.transfer_thread.resume_transfer()
    
    def cancel_transfer(self):
        """Cancel the transfer"""
        if self.transfer_thread:
            self.transfer_thread.cancel_transfer()
        self.close()
    
    def format_bytes(self, bytes_count: int) -> str:
        """Format bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_count < 1024.0:
                return f"{bytes_count:.1f} {unit}"
            bytes_count /= 1024.0
        return f"{bytes_count:.1f} TB"

# Database models
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class FirewallConfigDialog(QDialog):
    """Dialog showing platform-specific firewall configuration instructions"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Firewall Configuration")
        self.setModal(True)
        self.resize(800, 600)
        
        # Set light theme for the dialog
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                color: #000000;
            }
            QLabel {
                color: #000000;
                background-color: transparent;
            }
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QTextEdit {
                background-color: #f8f9fa;
                color: #000000;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 10px;
                font-family: 'Courier New', monospace;
                font-size: 11px;
            }
        """)
        
        # Get platform-specific instructions
        self.platform = platform.system().lower()
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the UI based on platform"""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("🔥 Firewall Configuration Required")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #e74c3c; margin: 10px;")
        layout.addWidget(title)
        
        # Platform info
        platform_label = QLabel(f"Detected Platform: {self.platform.title()}")
        platform_label.setStyleSheet("font-size: 14px; font-weight: bold; margin: 5px;")
        layout.addWidget(platform_label)
        
        # Required ports info
        ports_info = QLabel("Required Ports: UDP 8080 (Discovery), TCP 8081 (WebSocket)")
        ports_info.setStyleSheet("font-size: 12px; color: #2c3e50; margin: 5px;")
        layout.addWidget(ports_info)
        
        # Instructions text area
        self.instructions_text = QTextEdit()
        self.instructions_text.setReadOnly(True)
        self.instructions_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 10px;
                font-family: 'Courier New', monospace;
                font-size: 11px;
            }
        """)
        
        # Set platform-specific instructions
        instructions = self.get_platform_instructions()
        self.instructions_text.setPlainText(instructions)
        layout.addWidget(self.instructions_text)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        # Auto-configure firewall button
        auto_btn = QPushButton("🔧 Auto-Configure Firewall")
        auto_btn.clicked.connect(self.auto_configure_firewall)
        auto_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        
        # Test ports button
        test_btn = QPushButton("🧪 Test Ports")
        test_btn.clicked.connect(self.test_ports)
        test_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        
        # Cleanup ports button
        cleanup_btn = QPushButton("🧹 Cleanup Ports")
        cleanup_btn.clicked.connect(self.cleanup_ports)
        cleanup_btn.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
        """)
        
        # Copy to clipboard button
        copy_btn = QPushButton("📋 Copy Instructions")
        copy_btn.clicked.connect(self.copy_instructions)
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        
        # Close button
        close_btn = QPushButton("✅ Close")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        
        button_layout.addWidget(auto_btn)
        button_layout.addWidget(test_btn)
        button_layout.addWidget(cleanup_btn)
        button_layout.addWidget(copy_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def get_platform_instructions(self):
        """Get platform-specific firewall instructions"""
        if self.platform == "darwin":  # macOS
            return self.get_macos_instructions()
        elif self.platform == "windows":
            return self.get_windows_instructions()
        else:  # Linux
            return self.get_linux_instructions()
            
    def get_macos_instructions(self):
        return """🍎 macOS Firewall Configuration

🔧 AUTOMATIC CONFIGURATION (Recommended):
Click the "Auto-Configure Firewall" button above to automatically configure your firewall. This will:
- Add Python to firewall exceptions
- Allow incoming connections for the application
- Handle all necessary permissions

📋 MANUAL CONFIGURATION:
METHOD 1: System Preferences
1. Open System Preferences → Security & Privacy → Firewall
2. Click the lock to make changes (enter password)
3. Click "Firewall Options..."
4. Add Application: Click "+" and navigate to:
   - Python: /usr/bin/python3
   - Built app: ./dist/PeerToPeerChat
5. Set to "Allow incoming connections"

METHOD 2: Command Line
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/bin/python3
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblock /usr/bin/python3

🧪 TESTING:
# Check what's using ports
lsof -i :8080
lsof -i :8081

# Check firewall status
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate

🔧 TROUBLESHOOTING:
- Try automatic configuration first
- Ensure both UDP 8080 and TCP 8081 are allowed
- Check that no antivirus is blocking network traffic
- Verify both devices are on the same network"""

    def get_windows_instructions(self):
        return """🪟 Windows Firewall Configuration

🔧 AUTOMATIC CONFIGURATION (Recommended):
Click the "Auto-Configure Firewall" button above to automatically configure your firewall. This will:
- Add UDP port 8080 (Discovery) to Windows Defender Firewall
- Add TCP port 8081 (WebSocket) to Windows Defender Firewall
- Handle all necessary permissions

📋 MANUAL CONFIGURATION:
METHOD 1: Windows Defender Firewall
1. Open Windows Defender Firewall
2. Click "Allow an app or feature through Windows Defender Firewall"
3. Click "Change settings" (admin required)
4. Click "Allow another app..."
5. Browse to your Python executable or the built .exe file
6. Check both "Private" and "Public" networks
7. Click "OK"

METHOD 2: Command Line (Run as Administrator)
# Allow specific ports
netsh advfirewall firewall add rule name="P2P Discovery" dir=in action=allow protocol=UDP localport=8080
netsh advfirewall firewall add rule name="P2P WebSocket" dir=in action=allow protocol=TCP localport=8081

🧪 TESTING:
# Check what's using ports
netstat -an | findstr 8080
netstat -an | findstr 8081

# Check firewall rules
netsh advfirewall firewall show rule name="Peer-to-Peer Chat"

🔧 TROUBLESHOOTING:
- Try automatic configuration first
- Run commands as Administrator
- Ensure both UDP 8080 and TCP 8081 are allowed
- Check Windows Defender isn't blocking the application
- Verify both devices are on the same network"""

    def get_linux_instructions(self):
        return """🐧 Linux Firewall Configuration

🔧 AUTOMATIC CONFIGURATION (Recommended):
Click the "Auto-Configure Firewall" button above to automatically configure your firewall. This will:
- Try UFW first (Ubuntu/Debian)
- Fallback to iptables if UFW not available
- Add UDP port 8080 and TCP port 8081
- Handle all necessary permissions

📋 MANUAL CONFIGURATION:
METHOD 1: UFW (Ubuntu/Debian)
# Allow specific ports
sudo ufw allow 8080/udp
sudo ufw allow 8081/tcp

# Enable UFW if not already enabled
sudo ufw enable

METHOD 2: iptables
# Allow UDP port 8080
sudo iptables -A INPUT -p udp --dport 8080 -j ACCEPT

# Allow TCP port 8081
sudo iptables -A INPUT -p tcp --dport 8081 -j ACCEPT

# Save rules (Ubuntu/Debian)
sudo iptables-save > /etc/iptables/rules.v4

METHOD 3: firewalld (CentOS/RHEL/Fedora)
# Allow specific ports
sudo firewall-cmd --permanent --add-port=8080/udp
sudo firewall-cmd --permanent --add-port=8081/tcp

# Reload firewall
sudo firewall-cmd --reload

🧪 TESTING:
# Check what's using ports
sudo netstat -tulpn | grep :8080
sudo netstat -tulpn | grep :8081

# Check UFW status
sudo ufw status

# Check iptables rules
sudo iptables -L

🔧 TROUBLESHOOTING:
- Try automatic configuration first
- Ensure both UDP 8080 and TCP 8081 are allowed
- Check SELinux isn't blocking network access
- Verify both devices are on the same network
- Check system logs: sudo journalctl -f"""

    def copy_instructions(self):
        """Copy instructions to clipboard"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.instructions_text.toPlainText())
        QMessageBox.information(self, "Copied", "Instructions copied to clipboard!")
        
    def cleanup_ports(self):
        """Clean up processes using ports 8080 and 8081"""
        import subprocess
        
        # Ask for confirmation
        reply = QMessageBox.question(
            self, 
            "Cleanup Ports", 
            "Kill all processes using ports 8080 and 8081?\n\nThis will:\n- Kill any processes using UDP port 8080\n- Kill any processes using TCP port 8081\n- Free up ports for Peer-to-Peer Chat\n\nNote: This may close other applications using these ports.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
            
        try:
            killed_processes = []
            
            # Kill processes using port 8080
            try:
                result = subprocess.run(['lsof', '-ti', ':8080'], capture_output=True, text=True, timeout=10)
                if result.returncode == 0 and result.stdout.strip():
                    pids = result.stdout.strip().split('\n')
                    for pid in pids:
                        if pid.strip():
                            subprocess.run(['kill', '-9', pid.strip()], timeout=5)
                            killed_processes.append(f"Port 8080: PID {pid.strip()}")
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                pass
            
            # Kill processes using port 8081
            try:
                result = subprocess.run(['lsof', '-ti', ':8081'], capture_output=True, text=True, timeout=10)
                if result.returncode == 0 and result.stdout.strip():
                    pids = result.stdout.strip().split('\n')
                    for pid in pids:
                        if pid.strip():
                            subprocess.run(['kill', '-9', pid.strip()], timeout=5)
                            killed_processes.append(f"Port 8081: PID {pid.strip()}")
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                pass
            
            if killed_processes:
                QMessageBox.information(
                    self, 
                    "Ports Cleaned Up", 
                    f"Successfully killed processes:\n\n" + "\n".join(killed_processes) + "\n\nPorts 8080 and 8081 are now available!"
                )
            else:
                QMessageBox.information(
                    self, 
                    "No Processes Found", 
                    "No processes were found using ports 8080 or 8081.\n\nBoth ports are already available!"
                )
                
            # Test ports after cleanup
            self.test_ports()
            
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Cleanup Failed", 
                f"Failed to cleanup ports:\n\n{str(e)}\n\nPlease try manual cleanup or restart your system."
            )
        
    def auto_configure_firewall(self):
        """Automatically configure firewall for the current platform"""
        import subprocess
        import sys
        
        # Ask for confirmation
        reply = QMessageBox.question(
            self, 
            "Auto-Configure Firewall", 
            f"Automatically configure firewall for {self.platform.title()}?\n\nThis will attempt to:\n- Allow UDP port 8080 (Discovery)\n- Allow TCP port 8081 (WebSocket)\n\nNote: This may require administrator/sudo privileges.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply != QMessageBox.Yes:
            return
            
        try:
            if self.platform == "darwin":  # macOS
                self.configure_macos_firewall()
            elif self.platform == "windows":
                self.configure_windows_firewall()
            else:  # Linux
                self.configure_linux_firewall()
                
            # Test ports after configuration
            self.test_ports()
            
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Configuration Failed", 
                f"Failed to configure firewall automatically:\n\n{str(e)}\n\nPlease use manual configuration instead."
            )
    
    def configure_macos_firewall(self):
        """Configure macOS firewall"""
        import subprocess
        
        # Try to add Python to firewall exceptions
        try:
            # Get Python executable path
            python_path = sys.executable
            
            # Add Python to firewall
            result = subprocess.run([
                'sudo', '/usr/libexec/ApplicationFirewall/socketfilterfw', 
                '--add', python_path
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("✅ Added Python to macOS firewall")
            else:
                print(f"⚠️  Firewall add result: {result.stderr}")
                
            # Unblock Python
            result = subprocess.run([
                'sudo', '/usr/libexec/ApplicationFirewall/socketfilterfw', 
                '--unblock', python_path
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("✅ Unblocked Python in macOS firewall")
            else:
                print(f"⚠️  Firewall unblock result: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            raise Exception("Firewall configuration timed out. Please run manually.")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Firewall configuration failed: {e.stderr}")
        except FileNotFoundError:
            raise Exception("macOS firewall tools not found. Please configure manually.")
    
    def configure_windows_firewall(self):
        """Configure Windows firewall"""
        import subprocess
        
        try:
            # Allow UDP port 8080
            result = subprocess.run([
                'netsh', 'advfirewall', 'firewall', 'add', 'rule',
                'name=P2P Discovery', 'dir=in', 'action=allow', 
                'protocol=UDP', 'localport=8080'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("✅ Added UDP port 8080 to Windows firewall")
            else:
                print(f"⚠️  UDP rule result: {result.stderr}")
            
            # Allow TCP port 8081
            result = subprocess.run([
                'netsh', 'advfirewall', 'firewall', 'add', 'rule',
                'name=P2P WebSocket', 'dir=in', 'action=allow', 
                'protocol=TCP', 'localport=8081'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("✅ Added TCP port 8081 to Windows firewall")
            else:
                print(f"⚠️  TCP rule result: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            raise Exception("Firewall configuration timed out. Please run manually.")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Firewall configuration failed: {e.stderr}")
        except FileNotFoundError:
            raise Exception("Windows netsh not found. Please configure manually.")
    
    def configure_linux_firewall(self):
        """Configure Linux firewall"""
        import subprocess
        
        try:
            # Try UFW first (Ubuntu/Debian)
            try:
                # Allow UDP port 8080
                result = subprocess.run([
                    'sudo', 'ufw', 'allow', '8080/udp'
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    print("✅ Added UDP port 8080 to UFW")
                else:
                    print(f"⚠️  UFW UDP result: {result.stderr}")
                
                # Allow TCP port 8081
                result = subprocess.run([
                    'sudo', 'ufw', 'allow', '8081/tcp'
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    print("✅ Added TCP port 8081 to UFW")
                else:
                    print(f"⚠️  UFW TCP result: {result.stderr}")
                    
            except FileNotFoundError:
                # Try iptables
                print("UFW not found, trying iptables...")
                
                # Allow UDP port 8080
                result = subprocess.run([
                    'sudo', 'iptables', '-A', 'INPUT', '-p', 'udp', 
                    '--dport', '8080', '-j', 'ACCEPT'
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    print("✅ Added UDP port 8080 to iptables")
                else:
                    print(f"⚠️  iptables UDP result: {result.stderr}")
                
                # Allow TCP port 8081
                result = subprocess.run([
                    'sudo', 'iptables', '-A', 'INPUT', '-p', 'tcp', 
                    '--dport', '8081', '-j', 'ACCEPT'
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    print("✅ Added TCP port 8081 to iptables")
                else:
                    print(f"⚠️  iptables TCP result: {result.stderr}")
                    
        except subprocess.TimeoutExpired:
            raise Exception("Firewall configuration timed out. Please run manually.")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Firewall configuration failed: {e.stderr}")
        except FileNotFoundError:
            raise Exception("Linux firewall tools not found. Please configure manually.")
        
    def test_ports(self):
        """Test if ports are available"""
        import subprocess
        
        # Test UDP port 8080
        udp_result = self.test_udp_port(8080)
        # Test TCP port 8081
        tcp_result = self.test_tcp_port(8081)
        
        result_text = f"""Port Test Results:

UDP Port 8080 (Discovery): {udp_result}
TCP Port 8081 (WebSocket): {tcp_result}

If ports show as "IN USE", you need to:
1. Close the application using those ports
2. Configure firewall to allow these ports
3. Restart the application"""
        
        QMessageBox.information(self, "Port Test Results", result_text)
        
    def test_udp_port(self, port):
        """Test if UDP port is available"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind(('', port))
            sock.close()
            return "✅ Available"
        except OSError:
            return "❌ IN USE"
            
    def test_tcp_port(self, port):
        """Test if TCP port is available"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('', port))
            sock.close()
            return "✅ Available"
        except OSError:
            return "❌ IN USE"

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    uuid = Column(String(36), unique=True, nullable=False)  # UUID string
    ip_address = Column(String(15), nullable=False)
    username = Column(String(50), nullable=False)
    last_seen = Column(DateTime, default=datetime.utcnow)
    is_online = Column(Boolean, default=False)
    first_seen = Column(DateTime, default=datetime.utcnow)

class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    sender_ip = Column(String(15), nullable=False)
    receiver_ip = Column(String(15), nullable=False)
    message_type = Column(String(20), nullable=False)  # text, image, file
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_encrypted = Column(Boolean, default=True)

class CurrentUser(Base):
    __tablename__ = 'current_user'
    id = Column(Integer, primary_key=True)
    uuid = Column(String(36), unique=True, nullable=False)
    username = Column(String(50), nullable=False)
    current_ip = Column(String(15), nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow)

class PeerDiscovery(QThread):
    """Thread for discovering peers on LAN"""
    peer_found = pyqtSignal(str, str, str)  # ip, username, uuid
    peer_lost = pyqtSignal(str)
    port_error = pyqtSignal(str)  # port error message

    def __init__(self, current_user_uuid=None, current_username=None, discovery_port=8080):
        super().__init__()
        self.running = True
        self.discovered_peers = {}
        self.current_user_uuid = current_user_uuid
        self.current_username = current_username
        self.discovery_port = discovery_port

    def run(self):
        print("🚀 PeerDiscovery thread started")
        # Launch broadcast in a background thread
        threading.Thread(target=self.broadcast_presence, daemon=True).start()
        # Launch listener in another background thread
        threading.Thread(target=self.listen_for_peers, daemon=True).start()
        # Keep QThread alive
        while self.running:
            self.msleep(200)

    def broadcast_presence(self):
        """Broadcast our presence on LAN"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        message = json.dumps({
            'type': 'peer_announcement',
            'username': self.current_username or socket.gethostname(),
            'uuid': self.current_user_uuid,
            'port': 8081,
            'discovery_port': self.discovery_port
        })

        try:
            while self.running:
                try:
                    sock.sendto(message.encode(), ('255.255.255.255', self.discovery_port))
                    print(f"📡 Broadcasting presence on {self.discovery_port}")
                except Exception as e:
                    print(f"❌ Broadcast failed: {e}")
                for _ in range(50):  # ~5 seconds
                    if not self.running:
                        break
                    time.sleep(0.1)
        finally:
            sock.close()

    def listen_for_peers(self):
        """Listen for peer announcements"""
        print("👂 Starting listener...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            sock.bind(('', self.discovery_port))
            print(f"✅ Listening for peers on port {self.discovery_port}")
        except OSError as e:
            print(f"❌ Could not bind port {self.discovery_port}: {e}")
            self.port_error.emit(f"Port {self.discovery_port} already in use.\n\n{e}")
            return

        sock.settimeout(1.0)
        try:
            while self.running:
                try:
                    data, addr = sock.recvfrom(1024)
                    peer_info = json.loads(data.decode())
                    print(f"📥 Received from {addr}: {peer_info}")

                    if peer_info['type'] == 'peer_announcement':
                        ip = addr[0]
                        username = peer_info['username']
                        peer_uuid = peer_info.get('uuid', 'unknown')

                        if peer_uuid != self.current_user_uuid:
                            if ip not in self.discovered_peers:
                                self.discovered_peers[ip] = {'username': username, 'uuid': peer_uuid}
                                print(f"👋 Found peer: {username} ({ip}) UUID={peer_uuid}")
                                self.peer_found.emit(ip, username, peer_uuid)
                            else:
                                self.discovered_peers[ip].update({'username': username, 'uuid': peer_uuid})
                        else:
                            print("🚫 Ignored self-announcement")
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"Listen error: {e}")
                    break
        finally:
            sock.close()

    def stop(self):
        """Stop discovery cleanly"""
        print("🛑 Stopping peer discovery...")
        self.running = False
        self.wait(500)


class WebSocketServer(QThread):
    """WebSocket server for peer-to-peer communication"""
    message_received = pyqtSignal(str, str, str)  # sender_ip, message_type, content
    port_error = pyqtSignal(str)  # port error message
    
    def __init__(self, port=8081):
        super().__init__()
        self.port = port
        self.clients = {}
        self.running = True
        self.server = None
        self.active_transfers = {}  # Store active file transfers
        
    def find_available_port(self, start_port):
        """Find an available port starting from start_port"""
        import socket
        port = start_port
        while port < start_port + 100:  # Try up to 100 ports
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.bind(('', port))
                sock.close()
                return port
            except OSError:
                port += 1
        return start_port  # Fallback to original port
        
    async def handle_client(self, websocket, path):
        """Handle incoming WebSocket connections"""
        client_ip = websocket.remote_address[0]
        self.clients[client_ip] = websocket
        
        try:
            async for message in websocket:
                data = json.loads(message)
                
                # Handle different message types
                if data['type'] == 'file_chunk':
                    await self.handle_file_chunk(client_ip, data)
                else:
                    # Handle regular messages
                    self.message_received.emit(client_ip, data['type'], data['content'])
                    
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            if client_ip in self.clients:
                del self.clients[client_ip]
    
    async def handle_file_chunk(self, client_ip: str, data: dict):
        """Handle incoming file chunks"""
        transfer_id = data['transfer_id']
        chunk_data = base64.b64decode(data['chunk_data'])
        chunk_index = data['chunk_index']
        total_chunks = data['total_chunks']
        filename = data['filename']
        
        # Initialize transfer if first chunk
        if transfer_id not in self.active_transfers:
            self.active_transfers[transfer_id] = {
                'filename': filename,
                'sender_ip': client_ip,
                'chunks': {},
                'total_chunks': total_chunks,
                'file_size': data['file_size']
            }
        
        # Store chunk
        self.active_transfers[transfer_id]['chunks'][chunk_index] = chunk_data
        
        # Check if all chunks received
        if len(self.active_transfers[transfer_id]['chunks']) == total_chunks:
            await self.complete_file_transfer(transfer_id)
    
    async def complete_file_transfer(self, transfer_id: str):
        """Complete file transfer by assembling chunks"""
        transfer = self.active_transfers[transfer_id]
        filename = transfer['filename']
        sender_ip = transfer['sender_ip']
        
        try:
            # Create downloads directory if it doesn't exist
            downloads_dir = os.path.join(os.path.expanduser("~"), "Downloads", "PeerToPeerChat")
            os.makedirs(downloads_dir, exist_ok=True)
            
            # Assemble file
            file_path = os.path.join(downloads_dir, filename)
            with open(file_path, 'wb') as f:
                for i in range(transfer['total_chunks']):
                    if i in transfer['chunks']:
                        f.write(transfer['chunks'][i])
            
            # Notify about completed file
            self.message_received.emit(sender_ip, 'file_completed', filename)
            print(f"✅ File transfer completed: {filename} from {sender_ip}")
            
        except Exception as e:
            print(f"❌ Error completing file transfer: {e}")
            self.message_received.emit(sender_ip, 'file_error', str(e))
        finally:
            # Clean up transfer
            del self.active_transfers[transfer_id]
                
    async def start_server(self):
        """Start the WebSocket server"""
        try:
            self.server = await websockets.serve(self.handle_client, "0.0.0.0", self.port)
            print(f"✅ WebSocket server started on port {self.port}")
            
            # Wait for server to be closed
            await self.server.wait_closed()
        except OSError as e:
            print(f"❌ Port {self.port} is already in use!")
            print(f"❌ Error: {e}")
            print(f"💡 Please close the application using port {self.port} and try again.")
            # Emit error signal to main window
            self.port_error.emit(f"Port {self.port} is already in use by another application.\n\nPlease close the application using this port and try again.")
            return
        
    def run(self):
        """Run the WebSocket server"""
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.start_server())
        except Exception as e:
            print(f"WebSocket server error: {e}")
        finally:
            print("WebSocket server stopped")
        
    def stop(self):
        """Stop the WebSocket server"""
        print("Stopping WebSocket server...")
        self.running = False
        if self.server:
            # Close all client connections
            for client in self.clients.values():
                try:
                    asyncio.create_task(client.close())
                except:
                    pass
            # Close the server
            try:
                asyncio.create_task(self.server.close())
            except:
                pass
            # Clear clients
            self.clients.clear()
        
    def send_message(self, target_ip: str, message_type: str, content: str):
        """Send message to specific peer"""
        if target_ip in self.clients:
            message = json.dumps({
                'type': message_type,
                'content': content,
                'timestamp': datetime.utcnow().isoformat()
            })
            asyncio.create_task(self.clients[target_ip].send(message))

class ChatWidget(QWidget):
    """Chat interface widget"""
    def __init__(self):
        super().__init__()
        self.current_peer = None
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Chat header
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.StyledPanel)
        header_layout = QHBoxLayout()
        
        self.peer_label = QLabel("Select a peer to start chatting")
        self.peer_label.setFont(QFont("Arial", 12, QFont.Bold))
        header_layout.addWidget(self.peer_label)
        
        header_layout.addStretch()
        
        self.file_button = QPushButton("📁 Send File")
        self.file_button.clicked.connect(self.send_file)
        header_layout.addWidget(self.file_button)
        
        self.image_button = QPushButton("🖼️ Send Image")
        self.image_button.clicked.connect(self.send_image)
        header_layout.addWidget(self.image_button)
        
        header_frame.setLayout(header_layout)
        layout.addWidget(header_frame)
        
        # Chat messages area
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.setFont(QFont("Arial", 10))
        layout.addWidget(self.chat_area)
        
        # Message input area
        input_frame = QFrame()
        input_layout = QHBoxLayout()
        
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type your message...")
        self.message_input.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.message_input)
        
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)
        
        input_frame.setLayout(input_layout)
        layout.addWidget(input_frame)
        
        self.setLayout(layout)
        
    def set_current_peer(self, peer_ip: str, peer_name: str):
        """Set the current peer for chat"""
        self.current_peer = peer_ip
        self.peer_label.setText(f"Chatting with {peer_name} ({peer_ip})")
        self.load_chat_history(peer_ip)
        
    def add_message(self, sender: str, message: str, message_type: str = "text", timestamp: str = None):
        """Add message to chat area with timestamp"""
        if timestamp:
            try:
                # Parse ISO timestamp
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                formatted_time = dt.strftime("%H:%M:%S")
            except:
                formatted_time = datetime.now().strftime("%H:%M:%S")
        else:
            formatted_time = datetime.now().strftime("%H:%M:%S")
        
        if message_type == "text":
            self.chat_area.append(f"[{formatted_time}] {sender}: {message}")
        elif message_type == "image":
            self.chat_area.append(f"[{formatted_time}] {sender}: [Image: {message}]")
        elif message_type == "file":
            self.chat_area.append(f"[{formatted_time}] {sender}: [File: {message}]")
            
        # Auto-scroll to bottom
        scrollbar = self.chat_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def send_message(self):
        """Send text message"""
        if not self.current_peer:
            return
            
        message = self.message_input.text().strip()
        if message:
            self.add_message("You", message)
            # Send message via WebSocket
            main_window = self.parent()
            if hasattr(main_window, 'send_message_to_peer'):
                success = main_window.send_message_to_peer(self.current_peer, "text", message)
                if not success:
                    self.add_message("System", "Failed to send message - no connection to peer")
            self.message_input.clear()
            
    def send_file(self):
        """Send file to current peer"""
        if not self.current_peer:
            QMessageBox.warning(self, "No Peer", "Please select a peer first")
            return
            
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File to Send")
        if file_path:
            filename = os.path.basename(file_path)
            self.add_message("You", filename, "file")
            
            # Get main window and WebSocket connection
            main_window = self.parent()
            if hasattr(main_window, 'websocket_clients') and self.current_peer in main_window.websocket_clients:
                websocket = main_window.websocket_clients[self.current_peer]
                
                # Show file transfer dialog
                transfer_dialog = FileTransferDialog(file_path, self.current_peer, websocket, main_window)
                transfer_dialog.show()
            else:
                self.add_message("System", "No connection to peer - cannot send file")
            
    def send_image(self):
        """Send image to current peer"""
        if not self.current_peer:
            QMessageBox.warning(self, "No Peer", "Please select a peer first")
            return
            
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "", "Image Files (*.png *.jpg *.jpeg *.gif *.bmp)"
        )
        if file_path:
            filename = os.path.basename(file_path)
            self.add_message("You", filename, "image")
            
            # Send image info via WebSocket
            main_window = self.parent()
            if hasattr(main_window, 'send_message_to_peer'):
                success = main_window.send_message_to_peer(self.current_peer, "image", filename)
                if not success:
                    self.add_message("System", "Failed to send image info - no connection to peer")
            
    def load_chat_history(self, peer_ip: str):
        """Load chat history with peer"""
        self.chat_area.clear()
        # TODO: Load from database
        self.chat_area.append(f"Chat history with {peer_ip}")

class PeerListWidget(QWidget):
    """Widget showing available peers"""
    peer_selected = pyqtSignal(str, str, str)  # ip, username, uuid
    
    def __init__(self):
        super().__init__()
        self.peer_data = {}  # Store peer data by IP
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Header
        header_label = QLabel("Available Peers")
        header_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(header_label)
        
        # Peer list
        self.peer_list = QListWidget()
        self.peer_list.itemClicked.connect(self.on_peer_selected)
        layout.addWidget(self.peer_list)
        
        # Status info
        self.status_label = QLabel("Scanning for peers...")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        
    def add_peer(self, ip: str, username: str, peer_uuid: str):
        """Add peer to list"""
        # Store peer data
        self.peer_data[ip] = {'username': username, 'uuid': peer_uuid}
        
        # Check if peer already exists
        for i in range(self.peer_list.count()):
            item = self.peer_list.item(i)
            if item.text().endswith(f"({ip})"):
                self.peer_list.takeItem(i)
                break
                
        item_text = f"{username} ({ip})"
        self.peer_list.addItem(item_text)
        self.status_label.setText(f"Found {self.peer_list.count()} peer(s)")
        
    def remove_peer(self, ip: str):
        """Remove peer from list"""
        # Remove from stored data
        if ip in self.peer_data:
            del self.peer_data[ip]
            
        for i in range(self.peer_list.count()):
            item = self.peer_list.item(i)
            if item.text().endswith(f"({ip})"):
                self.peer_list.takeItem(i)
                break
                
        self.status_label.setText(f"Found {self.peer_list.count()} peer(s)")
        
    def on_peer_selected(self, item):
        """Handle peer selection"""
        text = item.text()
        # Extract IP from text like "username (192.168.1.100)"
        ip = text.split("(")[-1].rstrip(")")
        username = text.split(" (")[0]
        
        # Get UUID from stored data
        peer_uuid = self.peer_data.get(ip, {}).get('uuid', 'unknown')
        self.peer_selected.emit(ip, username, peer_uuid)

class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.current_user_uuid = None
        self.current_username = None
        self.db_session = None
        self.discovery_thread = None
        self.websocket_server = None
        self.websocket_clients = {}  # Store WebSocket client connections
        self.file_transfers = {}  # Store active file transfers
        self.transfer_queue = []  # Queue for pending transfers
        self.notification_manager = None  # Will be initialized after UI
        self.init_ui()
        self.init_database()
        self.start_services()
        self.init_notifications()
        
    def init_ui(self):
        self.setWindowTitle("Peer-to-Peer Chat & File Sharing")
        self.setGeometry(100, 100, 1200, 800)
        
        # Set modern dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QPushButton {
                background-color: #404040;
                border: 1px solid #555555;
                padding: 8px;
                border-radius: 4px;
                color: #ffffff;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:pressed {
                background-color: #353535;
            }
            QLineEdit {
                background-color: #404040;
                border: 1px solid #555555;
                padding: 8px;
                border-radius: 4px;
                color: #ffffff;
            }
            QTextEdit {
                background-color: #404040;
                border: 1px solid #555555;
                border-radius: 4px;
                color: #ffffff;
            }
            QListWidget {
                background-color: #404040;
                border: 1px solid #555555;
                border-radius: 4px;
                color: #ffffff;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #555555;
            }
            QListWidget::item:selected {
                background-color: #505050;
            }
            QLabel {
                color: #ffffff;
            }
            QFrame {
                background-color: #404040;
                border: 1px solid #555555;
                border-radius: 4px;
            }
        """)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout()
        
        # Splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - Peer list
        self.peer_widget = PeerListWidget()
        self.peer_widget.peer_selected.connect(self.on_peer_selected)
        splitter.addWidget(self.peer_widget)
        
        # Right panel - Chat
        self.chat_widget = ChatWidget()
        splitter.addWidget(self.chat_widget)
        
        # Set splitter proportions (30% peers, 70% chat)
        splitter.setSizes([360, 840])
        
        main_layout.addWidget(splitter)
        central_widget.setLayout(main_layout)
        
        # Status bar
        self.statusBar().showMessage("Ready - Scanning for peers...")
        
        # Create toolbar with firewall configuration
        self.create_toolbar()
        
    def init_database(self):
        """Initialize SQLite database"""
        self.engine = create_engine('sqlite:///peer_chat.db', echo=False)
        
        # Check if database exists and handle migration
        self.handle_database_migration()
        
        # Create all tables
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.db_session = Session()
        
        # Initialize or update current user
        self.current_user_uuid, self.current_username = self.get_or_create_user()
        
    def create_toolbar(self):
        """Create toolbar with firewall configuration icon"""
        toolbar = self.addToolBar("Main")
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        
        # Firewall configuration action
        firewall_action = QAction("🔥 Firewall Config", self)
        firewall_action.setToolTip("Show firewall configuration instructions")
        firewall_action.triggered.connect(self.show_firewall_config)
        
        # Add icon (using emoji as fallback)
        firewall_action.setText("🔥 Firewall Config")
        
        toolbar.addAction(firewall_action)
        
        # Add separator
        toolbar.addSeparator()
        
        # Settings action
        settings_action = QAction("⚙️ Settings", self)
        settings_action.setToolTip("Application settings")
        settings_action.triggered.connect(self.show_settings)
        toolbar.addAction(settings_action)
        
        # Notification settings action
        notification_action = QAction("🔔 Notifications", self)
        notification_action.setToolTip("Notification settings")
        notification_action.triggered.connect(self.show_notification_settings)
        toolbar.addAction(notification_action)
        
        # About action
        about_action = QAction("ℹ️ About", self)
        about_action.setToolTip("About this application")
        about_action.triggered.connect(self.show_about)
        toolbar.addAction(about_action)
        
    def show_firewall_config(self):
        """Show firewall configuration dialog"""
        dialog = FirewallConfigDialog(self)
        dialog.exec_()
        
    def handle_database_migration(self):
        """Handle database schema migration"""
        try:
            # Check if old database exists
            if os.path.exists('peer_chat.db'):
                # Connect to existing database
                conn = sqlite3.connect('peer_chat.db')
                cursor = conn.cursor()
                
                # Check if users table exists and has uuid column
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
                if cursor.fetchone():
                    cursor.execute("PRAGMA table_info(users)")
                    columns = [column[1] for column in cursor.fetchall()]
                    
                    if 'uuid' not in columns:
                        print("Migrating database schema...")
                        
                        # Create backup
                        import shutil
                        shutil.copy('peer_chat.db', 'peer_chat_backup.db')
                        print("Database backed up as peer_chat_backup.db")
                        
                        # Drop old tables to recreate with new schema
                        cursor.execute("DROP TABLE IF EXISTS users")
                        cursor.execute("DROP TABLE IF EXISTS messages")
                        
                        # Commit changes
                        conn.commit()
                        conn.close()
                        
                        print("Database migration completed - old schema removed")
                    else:
                        conn.close()
                        print("Database schema is up to date")
                else:
                    conn.close()
                    print("No existing database found, will create new one")
                    
        except Exception as e:
            print(f"Database migration error: {e}")
            # If migration fails, remove the database and start fresh
            if os.path.exists('peer_chat.db'):
                try:
                    os.remove('peer_chat.db')
                    print("Removed corrupted database, will create new one")
                except Exception as remove_error:
                    print(f"Could not remove corrupted database: {remove_error}")
        
    def get_or_create_user(self):
        """Get existing user or create new one with UUID"""
        # Get current IP address
        current_ip = self.get_local_ip()
        username = socket.gethostname()
        
        # Check if we have a current user record
        current_user = self.db_session.query(CurrentUser).first()
        
        if current_user:
            # Update IP if it changed
            if current_user.current_ip != current_ip:
                print(f"IP changed from {current_user.current_ip} to {current_ip}")
                current_user.current_ip = current_ip
                current_user.last_updated = datetime.utcnow()
                self.db_session.commit()
            
            return current_user.uuid, current_user.username
        else:
            # Create new user with UUID
            user_uuid = str(uuid.uuid4())
            print(f"Creating new user with UUID: {user_uuid}")
            
            # Create current user record
            current_user = CurrentUser(
                uuid=user_uuid,
                username=username,
                current_ip=current_ip
            )
            self.db_session.add(current_user)
            
            # Create user record in users table
            user_record = User(
                uuid=user_uuid,
                ip_address=current_ip,
                username=username,
                is_online=True
            )
            self.db_session.add(user_record)
            self.db_session.commit()
            
            return user_uuid, username
    
    def get_local_ip(self):
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
                import platform
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
        
    def start_services(self):
        """Start peer discovery and WebSocket server"""
        # Start peer discovery
        self.discovery_thread = PeerDiscovery(
            current_user_uuid=self.current_user_uuid,
            current_username=self.current_username
        )
        self.discovery_thread.peer_found.connect(self.peer_widget.add_peer)
        self.discovery_thread.peer_lost.connect(self.peer_widget.remove_peer)
        self.discovery_thread.port_error.connect(self.handle_port_error)
        self.discovery_thread.start()
        
        # Start WebSocket server
        self.websocket_server = WebSocketServer()
        self.websocket_server.message_received.connect(self.handle_message)
        self.websocket_server.port_error.connect(self.handle_websocket_port_error)
        self.websocket_server.start()
        
    def init_notifications(self):
        """Initialize notification system"""
        self.notification_manager = NotificationManager(self)
        
    def on_peer_selected(self, ip: str, username: str, peer_uuid: str):
        """Handle peer selection"""
        self.chat_widget.set_current_peer(ip, username)
        self.statusBar().showMessage(f"Connecting to {username} ({ip})...")
        
        # Update user record in database
        self.update_peer_in_database(ip, username, peer_uuid)
        
        # Establish WebSocket connection to peer
        threading.Thread(target=self.connect_to_peer_sync, args=(ip,), daemon=True).start()
        
    def connect_to_peer_sync(self, peer_ip: str, port: int = 8081):
        """Synchronous wrapper for WebSocket connection"""
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.connect_to_peer(peer_ip, port))
        except Exception as e:
            print(f"❌ Error in connect_to_peer_sync: {e}")
        finally:
            loop.close()
        
    async def connect_to_peer(self, peer_ip: str, port: int = 8081):
        """Establish WebSocket connection to a peer"""
        uri = f"ws://{peer_ip}:{port}"
        try:
            print(f"🔗 Connecting to peer WebSocket at {uri}")
            websocket = await websockets.connect(uri)
            self.websocket_clients[peer_ip] = websocket
            print(f"✅ Connected to peer WebSocket at {uri}")
            
            # Update status bar
            self.statusBar().showMessage(f"Connected to peer at {peer_ip}")
            
            # Start listening for messages from this peer
            asyncio.create_task(self.listen_to_peer(peer_ip, websocket))
            
        except Exception as e:
            print(f"❌ Failed to connect to peer {uri}: {e}")
            self.statusBar().showMessage(f"Failed to connect to {peer_ip}: {str(e)}")
            # Remove from clients if connection failed
            if peer_ip in self.websocket_clients:
                del self.websocket_clients[peer_ip]
    
    async def listen_to_peer(self, peer_ip: str, websocket):
        """Listen for messages from a specific peer"""
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    print(f"📨 Received from {peer_ip}: {data}")
                    
                    # Handle different message types
                    sender_name = self.get_peer_username(peer_ip)
                    timestamp = data.get('timestamp', datetime.utcnow().isoformat())
                    
                    if data['type'] == 'text':
                        self.chat_widget.add_message(
                            sender_name, 
                            data['content'], 
                            'text',
                            timestamp
                        )
                        # Show notification if app is not in focus
                        if self.notification_manager and not self.isActiveWindow():
                            self.notification_manager.show_message_notification(
                                sender_name, data['content'], 'text'
                            )
                    elif data['type'] == 'file':
                        self.chat_widget.add_message(
                            sender_name, 
                            data['content'], 
                            'file',
                            timestamp
                        )
                        if self.notification_manager and not self.isActiveWindow():
                            self.notification_manager.show_message_notification(
                                sender_name, data['content'], 'file'
                            )
                    elif data['type'] == 'image':
                        self.chat_widget.add_message(
                            sender_name, 
                            data['content'], 
                            'image',
                            timestamp
                        )
                        if self.notification_manager and not self.isActiveWindow():
                            self.notification_manager.show_message_notification(
                                sender_name, data['content'], 'image'
                            )
                    elif data['type'] == 'file_completed':
                        self.chat_widget.add_message(
                            sender_name, 
                            f"File received: {data['content']}", 
                            'file',
                            timestamp
                        )
                        if self.notification_manager and not self.isActiveWindow():
                            self.notification_manager.show_message_notification(
                                sender_name, f"File received: {data['content']}", 'file'
                            )
                    elif data['type'] == 'file_error':
                        self.chat_widget.add_message(
                            "System", 
                            f"File transfer error: {data['content']}", 
                            'text',
                            timestamp
                        )
                        
                except json.JSONDecodeError as e:
                    print(f"❌ Failed to parse message from {peer_ip}: {e}")
                except Exception as e:
                    print(f"❌ Error handling message from {peer_ip}: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            print(f"🔌 Connection to {peer_ip} closed")
        except Exception as e:
            print(f"❌ Error listening to {peer_ip}: {e}")
        finally:
            # Clean up connection
            if peer_ip in self.websocket_clients:
                del self.websocket_clients[peer_ip]
            self.statusBar().showMessage(f"Disconnected from {peer_ip}")
    
    def get_peer_username(self, peer_ip: str) -> str:
        """Get username for a peer IP"""
        for i in range(self.peer_widget.peer_list.count()):
            item = self.peer_widget.peer_list.item(i)
            if item.text().endswith(f"({peer_ip})"):
                return item.text().split(" (")[0]
        return "Unknown"
    
    def send_message_to_peer(self, peer_ip: str, message_type: str, content: str):
        """Send message to a specific peer via WebSocket"""
        if peer_ip not in self.websocket_clients:
            print(f"⚠️ No WebSocket connection to {peer_ip}")
            self.statusBar().showMessage(f"No connection to {peer_ip}")
            return False
            
        try:
            message = json.dumps({
                'type': message_type,
                'content': content,
                'timestamp': datetime.utcnow().isoformat(),
                'sender': self.current_username
            })
            
            # Send message asynchronously in a new thread
            def send_async():
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    websocket = self.websocket_clients[peer_ip]
                    loop.run_until_complete(websocket.send(message))
                    print(f"📤 Sent {message_type} to {peer_ip}: {content}")
                    loop.close()
                except Exception as e:
                    print(f"❌ Failed to send message to {peer_ip}: {e}")
            
            threading.Thread(target=send_async, daemon=True).start()
            return True
            
        except Exception as e:
            print(f"❌ Failed to send message to {peer_ip}: {e}")
            self.statusBar().showMessage(f"Failed to send message to {peer_ip}")
            return False
    
    def handle_file_transfer_error(self, transfer_id: str, error_message: str):
        """Handle file transfer errors and attempt recovery"""
        if transfer_id in self.file_transfers:
            transfer_info = self.file_transfers[transfer_id]
            print(f"❌ File transfer error for {transfer_info['filename']}: {error_message}")
            
            # Check if file still exists
            if os.path.exists(transfer_info['file_path']):
                # Attempt to resume transfer
                print(f"🔄 Attempting to resume transfer for {transfer_info['filename']}")
                self.resume_file_transfer(transfer_id)
            else:
                print(f"❌ Source file no longer exists: {transfer_info['filename']}")
                self.chat_widget.add_message("System", f"Transfer failed: Source file deleted", "text")
                del self.file_transfers[transfer_id]
    
    def resume_file_transfer(self, transfer_id: str):
        """Resume a paused or failed file transfer"""
        if transfer_id in self.file_transfers:
            transfer_info = self.file_transfers[transfer_id]
            # Create new transfer dialog for resume
            transfer_dialog = FileTransferDialog(
                transfer_info['file_path'], 
                transfer_info['target_ip'], 
                transfer_info['websocket'], 
                self
            )
            transfer_dialog.show()
            del self.file_transfers[transfer_id]
    
    def update_peer_in_database(self, ip: str, username: str, peer_uuid: str):
        """Update or create peer record in database"""
        # Check if user exists by UUID
        existing_user = self.db_session.query(User).filter_by(uuid=peer_uuid).first()
        
        if existing_user:
            # Update existing user
            if existing_user.ip_address != ip:
                print(f"Updating peer {username} IP from {existing_user.ip_address} to {ip}")
                existing_user.ip_address = ip
                existing_user.last_seen = datetime.utcnow()
                existing_user.is_online = True
                self.db_session.commit()
        else:
            # Create new user record
            print(f"Adding new peer {username} ({ip}) with UUID {peer_uuid}")
            new_user = User(
                uuid=peer_uuid,
                ip_address=ip,
                username=username,
                is_online=True
            )
            self.db_session.add(new_user)
            self.db_session.commit()
        
    def handle_message(self, sender_ip: str, message_type: str, content: str):
        """Handle incoming messages"""
        # Find username for sender
        username = "Unknown"
        for i in range(self.peer_widget.peer_list.count()):
            item = self.peer_widget.peer_list.item(i)
            if item.text().endswith(f"({sender_ip})"):
                username = item.text().split(" (")[0]
                break
                
        self.chat_widget.add_message(username, content, message_type)
        
    def handle_port_error(self, error_message):
        """Handle port error and show message to user"""
        print(f"Port error: {error_message}")
        
        # Show error dialog
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle("Port Already In Use")
        msg_box.setText("Cannot start Peer-to-Peer Chat")
        msg_box.setInformativeText(error_message)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()
        
        # Close the application
        self.close()
        
    def handle_websocket_port_error(self, error_message):
        """Handle WebSocket port error without closing the application"""
        print(f"WebSocket port error: {error_message}")
        
        # Show warning dialog but don't close the app
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle("WebSocket Port Issue")
        msg_box.setText("WebSocket server could not start")
        msg_box.setInformativeText(f"{error_message}\n\nPeer discovery will continue, but chat functionality may be limited.")
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()
        
        # Update status bar
        self.statusBar().showMessage("Peer discovery active - WebSocket server unavailable")
        
    def show_settings(self):
        """Show settings dialog"""
        QMessageBox.information(self, "Settings", "Settings functionality coming soon!")
        
    def show_notification_settings(self):
        """Show notification settings dialog"""
        if self.notification_manager:
            dialog = NotificationSettingsDialog(self.notification_manager, self)
            dialog.exec_()
        
    def show_about(self):
        """Show about dialog"""
        about_text = """
        <h2>Peer-to-Peer Chat & File Sharing</h2>
        <p><b>Version:</b> 1.0.0</p>
        <p><b>Built with:</b> PyQt5, SQLite, SQLAlchemy, WebSockets, Cryptography</p>
        <p><b>Features:</b></p>
        <ul>
        <li>Real-time peer-to-peer chat</li>
        <li>File and image sharing</li>
        <li>Automatic peer discovery on LAN</li>
        <li>End-to-end encryption</li>
        <li>Persistent user identity with UUID</li>
        </ul>
        <p><b>Required Ports:</b> UDP 8080, TCP 8081</p>
        <p>Click the 🔥 Firewall Config button for setup instructions.</p>
        """
        QMessageBox.about(self, "About", about_text)
        
    def closeEvent(self, event):
        """Handle application close"""
        print("Closing application...")
        
        # Stop peer discovery thread
        if hasattr(self, 'discovery_thread') and self.discovery_thread.isRunning():
            print("Stopping peer discovery...")
            self.discovery_thread.stop()
            if not self.discovery_thread.wait(2000):  # Wait up to 2 seconds
                print("Force terminating discovery thread...")
                self.discovery_thread.terminate()
                self.discovery_thread.wait(1000)
        
        # Stop WebSocket server
        if hasattr(self, 'websocket_server') and self.websocket_server.isRunning():
            print("Stopping WebSocket server...")
            self.websocket_server.stop()
            if not self.websocket_server.wait(2000):  # Wait up to 2 seconds
                print("Force terminating WebSocket server...")
                self.websocket_server.terminate()
                self.websocket_server.wait(1000)
        
        # Close database session
        if hasattr(self, 'db_session'):
            print("Closing database session...")
            self.db_session.close()
        
        print("Application closed successfully")
        event.accept()

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Peer-to-Peer Chat")
    
    # Handle Ctrl+C gracefully
    import signal
    def signal_handler(sig, frame):
        print('\nReceived interrupt signal. Closing application...')
        app.quit()
    
    signal.signal(signal.SIGINT, signal_handler)
    
    window = MainWindow()
    window.show()
    
    try:
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        print("Application interrupted by user")
        sys.exit(0)

if __name__ == "__main__":
    main()
