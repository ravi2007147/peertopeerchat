#!/bin/bash
# Create installer package script

echo "Creating installer package for Peer-to-Peer Chat..."

# Check if executable exists
if [ ! -f "dist/PeerToPeerChat.exe" ]; then
    echo "❌ Executable not found! Run ./build.sh first."
    exit 1
fi

# Create installer directory
INSTALLER_DIR="PeerToPeerChat_Installer"
rm -rf $INSTALLER_DIR
mkdir -p $INSTALLER_DIR

# Copy executable
cp dist/PeerToPeerChat.exe $INSTALLER_DIR/

# Create installation script
cat > $INSTALLER_DIR/install.bat << 'EOF'
@echo off
echo Installing Peer-to-Peer Chat Application...
echo.

REM Create application directory
if not exist "%PROGRAMFILES%\PeerToPeerChat" mkdir "%PROGRAMFILES%\PeerToPeerChat"

REM Copy executable
copy "PeerToPeerChat.exe" "%PROGRAMFILES%\PeerToPeerChat\"

REM Create desktop shortcut
set "DESKTOP=%USERPROFILE%\Desktop"
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%TEMP%\CreateShortcut.vbs"
echo sLinkFile = "%DESKTOP%\Peer-to-Peer Chat.lnk" >> "%TEMP%\CreateShortcut.vbs"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%TEMP%\CreateShortcut.vbs"
echo oLink.TargetPath = "%PROGRAMFILES%\PeerToPeerChat\PeerToPeerChat.exe" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.WorkingDirectory = "%PROGRAMFILES%\PeerToPeerChat" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.Description = "Peer-to-Peer Chat and File Sharing" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.Save >> "%TEMP%\CreateShortcut.vbs"
cscript "%TEMP%\CreateShortcut.vbs"
del "%TEMP%\CreateShortcut.vbs"

REM Create start menu shortcut
set "STARTMENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs"
if not exist "%STARTMENU%\PeerToPeerChat" mkdir "%STARTMENU%\PeerToPeerChat"
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%TEMP%\CreateStartMenuShortcut.vbs"
echo sLinkFile = "%STARTMENU%\PeerToPeerChat\Peer-to-Peer Chat.lnk" >> "%TEMP%\CreateStartMenuShortcut.vbs"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%TEMP%\CreateStartMenuShortcut.vbs"
echo oLink.TargetPath = "%PROGRAMFILES%\PeerToPeerChat\PeerToPeerChat.exe" >> "%TEMP%\CreateStartMenuShortcut.vbs"
echo oLink.WorkingDirectory = "%PROGRAMFILES%\PeerToPeerChat" >> "%TEMP%\CreateStartMenuShortcut.vbs"
echo oLink.Description = "Peer-to-Peer Chat and File Sharing" >> "%TEMP%\CreateStartMenuShortcut.vbs"
echo oLink.Save >> "%TEMP%\CreateStartMenuShortcut.vbs"
cscript "%TEMP%\CreateStartMenuShortcut.vbs"
del "%TEMP%\CreateStartMenuShortcut.vbs"

echo.
echo ✅ Installation completed successfully!
echo.
echo 📍 Application installed to: %PROGRAMFILES%\PeerToPeerChat\
echo 🖥️  Desktop shortcut created
echo 📋 Start menu shortcut created
echo.
echo 🚀 You can now run "Peer-to-Peer Chat" from your desktop or start menu
echo.
pause
EOF

# Create uninstall script
cat > $INSTALLER_DIR/uninstall.bat << 'EOF'
@echo off
echo Uninstalling Peer-to-Peer Chat Application...
echo.

REM Remove desktop shortcut
if exist "%USERPROFILE%\Desktop\Peer-to-Peer Chat.lnk" del "%USERPROFILE%\Desktop\Peer-to-Peer Chat.lnk"

REM Remove start menu shortcut
if exist "%APPDATA%\Microsoft\Windows\Start Menu\Programs\PeerToPeerChat" rmdir /s /q "%APPDATA%\Microsoft\Windows\Start Menu\Programs\PeerToPeerChat"

REM Remove application files
if exist "%PROGRAMFILES%\PeerToPeerChat" rmdir /s /q "%PROGRAMFILES%\PeerToPeerChat"

echo.
echo ✅ Uninstallation completed successfully!
echo.
pause
EOF

# Create README for installer
cat > $INSTALLER_DIR/README.txt << 'EOF'
Peer-to-Peer Chat and File Sharing Application
==============================================

INSTALLATION:
1. Run install.bat as Administrator
2. The application will be installed to Program Files
3. Desktop and Start Menu shortcuts will be created

UNINSTALLATION:
1. Run uninstall.bat as Administrator
2. All files and shortcuts will be removed

FEATURES:
- Automatic peer discovery on local network
- Real-time chat with text, images, and files
- Secure encrypted communication
- Modern dark-themed GUI
- No internet connection required

NETWORK REQUIREMENTS:
- All peers must be on the same local network (LAN)
- UDP port 8888 for peer discovery
- TCP port 8765 for WebSocket communication
- Firewall should allow these ports

USAGE:
1. Launch the application
2. Wait for automatic peer discovery
3. Click on a peer to start chatting
4. Use Send File or Send Image buttons to share files

SUPPORT:
- Check firewall settings if peers are not discovered
- Ensure all devices are on the same network
- Contact support if you encounter issues

Version: 1.0
Build Date: $(date)
EOF

# Create a simple icon (if none exists)
if [ ! -f "icon.ico" ]; then
    echo "Creating default icon..."
    # Create a simple 32x32 icon using ImageMagick if available
    if command -v convert &> /dev/null; then
        convert -size 32x32 xc:blue -fill white -pointsize 20 -gravity center -annotate +0+0 "P2P" icon.ico
    else
        echo "Note: Install ImageMagick to create custom icons"
    fi
fi

# Copy icon if it exists
if [ -f "icon.ico" ]; then
    cp icon.ico $INSTALLER_DIR/
fi

# Create zip package
echo "Creating installer package..."
zip -r "PeerToPeerChat_Installer.zip" $INSTALLER_DIR/

echo ""
echo "✅ Installer package created successfully!"
echo "📦 Package: PeerToPeerChat_Installer.zip"
echo "📁 Contents:"
ls -la $INSTALLER_DIR/
echo ""
echo "🚀 To distribute:"
echo "   1. Send PeerToPeerChat_Installer.zip to target Windows PCs"
echo "   2. Extract the zip file"
echo "   3. Run install.bat as Administrator"
echo "   4. Application will be installed and ready to use!"
echo ""
echo "📋 Package includes:"
echo "   - PeerToPeerChat.exe (standalone executable)"
echo "   - install.bat (installation script)"
echo "   - uninstall.bat (removal script)"
echo "   - README.txt (instructions)"
echo "   - icon.ico (application icon, if available)"
