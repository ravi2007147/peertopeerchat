#!/bin/bash
# Windows Build Script for Peer-to-Peer Chat Application
# This script should be run on a Windows machine

echo "Building Peer-to-Peer Chat Application for Windows..."

# Clean previous builds
echo "Cleaning previous builds..."
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
del *.spec 2>nul

# Install/upgrade PyInstaller
echo "Installing PyInstaller..."
pip install --upgrade pyinstaller

# Create the Windows executable
echo "Creating Windows executable..."
pyinstaller --onefile ^
    --windowed ^
    --name "PeerToPeerChat" ^
    --hidden-import=PyQt5.QtCore ^
    --hidden-import=PyQt5.QtGui ^
    --hidden-import=PyQt5.QtWidgets ^
    --hidden-import=sqlalchemy ^
    --hidden-import=websockets ^
    --hidden-import=cryptography ^
    --hidden-import=asyncio ^
    --hidden-import=json ^
    --hidden-import=socket ^
    --hidden-import=threading ^
    --hidden-import=datetime ^
    --hidden-import=base64 ^
    --hidden-import=os ^
    --hidden-import=sys ^
    --hidden-import=uuid ^
    --hidden-import=sqlite3 ^
    --hidden-import=shutil ^
    index.py

# Check if build was successful
if exist "dist\PeerToPeerChat.exe" (
    echo.
    echo ✅ Build successful!
    echo 📦 Executable created: dist\PeerToPeerChat.exe
    echo.
    echo 📋 Package contents:
    dir dist
    echo.
    echo 🚀 You can now distribute dist\PeerToPeerChat.exe to any Windows PC
    echo    No Python installation required on target machines!
    echo.
    echo 📁 To create a complete installer package:
    echo    create_installer.bat
) else (
    echo ❌ Build failed! Check the output above for errors.
    exit 1
)
