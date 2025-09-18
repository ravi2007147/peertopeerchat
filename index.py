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
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    ip_address = Column(String(15), unique=True, nullable=False)
    username = Column(String(50), nullable=False)
    last_seen = Column(DateTime, default=datetime.utcnow)
    is_online = Column(Boolean, default=False)

class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    sender_ip = Column(String(15), nullable=False)
    receiver_ip = Column(String(15), nullable=False)
    message_type = Column(String(20), nullable=False)  # text, image, file
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_encrypted = Column(Boolean, default=True)

class PeerDiscovery(QThread):
    """Thread for discovering peers on LAN"""
    peer_found = pyqtSignal(str, str)  # ip, username
    peer_lost = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.running = True
        self.discovered_peers = {}
        
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
            'username': socket.gethostname(),
            'port': 8765
        })
        
        while self.running:
            try:
                sock.sendto(message.encode(), ('<broadcast>', 8888))
                self.msleep(5000)  # Broadcast every 5 seconds
            except Exception as e:
                print(f"Broadcast error: {e}")
                
    def listen_for_peers(self):
        """Listen for peer announcements"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', 8888))
        sock.settimeout(1.0)
        
        while self.running:
            try:
                data, addr = sock.recvfrom(1024)
                peer_info = json.loads(data.decode())
                
                if peer_info['type'] == 'peer_announcement':
                    ip = addr[0]
                    username = peer_info['username']
                    
                    if ip not in self.discovered_peers:
                        self.discovered_peers[ip] = username
                        self.peer_found.emit(ip, username)
                    else:
                        # Update last seen
                        self.discovered_peers[ip] = username
                        
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Listen error: {e}")
                
    def stop(self):
        self.running = False

class WebSocketServer(QThread):
    """WebSocket server for peer-to-peer communication"""
    message_received = pyqtSignal(str, str, str)  # sender_ip, message_type, content
    
    def __init__(self, port=8765):
        super().__init__()
        self.port = port
        self.clients = {}
        self.running = True
        
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
        server = await websockets.serve(self.handle_client, "0.0.0.0", self.port)
        await server.wait_closed()
        
    def run(self):
        """Run the WebSocket server"""
        asyncio.run(self.start_server())
        
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
    peer_selected = pyqtSignal(str, str)  # ip, username
    
    def __init__(self):
        super().__init__()
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
        
    def add_peer(self, ip: str, username: str):
        """Add peer to list"""
        # Check if peer already exists
        for i in range(self.peer_list.count()):
            item = self.peer_list.item(i)
            if item.text().startswith(ip):
                self.peer_list.takeItem(i)
                break
                
        item_text = f"{username} ({ip})"
        self.peer_list.addItem(item_text)
        self.status_label.setText(f"Found {self.peer_list.count()} peer(s)")
        
    def remove_peer(self, ip: str):
        """Remove peer from list"""
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
        self.peer_selected.emit(ip, username)

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
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.db_session = Session()
        
    def start_services(self):
        """Start peer discovery and WebSocket server"""
        # Start peer discovery
        self.discovery_thread = PeerDiscovery()
        self.discovery_thread.peer_found.connect(self.peer_widget.add_peer)
        self.discovery_thread.peer_lost.connect(self.peer_widget.remove_peer)
        self.discovery_thread.start()
        
        # Start WebSocket server
        self.websocket_server = WebSocketServer()
        self.websocket_server.message_received.connect(self.handle_message)
        self.websocket_server.start()
        
    def on_peer_selected(self, ip: str, username: str):
        """Handle peer selection"""
        self.chat_widget.set_current_peer(ip, username)
        self.statusBar().showMessage(f"Connected to {username} ({ip})")
        
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
        self.discovery_thread.stop()
        self.discovery_thread.wait()
        self.websocket_server.running = False
        self.websocket_server.wait()
        event.accept()

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Peer-to-Peer Chat")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
