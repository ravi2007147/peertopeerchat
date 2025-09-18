# Windows Build Instructions

## 🖥️ **How to Create Windows .exe File**

### **Method 1: Build on Windows Machine (Recommended)**

1. **Copy the entire project** to a Windows PC
2. **Install Python 3.7+** on Windows
3. **Open Command Prompt** as Administrator
4. **Navigate to project folder**:
   ```cmd
   cd C:\path\to\peertopeer\src
   ```
5. **Install dependencies**:
   ```cmd
   pip install -r requirements.txt
   ```
6. **Run Windows build script**:
   ```cmd
   build_windows.bat
   ```
7. **Get the executable**: `dist\PeerToPeerChat.exe`

### **Method 2: Use Current macOS Build**

The current build works on macOS:
- **Executable**: `dist/PeerToPeerChat` (37MB)
- **App Bundle**: `dist/PeerToPeerChat.app`
- **Run with**: `./dist/PeerToPeerChat`

### **Method 3: Cross-Platform Distribution**

For maximum compatibility, create builds for both platforms:

#### **On macOS** (Current):
```bash
./build.sh
# Creates: dist/PeerToPeerChat (macOS executable)
```

#### **On Windows**:
```cmd
build_windows.bat
# Creates: dist\PeerToPeerChat.exe (Windows executable)
```

## 📦 **Distribution Options**

### **Option A: Source Code Distribution**
- Send the entire `src/` folder
- Recipients run `setup.sh` (macOS/Linux) or install Python + dependencies (Windows)
- Most flexible but requires Python installation

### **Option B: Executable Distribution**
- **macOS**: Send `dist/PeerToPeerChat` or `dist/PeerToPeerChat.app`
- **Windows**: Send `dist\PeerToPeerChat.exe`
- **No Python required** on target machines
- **Easiest for end users**

### **Option C: Installer Package**
- Use `create_installer.sh` (macOS) or create Windows installer
- Professional installation experience
- Desktop shortcuts and start menu entries

## 🎯 **Recommended Approach**

1. **For macOS users**: Use current build (`dist/PeerToPeerChat`)
2. **For Windows users**: Copy project to Windows PC and run `build_windows.bat`
3. **For mixed environments**: Create both builds

## 📋 **Current Build Status**

✅ **macOS Build**: Complete and working
- File: `dist/PeerToPeerChat` (37MB)
- App: `dist/PeerToPeerChat.app`
- Tested: ✅ Working perfectly

⏳ **Windows Build**: Requires Windows machine
- Script: `build_windows.bat` (ready to use)
- Requirements: Windows PC with Python

## 🚀 **Quick Test**

Test the current macOS build:
```bash
# Run the executable
./dist/PeerToPeerChat

# Or run the app bundle
open dist/PeerToPeerChat.app
```

The application should start and show the peer-to-peer chat interface!
