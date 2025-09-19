#!/usr/bin/env python3
"""
Notification Classes for Peer-to-Peer Chat Application
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QCheckBox, QDialogButtonBox, QMessageBox, QSystemTrayIcon, QMenu, QAction
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap, QIcon, QColor

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
