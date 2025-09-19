#!/usr/bin/env python3
"""
File Transfer Classes for Peer-to-Peer Chat Application
"""

import os
import json
import base64
import asyncio
import threading
import uuid
from datetime import datetime
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar
from PyQt5.QtGui import QFont

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
