# Peer-to-Peer Chat & File Sharing Application

A modern peer-to-peer chat and file sharing application built with Python, PyQt5, SQLite, SQLAlchemy, WebSockets, and Cryptography. This application allows users on the same local network to communicate and share files without requiring internet connectivity.

## 🌟 Features

- **🔍 Automatic Peer Discovery**: Automatically discovers other peers on your local network
- **💬 Real-time Chat**: Send text messages, images, and files instantly
- **🔒 Secure Communication**: End-to-end encryption for all messages using Fernet encryption
- **🎨 Modern GUI**: Clean, dark-themed interface similar to modern chat applications
- **📁 File Sharing**: Share any type of file with peers on the network
- **🌐 Offline Capability**: Works entirely on local network without internet
- **📦 Standalone Executable**: Can be packaged as .exe for easy distribution

## 📋 Requirements

- Python 3.7+ (for development)
- PyQt5, SQLAlchemy, WebSockets, Cryptography (automatically installed)
- Windows/Linux/macOS (for running the application)
- Local network connection (LAN)

## 🚀 Quick Start Guide

### Option 1: Automated Setup (Recommended)

1. **Run the setup script:**
   ```bash
   ./setup.sh
   ```

2. **Start the application:**
   ```bash
   ./run.sh
   ```

### Option 2: Manual Setup

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

## 🧪 Single PC Testing

Before installing on multiple PCs, you can test the application on a single machine:

### Quick Test (Recommended)
```bash
./test_single_pc.sh quick
```
This starts 2 instances automatically for testing peer discovery and chat.

### Manual Testing
```bash
# Terminal 1
./run.sh

# Terminal 2  
./run.sh
```

### Test Management
```bash
./test_single_pc.sh status    # Check running instances
./test_single_pc.sh stop      # Stop all test instances
./test_single_pc.sh start      # Full test with custom ports
```

### What to Test
- ✅ **Peer Discovery**: Both instances should appear in each other's peer list
- ✅ **Chat Messages**: Send/receive text messages between instances
- ✅ **File Sharing**: Test sending files and images
- ✅ **UUID System**: Each instance should have unique identity
- ✅ **Clean Shutdown**: Application should close properly

See `TESTING_GUIDE.md` for detailed testing instructions.

## 📜 Scripts Explained

### 🔧 `setup.sh` - Automated Setup Script
**Purpose**: Automatically sets up the development environment and installs all dependencies.

**What it does**:
- Creates virtual environment at `../myenv` (if it doesn't exist)
- Activates the virtual environment
- Upgrades pip to the latest version
- Installs all required packages from `requirements.txt`
- Provides instructions for running the application

**Usage**:
```bash
./setup.sh
```

### ▶️ `run.sh` - Application Launcher
**Purpose**: Quick launcher script that activates the virtual environment and starts the application.

**What it does**:
- Activates the virtual environment (`../myenv`)
- Launches the main application (`python index.py`)

**Usage**:
```bash
./run.sh
```

### 🏗️ `build.sh` - Executable Builder
**Purpose**: Creates a standalone Windows executable (.exe) using PyInstaller.

**What it does**:
- Activates virtual environment
- Cleans previous build files
- Installs/upgrades PyInstaller
- Creates a single-file executable with all dependencies bundled
- Generates `dist/PeerToPeerChat.exe`

**Usage**:
```bash
./build.sh
```

**Requirements**: Must be run on Windows or with Wine for cross-compilation.

### 📦 `create_installer.sh` - Installer Package Creator
**Purpose**: Creates a complete installer package for Windows distribution.

**What it does**:
- Checks if executable exists (run `build.sh` first)
- Creates installer directory with all necessary files
- Generates Windows batch scripts for installation/uninstallation
- Creates desktop and start menu shortcuts
- Packages everything into a zip file for distribution

**Usage**:
```bash
./create_installer.sh
```

**Output**: `PeerToPeerChat_Installer.zip` containing:
- `PeerToPeerChat.exe` (standalone executable)
- `install.bat` (installation script)
- `uninstall.bat` (removal script)
- `README.txt` (user instructions)
- `icon.ico` (application icon)

## 🎯 How to Use the Software

### 1. **Starting the Application**
- Run `./run.sh` or `python index.py`
- The application will automatically start scanning for peers

### 2. **Discovering Peers**
- The left panel shows "Available Peers"
- Peers are automatically discovered on the same LAN
- Each peer shows as "Username (IP Address)"
- Status shows number of discovered peers

### 3. **Starting a Chat**
- Click on any peer in the left panel
- The right panel will show the chat interface
- Chat history loads automatically

### 4. **Sending Messages**
- Type your message in the input box
- Press Enter or click "Send" button
- Messages appear in real-time

### 5. **Sharing Files**
- Click "📁 Send File" to share any file
- Click "🖼️ Send Image" to share images
- Files are encrypted and sent securely

### 6. **Network Status**
- Status bar shows current connection status
- "Scanning for peers..." when discovering
- "Connected to [peer]" when chatting

## 🌐 Network Requirements

### **Ports Required**:
- **UDP Port 8888**: Peer discovery (broadcast/listen)
- **TCP Port 8765**: WebSocket communication

### **Network Setup**:
- All devices must be on the **same local network** (LAN)
- Firewall should allow the required ports
- No internet connection needed

### **Troubleshooting Network Issues**:
1. **No peers found**: Check if all devices are on the same network
2. **Connection failed**: Verify firewall settings allow ports 8888 and 8765
3. **Can't send messages**: Ensure WebSocket port 8765 is available

## 📦 Distribution & Installation

### **For Developers**:
1. Run `./build.sh` to create executable
2. Run `./create_installer.sh` to create installer package
3. Distribute `PeerToPeerChat_Installer.zip`

### **For End Users** (Windows):
1. Extract `PeerToPeerChat_Installer.zip`
2. Run `install.bat` as Administrator
3. Application installs to Program Files
4. Desktop and Start Menu shortcuts created
5. Run "Peer-to-Peer Chat" from desktop or start menu

### **Uninstallation**:
1. Run `uninstall.bat` as Administrator
2. All files and shortcuts removed

## 🔒 Security Features

- **End-to-End Encryption**: All messages encrypted with Fernet
- **Local Network Only**: No external internet communication
- **Secure File Transfer**: Files encrypted during transmission
- **Peer Authentication**: Automatic peer verification

## 🏗️ Architecture

### **Components**:
- **PeerDiscovery**: UDP broadcast for LAN peer discovery
- **WebSocketServer**: Real-time communication server
- **ChatWidget**: Modern chat interface
- **PeerListWidget**: Available peers display
- **Database**: SQLite with SQLAlchemy ORM

### **Communication Flow**:
1. **Discovery**: UDP broadcast announces presence
2. **Connection**: WebSocket establishes peer-to-peer connection
3. **Encryption**: Messages encrypted before transmission
4. **Storage**: Messages stored in local encrypted database

## 🐛 Troubleshooting

### **Common Issues**:

1. **"No peers found"**
   - Ensure all devices on same network
   - Check firewall settings
   - Verify UDP port 8888 is available

2. **"Connection failed"**
   - Check TCP port 8765 availability
   - Verify firewall allows WebSocket connections
   - Ensure peer is still online

3. **"Build failed"**
   - Run `./setup.sh` first to install dependencies
   - Ensure PyInstaller is installed
   - Check for missing Python packages

4. **"GUI not loading"**
   - Verify PyQt5 installation
   - Check virtual environment activation
   - Run `pip install PyQt5` if needed

### **Debug Mode**:
Run with verbose output:
```bash
python -v index.py
```

## 📝 Development

### **File Structure**:
```
src/
├── index.py              # Main application
├── requirements.txt      # Python dependencies
├── setup.sh             # Setup script
├── run.sh               # Launcher script
├── build.sh             # Build script
├── create_installer.sh  # Installer creator
├── migrate_db.py        # Database migration script
├── README.md            # This file
└── dist/                # Build output (after build.sh)
    └── PeerToPeerChat.exe
```

### **Database Migration**:
If you encounter database schema errors, run the migration script:
```bash
python migrate_db.py
```
This will:
- Backup your existing database
- Migrate to the new UUID-based schema
- Preserve your data where possible

### **Adding Features**:
1. Modify `index.py` for new functionality
2. Update `requirements.txt` for new dependencies
3. Test with `./run.sh`
4. Rebuild with `./build.sh`

## 📞 Support

- **Network Issues**: Check firewall and port availability
- **Build Issues**: Ensure all dependencies installed
- **Runtime Issues**: Verify Python and PyQt5 installation

## 📄 License

This project is open source. Feel free to modify and distribute.

---

**Version**: 1.0  
**Last Updated**: $(date)  
**Compatibility**: Windows 10+, Linux, macOS
