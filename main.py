#!/usr/bin/env python3
"""
Main Application for Peer-to-Peer Chat & File Sharing
"""

import sys
import os
import json
import threading
import asyncio
import websockets
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QAction, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

# Import our modules
from models.database import DatabaseManager, User
from network.communication import PeerDiscovery, WebSocketServer
from network.file_transfer import FileTransferDialog
from ui.components import ChatWidget, PeerListWidget
from ui.notifications import NotificationManager, NotificationSettingsDialog
from dialogs.firewall import FirewallConfigDialog
from utils.helpers import get_local_ip, generate_user_uuid, get_hostname

class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.current_user_uuid = None
        self.current_username = None
        self.db_manager = None
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
        """Initialize the user interface"""
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
            QTextEdit, QLineEdit {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 5px;
            }
            QPushButton {
                background-color: #4a4a4a;
                color: #ffffff;
                border: 1px solid #666666;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
            }
            QPushButton:pressed {
                background-color: #3a3a3a;
            }
            QListWidget {
                background-color: #3c3c3c;
                color: #ffffff;
                border: 1px solid #555555;
                selection-background-color: #0078d4;
            }
            QLabel {
                color: #ffffff;
            }
            QSplitter::handle {
                background-color: #555555;
            }
        """)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Create splitter
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Create peer list widget
        self.peer_widget = PeerListWidget()
        self.peer_widget.peer_selected.connect(self.on_peer_selected)
        splitter.addWidget(self.peer_widget)
        
        # Create chat widget
        self.chat_widget = ChatWidget()
        splitter.addWidget(self.chat_widget)
        
        # Set splitter proportions
        splitter.setSizes([300, 900])
        
        # Create toolbar
        self.create_toolbar()
        
        # Status bar
        self.statusBar().showMessage("Starting application...")
        
    def create_toolbar(self):
        """Create toolbar with firewall configuration icon"""
        toolbar = self.addToolBar("Main")
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        
        # Firewall configuration action
        firewall_action = QAction("🔥 Firewall Config", self)
        firewall_action.setToolTip("Show firewall configuration instructions")
        firewall_action.triggered.connect(self.show_firewall_config)
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
        
    def init_database(self):
        """Initialize database"""
        try:
            self.db_manager = DatabaseManager()
            self.db_manager.handle_migration()
            self.db_session = self.db_manager.get_session()
            
            # Get or create current user
            self.current_user_uuid, self.current_username = self.get_or_create_user()
            
        except Exception as e:
            print(f"Database initialization error: {e}")
            QMessageBox.critical(self, "Database Error", f"Failed to initialize database: {e}")
            sys.exit(1)
    
    def get_or_create_user(self):
        """Get existing user or create new one"""
        try:
            # Try to get existing user
            existing_user = self.db_session.query(User).first()
            
            if existing_user:
                # Update IP address if changed
                current_ip = get_local_ip()
                if existing_user.ip_address != current_ip:
                    print(f"🔄 Updating IP address from {existing_user.ip_address} to {current_ip}")
                    existing_user.ip_address = current_ip
                    existing_user.last_seen = datetime.utcnow()
                    existing_user.is_online = True
                    self.db_session.commit()
                
                return existing_user.uuid, existing_user.username
            else:
                # Create new user
                user_uuid = generate_user_uuid()
                username = get_hostname()
                current_ip = get_local_ip()
                
                new_user = User(
                    uuid=user_uuid,
                    ip_address=current_ip,
                    username=username,
                    is_online=True
                )
                
                self.db_session.add(new_user)
                self.db_session.commit()
                
                print(f"👤 Created new user: {username} ({current_ip}) UUID={user_uuid}")
                return user_uuid, username
                
        except Exception as e:
            print(f"Error getting/creating user: {e}")
            # Fallback
            return generate_user_uuid(), get_hostname()
    
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
        """Handle port errors from discovery thread"""
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle("Port Error")
        msg_box.setText("Critical Port Error")
        msg_box.setInformativeText(error_message)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()
        
        # Close application
        self.close()
    
    def handle_websocket_port_error(self, error_message):
        """Handle WebSocket port errors (non-critical)"""
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle("WebSocket Port Error")
        msg_box.setText("WebSocket Server Unavailable")
        msg_box.setInformativeText(error_message)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()
        
        # Update status bar
        self.statusBar().showMessage("Peer discovery active - WebSocket server unavailable")
        
    def show_firewall_config(self):
        """Show firewall configuration dialog"""
        dialog = FirewallConfigDialog(self)
        dialog.exec_()
        
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
        <li>Real-time peer discovery</li>
        <li>Secure encrypted messaging</li>
        <li>File and image sharing</li>
        <li>Progress tracking for transfers</li>
        <li>Desktop notifications</li>
        <li>Cross-platform support</li>
        </ul>
        <p><b>Network:</b> Uses UDP for discovery (port 8080) and WebSocket for communication (port 8081)</p>
        """
        QMessageBox.about(self, "About", about_text)
    
    def closeEvent(self, event):
        """Handle application close"""
        print("Closing application...")
        
        # Stop discovery thread
        if self.discovery_thread:
            print("Stopping peer discovery...")
            self.discovery_thread.stop()
            print("Stopping peer discovery thread...")
            if not self.discovery_thread.wait(2000):
                print("Force terminating discovery thread...")
                self.discovery_thread.terminate()
                self.discovery_thread.wait()
        
        # Stop WebSocket server
        if self.websocket_server:
            print("Stopping WebSocket server...")
            self.websocket_server.stop()
            print("Stopping WebSocket server...")
            if not self.websocket_server.wait(2000):
                print("Force terminating WebSocket server...")
                self.websocket_server.terminate()
                self.websocket_server.wait()
        
        # Close database session
        if self.db_session:
            print("Closing database session...")
            self.db_session.close()
        
        print("Application closed successfully")
        event.accept()

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("Peer-to-Peer Chat")
    app.setApplicationVersion("1.0.0")
    
    # Set application icon (if available)
    # app.setWindowIcon(QIcon("icon.png"))
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Handle Ctrl+C gracefully
    import signal
    def signal_handler(sig, frame):
        print("\nReceived interrupt signal, closing application...")
        window.close()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Start event loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

