# Peer-to-Peer Chat & File Sharing Application

A modern peer-to-peer chat and file sharing application built with Python, PyQt5, SQLite, SQLAlchemy, WebSockets, and Cryptography.

## Features

- **Peer Discovery**: Automatically discovers other peers on your local network
- **Real-time Chat**: Send text messages, images, and files
- **Secure Communication**: End-to-end encryption for all messages
- **Modern GUI**: Clean, dark-themed interface similar to modern chat applications
- **File Sharing**: Share any type of file with peers
- **Offline Capability**: Works entirely on local network without internet

## Requirements

- Python 3.7+
- PyQt5
- SQLAlchemy
- WebSockets
- Cryptography

## Quick Setup

1. **Run the setup script:**
   ```bash
   ./setup.sh
   ```

2. **Start the application:**
   ```bash
   ./run.sh
   ```

## Manual Setup

If you prefer to set up manually:

1. **Activate your virtual environment:**
   ```bash
   source ../myenv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python index.py
   ```

## How to Use

1. **Launch the application** - It will automatically start scanning for peers on your local network
2. **Select a peer** - Click on any peer in the left panel to start chatting
3. **Send messages** - Type in the message box and press Enter or click Send
4. **Share files** - Use the "📁 Send File" button to share any file
5. **Share images** - Use the "🖼️ Send Image" button to share images

## Architecture

- **Peer Discovery**: Uses UDP broadcast on port 8888 to announce presence and discover peers
- **Communication**: WebSocket server on port 8765 for real-time messaging
- **Database**: SQLite with SQLAlchemy ORM for storing messages and user data
- **Encryption**: Fernet symmetric encryption for secure message transmission
- **GUI**: PyQt5 with modern dark theme and responsive layout

## Network Requirements

- All peers must be on the same local network (LAN)
- UDP port 8888 must be available for peer discovery
- TCP port 8765 must be available for WebSocket communication
- Firewall should allow these ports for proper functionality

## Troubleshooting

- **No peers found**: Ensure all devices are on the same network and firewall allows the required ports
- **Connection issues**: Check if ports 8888 and 8765 are available
- **GUI not loading**: Ensure PyQt5 is properly installed in your virtual environment

## Development

The application is structured with:
- `index.py`: Main application file with GUI and core functionality
- `requirements.txt`: Python dependencies
- `setup.sh`: Automated setup script
- `run.sh`: Application launcher script

## Security

- All messages are encrypted using Fernet symmetric encryption
- Peer discovery uses local network broadcast only
- No external internet connection required
- Messages stored locally in encrypted SQLite database
