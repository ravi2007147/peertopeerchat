@echo off
REM Windows Installer Creator for Peer-to-Peer Chat
REM This script creates a complete installer package

echo Creating Windows installer package...

REM Check if executable exists
if not exist "dist\PeerToPeerChat.exe" (
    echo ❌ Executable not found! Run build_windows.bat first.
    pause
    exit 1
)

REM Create installer directory
set INSTALLER_DIR=PeerToPeerChat_Installer
if exist "%INSTALLER_DIR%" rmdir /s /q "%INSTALLER_DIR%"
mkdir "%INSTALLER_DIR%"

REM Copy executable
copy "dist\PeerToPeerChat.exe" "%INSTALLER_DIR%\"

REM Create installation script
echo @echo off > "%INSTALLER_DIR%\install.bat"
echo echo Installing Peer-to-Peer Chat Application... >> "%INSTALLER_DIR%\install.bat"
echo echo. >> "%INSTALLER_DIR%\install.bat"
echo. >> "%INSTALLER_DIR%\install.bat"
echo REM Create application directory >> "%INSTALLER_DIR%\install.bat"
echo if not exist "%%PROGRAMFILES%%\PeerToPeerChat" mkdir "%%PROGRAMFILES%%\PeerToPeerChat" >> "%INSTALLER_DIR%\install.bat"
echo. >> "%INSTALLER_DIR%\install.bat"
echo REM Copy executable >> "%INSTALLER_DIR%\install.bat"
echo copy "PeerToPeerChat.exe" "%%PROGRAMFILES%%\PeerToPeerChat\" >> "%INSTALLER_DIR%\install.bat"
echo. >> "%INSTALLER_DIR%\install.bat"
echo REM Create desktop shortcut >> "%INSTALLER_DIR%\install.bat"
echo set "DESKTOP=%%USERPROFILE%%\Desktop" >> "%INSTALLER_DIR%\install.bat"
echo echo Set oWS = WScript.CreateObject("WScript.Shell") ^> "%%TEMP%%\CreateShortcut.vbs" >> "%INSTALLER_DIR%\install.bat"
echo echo sLinkFile = "%%DESKTOP%%\Peer-to-Peer Chat.lnk" ^>^> "%%TEMP%%\CreateShortcut.vbs" >> "%INSTALLER_DIR%\install.bat"
echo echo Set oLink = oWS.CreateShortcut(sLinkFile) ^>^> "%%TEMP%%\CreateShortcut.vbs" >> "%INSTALLER_DIR%\install.bat"
echo echo oLink.TargetPath = "%%PROGRAMFILES%%\PeerToPeerChat\PeerToPeerChat.exe" ^>^> "%%TEMP%%\CreateShortcut.vbs" >> "%INSTALLER_DIR%\install.bat"
echo echo oLink.WorkingDirectory = "%%PROGRAMFILES%%\PeerToPeerChat" ^>^> "%%TEMP%%\CreateShortcut.vbs" >> "%INSTALLER_DIR%\install.bat"
echo echo oLink.Description = "Peer-to-Peer Chat and File Sharing" ^>^> "%%TEMP%%\CreateShortcut.vbs" >> "%INSTALLER_DIR%\install.bat"
echo echo oLink.Save ^>^> "%%TEMP%%\CreateShortcut.vbs" >> "%INSTALLER_DIR%\install.bat"
echo cscript "%%TEMP%%\CreateShortcut.vbs" >> "%INSTALLER_DIR%\install.bat"
echo del "%%TEMP%%\CreateShortcut.vbs" >> "%INSTALLER_DIR%\install.bat"
echo. >> "%INSTALLER_DIR%\install.bat"
echo echo. >> "%INSTALLER_DIR%\install.bat"
echo echo ✅ Installation completed successfully! >> "%INSTALLER_DIR%\install.bat"
echo echo. >> "%INSTALLER_DIR%\install.bat"
echo echo 📍 Application installed to: %%PROGRAMFILES%%\PeerToPeerChat\ >> "%INSTALLER_DIR%\install.bat"
echo echo 🖥️  Desktop shortcut created >> "%INSTALLER_DIR%\install.bat"
echo echo. >> "%INSTALLER_DIR%\install.bat"
echo echo 🚀 You can now run "Peer-to-Peer Chat" from your desktop >> "%INSTALLER_DIR%\install.bat"
echo echo. >> "%INSTALLER_DIR%\install.bat"
echo pause >> "%INSTALLER_DIR%\install.bat"

REM Create uninstall script
echo @echo off > "%INSTALLER_DIR%\uninstall.bat"
echo echo Uninstalling Peer-to-Peer Chat Application... >> "%INSTALLER_DIR%\uninstall.bat"
echo echo. >> "%INSTALLER_DIR%\uninstall.bat"
echo. >> "%INSTALLER_DIR%\uninstall.bat"
echo REM Remove desktop shortcut >> "%INSTALLER_DIR%\uninstall.bat"
echo if exist "%%USERPROFILE%%\Desktop\Peer-to-Peer Chat.lnk" del "%%USERPROFILE%%\Desktop\Peer-to-Peer Chat.lnk" >> "%INSTALLER_DIR%\uninstall.bat"
echo. >> "%INSTALLER_DIR%\uninstall.bat"
echo REM Remove application files >> "%INSTALLER_DIR%\uninstall.bat"
echo if exist "%%PROGRAMFILES%%\PeerToPeerChat" rmdir /s /q "%%PROGRAMFILES%%\PeerToPeerChat" >> "%INSTALLER_DIR%\uninstall.bat"
echo. >> "%INSTALLER_DIR%\uninstall.bat"
echo echo. >> "%INSTALLER_DIR%\uninstall.bat"
echo echo ✅ Uninstallation completed successfully! >> "%INSTALLER_DIR%\uninstall.bat"
echo echo. >> "%INSTALLER_DIR%\uninstall.bat"
echo pause >> "%INSTALLER_DIR%\uninstall.bat"

REM Create README
echo Peer-to-Peer Chat and File Sharing Application > "%INSTALLER_DIR%\README.txt"
echo ============================================== >> "%INSTALLER_DIR%\README.txt"
echo. >> "%INSTALLER_DIR%\README.txt"
echo INSTALLATION: >> "%INSTALLER_DIR%\README.txt"
echo 1. Run install.bat as Administrator >> "%INSTALLER_DIR%\README.txt"
echo 2. The application will be installed to Program Files >> "%INSTALLER_DIR%\README.txt"
echo 3. Desktop shortcut will be created >> "%INSTALLER_DIR%\README.txt"
echo. >> "%INSTALLER_DIR%\README.txt"
echo UNINSTALLATION: >> "%INSTALLER_DIR%\README.txt"
echo 1. Run uninstall.bat as Administrator >> "%INSTALLER_DIR%\README.txt"
echo 2. All files and shortcuts will be removed >> "%INSTALLER_DIR%\README.txt"
echo. >> "%INSTALLER_DIR%\README.txt"
echo FEATURES: >> "%INSTALLER_DIR%\README.txt"
echo - Automatic peer discovery on local network >> "%INSTALLER_DIR%\README.txt"
echo - Real-time chat with text, images, and files >> "%INSTALLER_DIR%\README.txt"
echo - Secure encrypted communication >> "%INSTALLER_DIR%\README.txt"
echo - Modern dark-themed GUI >> "%INSTALLER_DIR%\README.txt"
echo - No internet connection required >> "%INSTALLER_DIR%\README.txt"
echo. >> "%INSTALLER_DIR%\README.txt"
echo NETWORK REQUIREMENTS: >> "%INSTALLER_DIR%\README.txt"
echo - All peers must be on the same local network (LAN) >> "%INSTALLER_DIR%\README.txt"
echo - UDP port 8888 for peer discovery >> "%INSTALLER_DIR%\README.txt"
echo - TCP port 8765 for WebSocket communication >> "%INSTALLER_DIR%\README.txt"
echo - Firewall should allow these ports >> "%INSTALLER_DIR%\README.txt"
echo. >> "%INSTALLER_DIR%\README.txt"
echo USAGE: >> "%INSTALLER_DIR%\README.txt"
echo 1. Launch the application >> "%INSTALLER_DIR%\README.txt"
echo 2. Wait for automatic peer discovery >> "%INSTALLER_DIR%\README.txt"
echo 3. Click on a peer to start chatting >> "%INSTALLER_DIR%\README.txt"
echo 4. Use Send File or Send Image buttons to share files >> "%INSTALLER_DIR%\README.txt"
echo. >> "%INSTALLER_DIR%\README.txt"
echo SUPPORT: >> "%INSTALLER_DIR%\README.txt"
echo - Check firewall settings if peers are not discovered >> "%INSTALLER_DIR%\README.txt"
echo - Ensure all devices are on the same network >> "%INSTALLER_DIR%\README.txt"
echo - Contact support if you encounter issues >> "%INSTALLER_DIR%\README.txt"
echo. >> "%INSTALLER_DIR%\README.txt"
echo Version: 1.0 >> "%INSTALLER_DIR%\README.txt"
echo Build Date: %DATE% %TIME% >> "%INSTALLER_DIR%\README.txt"

REM Create zip package
echo Creating installer package...
powershell -command "Compress-Archive -Path '%INSTALLER_DIR%\*' -DestinationPath 'PeerToPeerChat_Installer.zip' -Force"

echo.
echo ✅ Installer package created successfully!
echo 📦 Package: PeerToPeerChat_Installer.zip
echo 📁 Contents:
dir "%INSTALLER_DIR%"
echo.
echo 🚀 To distribute:
echo    1. Send PeerToPeerChat_Installer.zip to target Windows PCs
echo    2. Extract the zip file
echo    3. Run install.bat as Administrator
echo    4. Application will be installed and ready to use!
echo.
echo 📋 Package includes:
echo    - PeerToPeerChat.exe (standalone executable)
echo    - install.bat (installation script)
echo    - uninstall.bat (removal script)
echo    - README.txt (instructions)
echo.
pause
