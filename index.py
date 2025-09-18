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
    QTabWidget, QGroupBox, QGridLayout, QComboBox, QSpinBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt5.QtGui import QFont, QPixmap, QIcon, QPalette, QColor

# Database models
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

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
    
    def __init__(self, current_user_uuid=None, current_username=None, discovery_port=8888):
        super().__init__()
        self.running = True
        self.discovered_peers = {}
        self.current_user_uuid = current_user_uuid
        self.current_username = current_username
        # Use a simple approach: try port 8888, if it fails, use 8889, etc.
        self.discovery_port = self.find_available_port(discovery_port)
        self.broadcast_port = 8888  # Always broadcast to standard port
        
    def find_available_port(self, start_port):
        """Find an available port starting from start_port"""
        import socket
        port = start_port
        while port < start_port + 100:  # Try up to 100 ports
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.bind(('', port))
                sock.close()
                return port
            except OSError:
                port += 1
        return start_port  # Fallback to original port
        
    def run(self):
        """Broadcast and listen for peer announcements"""
        # Broadcast our presence
        self.broadcast_presence()
        
        # Listen for other peers
        self.listen_for_peers()
        
    def broadcast_presence(self):
        """Broadcast our presence on LAN"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        message = json.dumps({
            'type': 'peer_announcement',
            'username': self.current_username or socket.gethostname(),
            'uuid': self.current_user_uuid,
            'port': 8765,  # WebSocket port (will be handled by WebSocketServer)
            'discovery_port': self.discovery_port
        })
        
        try:
            while self.running:
                try:
                    # Broadcast on the standard discovery port (8888) so all instances can hear each other
                    sock.sendto(message.encode(), ('<broadcast>', self.broadcast_port))
                    print(f"Broadcasting presence on port {self.broadcast_port}, listening on {self.discovery_port}")
                    # Use shorter sleep and check running status more frequently
                    for _ in range(50):  # 50 * 100ms = 5 seconds
                        if not self.running:
                            break
                        self.msleep(100)
                except Exception as e:
                    print(f"Broadcast error: {e}")
                    break
        finally:
            sock.close()
                
    def listen_for_peers(self):
        """Listen for peer announcements"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Try to bind to broadcast port first, fallback to discovery port if needed
        try:
            sock.bind(('', self.broadcast_port))
            print(f"Listening for peers on port {self.broadcast_port}")
        except OSError:
            sock.bind(('', self.discovery_port))
            print(f"Listening for peers on port {self.discovery_port}")
        sock.settimeout(1.0)
        
        try:
            while self.running:
                try:
                    data, addr = sock.recvfrom(1024)
                    peer_info = json.loads(data.decode())
                    
                    if peer_info['type'] == 'peer_announcement':
                        ip = addr[0]
                        username = peer_info['username']
                        peer_uuid = peer_info.get('uuid', 'unknown')
                        
                        # Don't add ourselves to the peer list
                        if peer_uuid != self.current_user_uuid:
                            if ip not in self.discovered_peers:
                                self.discovered_peers[ip] = {'username': username, 'uuid': peer_uuid}
                                self.peer_found.emit(ip, username, peer_uuid)
                            else:
                                # Update last seen
                                self.discovered_peers[ip] = {'username': username, 'uuid': peer_uuid}
                            
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"Listen error: {e}")
                    break
        finally:
            sock.close()
                
    def stop(self):
        print("Stopping peer discovery thread...")
        self.running = False
        # Give the thread a moment to finish current operations
        self.msleep(200)

class WebSocketServer(QThread):
    """WebSocket server for peer-to-peer communication"""
    message_received = pyqtSignal(str, str, str)  # sender_ip, message_type, content
    
    def __init__(self, port=8765):
        super().__init__()
        self.port = self.find_available_port(port)
        self.clients = {}
        self.running = True
        self.server = None
        
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
                self.message_received.emit(client_ip, data['type'], data['content'])
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            if client_ip in self.clients:
                del self.clients[client_ip]
                
    async def start_server(self):
        """Start the WebSocket server"""
        self.server = await websockets.serve(self.handle_client, "0.0.0.0", self.port)
        print(f"WebSocket server started on port {self.port}")
        
        # Wait for server to be closed
        await self.server.wait_closed()
        
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
        
    def add_message(self, sender: str, message: str, message_type: str = "text"):
        """Add message to chat area"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if message_type == "text":
            self.chat_area.append(f"[{timestamp}] {sender}: {message}")
        elif message_type == "image":
            self.chat_area.append(f"[{timestamp}] {sender}: [Image: {message}]")
        elif message_type == "file":
            self.chat_area.append(f"[{timestamp}] {sender}: [File: {message}]")
            
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
            # Emit signal to send message via WebSocket
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
        self.init_ui()
        self.init_database()
        self.start_services()
        
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
        """Get local IP address"""
        try:
            # Connect to a remote address to determine local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception:
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
        self.discovery_thread.start()
        
        # Start WebSocket server
        self.websocket_server = WebSocketServer()
        self.websocket_server.message_received.connect(self.handle_message)
        self.websocket_server.start()
        
    def on_peer_selected(self, ip: str, username: str, peer_uuid: str):
        """Handle peer selection"""
        self.chat_widget.set_current_peer(ip, username)
        self.statusBar().showMessage(f"Connected to {username} ({ip})")
        
        # Update user record in database
        self.update_peer_in_database(ip, username, peer_uuid)
        
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
