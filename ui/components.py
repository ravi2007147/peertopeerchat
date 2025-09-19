#!/usr/bin/env python3
"""
UI Components for Peer-to-Peer Chat Application
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, 
    QPushButton, QListWidget, QLabel, QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from datetime import datetime
import os

class ChatWidget(QWidget):
    """Chat interface widget"""
    
    def __init__(self):
        super().__init__()
        self.current_peer = None
        self.init_ui()
        
    def init_ui(self):
        """Initialize the chat UI"""
        layout = QVBoxLayout()
        
        # Peer info
        self.peer_label = QLabel("Select a peer to start chatting")
        self.peer_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(self.peer_label)
        
        # Chat area
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.setFont(QFont("Consolas", 10))
        layout.addWidget(self.chat_area)
        
        # Message input
        input_layout = QHBoxLayout()
        
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type your message...")
        self.message_input.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.message_input)
        
        send_button = QPushButton("Send")
        send_button.clicked.connect(self.send_message)
        input_layout.addWidget(send_button)
        
        # File transfer buttons
        file_button = QPushButton("📁 File")
        file_button.clicked.connect(self.send_file)
        input_layout.addWidget(file_button)
        
        image_button = QPushButton("🖼️ Image")
        image_button.clicked.connect(self.send_image)
        input_layout.addWidget(image_button)
        
        layout.addLayout(input_layout)
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
                from network.file_transfer import FileTransferDialog
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

