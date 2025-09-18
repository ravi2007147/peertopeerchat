#!/bin/bash
# Build script for creating standalone .exe package

echo "Building Peer-to-Peer Chat Application..."

# Activate virtual environment
source ../myenv/bin/activate

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build/
rm -rf dist/
rm -rf *.spec

# Install/upgrade PyInstaller
echo "Installing PyInstaller..."
pip install --upgrade pyinstaller

# Create the executable
echo "Creating standalone executable..."
pyinstaller --onefile \
    --windowed \
    --name "PeerToPeerChat" \
    --icon=icon.ico \
    --add-data "README.md;." \
    --hidden-import=PyQt5.QtCore \
    --hidden-import=PyQt5.QtGui \
    --hidden-import=PyQt5.QtWidgets \
    --hidden-import=sqlalchemy \
    --hidden-import=websockets \
    --hidden-import=cryptography \
    --hidden-import=asyncio \
    --hidden-import=json \
    --hidden-import=socket \
    --hidden-import=threading \
    --hidden-import=datetime \
    --hidden-import=base64 \
    --hidden-import=os \
    --hidden-import=sys \
    index.py

# Check if build was successful
if [ -f "dist/PeerToPeerChat.exe" ]; then
    echo ""
    echo "✅ Build successful!"
    echo "📦 Executable created: dist/PeerToPeerChat.exe"
    echo ""
    echo "📋 Package contents:"
    ls -la dist/
    echo ""
    echo "🚀 You can now distribute dist/PeerToPeerChat.exe to any Windows PC"
    echo "   No Python installation required on target machines!"
    echo ""
    echo "📁 To create a complete installer package:"
    echo "   ./create_installer.sh"
else
    echo "❌ Build failed! Check the output above for errors."
    exit 1
fi
