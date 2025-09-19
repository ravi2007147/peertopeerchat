# Peer-to-Peer Chat & File Sharing Application

A professional, modular peer-to-peer chat and file sharing application built with PyQt5, SQLite, SQLAlchemy, WebSockets, and Cryptography.

## 🏗️ Project Structure

```
src/
├── main.py                 # Main application entry point
├── models/                 # Database models and management
│   ├── __init__.py
│   └── database.py         # User, Message models & DatabaseManager
├── network/                # Network communication classes
│   ├── __init__.py
│   ├── communication.py    # PeerDiscovery & WebSocketServer
│   └── file_transfer.py   # FileTransfer & FileTransferDialog
├── ui/                     # User interface components
│   ├── __init__.py
│   ├── components.py      # ChatWidget & PeerListWidget
│   └── notifications.py    # NotificationManager & Settings
├── dialogs/                # Dialog windows
│   ├── __init__.py
│   └── firewall.py        # FirewallConfigDialog
├── utils/                  # Utility functions
│   ├── __init__.py
│   └── helpers.py         # Helper functions & utilities
└── requirements.txt       # Python dependencies
```

## 🚀 Features

### Core Functionality
- **Peer Discovery**: Automatic LAN peer detection using UDP broadcast
- **Real-time Chat**: WebSocket-based messaging with timestamps
- **File Sharing**: Chunked file transfer with progress tracking
- **Image Sharing**: Support for image file transfers
- **Encryption**: End-to-end encrypted communication

### Advanced Features
- **Progress Tracking**: Real-time file transfer progress with pause/resume
- **Desktop Notifications**: System tray notifications for incoming messages
- **Error Handling**: Robust error handling and recovery mechanisms
- **Cross-platform**: Works on Windows, macOS, and Linux
- **Firewall Configuration**: Automatic and manual firewall setup

### User Experience
- **Modern UI**: Dark theme with professional styling
- **System Tray**: Minimize to system tray with notifications
- **Settings**: Configurable notification preferences
- **Database**: Persistent user and message storage
- **UUID System**: Unique user identification across sessions

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd peertopeer/src
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv ../myenv
   source ../myenv/bin/activate  # On Windows: ../myenv/Scripts/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```bash
   python main.py
   ```

## 📋 Dependencies

- **PyQt5**: GUI framework
- **SQLAlchemy**: Database ORM
- **websockets**: WebSocket communication
- **cryptography**: Encryption support
- **SQLite**: Database (included with Python)

## 🔧 Configuration

### Firewall Setup
The application requires two ports:
- **UDP 8080**: Peer discovery
- **TCP 8081**: WebSocket communication

Use the "🔥 Firewall Config" button in the toolbar for automatic setup.

### Network Requirements
- All peers must be on the same local network
- Firewall must allow the required ports
- No internet connection required (pure LAN communication)

## 🎯 Usage

1. **Start the application** on multiple devices
2. **Wait for peer discovery** (peers appear in the left panel)
3. **Click on a peer** to establish connection
4. **Start chatting** or send files/images
5. **Use notifications** to stay updated when minimized

## 🔒 Security

- **End-to-end encryption** for all communications
- **UUID-based user identification** prevents impersonation
- **Local network only** - no external connections
- **Secure file transfers** with integrity checking

## 🐛 Troubleshooting

### Common Issues

1. **"Available Peers" empty**:
   - Check firewall settings
   - Ensure all devices are on same network
   - Use "Test Ports" in firewall dialog

2. **File transfer fails**:
   - Check WebSocket connection status
   - Verify file permissions
   - Use pause/resume for large files

3. **Notifications not working**:
   - Check system tray availability
   - Verify notification settings
   - Ensure app is minimized

### Debug Mode
Run with debug output:
```bash
python main.py --debug
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with PyQt5 for cross-platform GUI
- Uses SQLAlchemy for robust database management
- WebSocket implementation for real-time communication
- Cryptography library for secure communications