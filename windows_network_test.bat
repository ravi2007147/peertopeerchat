@echo off
REM Windows Network Diagnostic Script for Peer-to-Peer Chat
REM Run this in Command Prompt as Administrator

echo 🔍 Windows Peer-to-Peer Chat Network Diagnostics
echo ================================================
echo.

REM Get local IP address
echo 📍 Local IP Address:
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4"') do (
    set "ip=%%a"
    set "ip=!ip: =!"
    echo    !ip!
    goto :found_ip
)
:found_ip
echo.

REM Check port availability
echo 🔌 Port Availability:
echo    Port 8080 (Discovery):
netstat -an | findstr ":8080" >nul
if %errorlevel% equ 0 (
    echo    ❌ Port 8080 is in use:
    netstat -an | findstr ":8080"
) else (
    echo    ✅ Port 8080 is available
)

echo.
echo    Port 8081 (WebSocket):
netstat -an | findstr ":8081" >nul
if %errorlevel% equ 0 (
    echo    ❌ Port 8081 is in use:
    netstat -an | findstr ":8081"
) else (
    echo    ✅ Port 8081 is available
)

echo.

REM Test network connectivity
echo 🌐 Network Connectivity:
echo    Testing connection to Google DNS (8.8.8.8)...
ping -n 1 8.8.8.8 >nul
if %errorlevel% equ 0 (
    echo    ✅ Internet connectivity: OK
) else (
    echo    ❌ Internet connectivity: Failed
)

echo.

REM Check Windows Firewall status
echo 🔥 Windows Firewall Status:
netsh advfirewall show allprofiles state | findstr "State"
echo.

REM Test UDP broadcast (if netcat is available)
echo 📡 UDP Broadcast Test:
where nc >nul 2>&1
if %errorlevel% equ 0 (
    echo    Sending test broadcast to 255.255.255.255:8080...
    echo {"type":"test","ip":"%ip%","platform":"windows"} | nc -u -w1 255.255.255.255 8080
    echo    ✅ Broadcast sent via netcat
) else (
    echo    ❌ Netcat (nc) not available
    echo    💡 Install netcat or use PowerShell for UDP testing
)

echo.

REM Test UDP listening (if netcat is available)
echo 👂 UDP Listening Test (5 seconds):
where nc >nul 2>&1
if %errorlevel% equ 0 (
    echo    Listening on port 8080 for incoming broadcasts...
    timeout /t 5 /nobreak >nul & nc -u -l 8080
    echo    ✅ Listener test completed
) else (
    echo    ❌ Netcat (nc) not available for listening test
)

echo.

REM Check network interfaces
echo 🌐 Network Interfaces:
ipconfig | findstr /i "adapter\|IPv4"

echo.
echo 🎯 Troubleshooting Tips:
echo    1. Ensure both devices are on the same network
echo    2. Run this script as Administrator
echo    3. Check if Windows Defender is blocking the application
echo    4. Verify no antivirus is blocking network traffic
echo    5. Try running the Python application as Administrator
echo.
echo 💡 Manual Test:
echo    On Mac: nc -u -l 8080
echo    On Windows: echo hello ^| nc -u [MAC_IP] 8080
echo.
pause
