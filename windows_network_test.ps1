# PowerShell Network Diagnostic Script for Peer-to-Peer Chat
# Run this in PowerShell as Administrator

Write-Host "🔍 Windows PowerShell Peer-to-Peer Chat Diagnostics" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan
Write-Host ""

# Get local IP address
Write-Host "📍 Local IP Address:" -ForegroundColor Yellow
$localIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.*"} | Select-Object -First 1).IPAddress
Write-Host "   $localIP" -ForegroundColor Green
Write-Host ""

# Check port availability
Write-Host "🔌 Port Availability:" -ForegroundColor Yellow
Write-Host "   Port 8080 (Discovery):" -ForegroundColor White
$port8080 = Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue
$udp8080 = Get-NetUDPEndpoint -LocalPort 8080 -ErrorAction SilentlyContinue
if ($port8080 -or $udp8080) {
    Write-Host "   ❌ Port 8080 is in use" -ForegroundColor Red
    if ($port8080) { $port8080 | Format-Table LocalAddress, LocalPort, State }
    if ($udp8080) { $udp8080 | Format-Table LocalAddress, LocalPort }
} else {
    Write-Host "   ✅ Port 8080 is available" -ForegroundColor Green
}

Write-Host ""
Write-Host "   Port 8081 (WebSocket):" -ForegroundColor White
$port8081 = Get-NetTCPConnection -LocalPort 8081 -ErrorAction SilentlyContinue
if ($port8081) {
    Write-Host "   ❌ Port 8081 is in use" -ForegroundColor Red
    $port8081 | Format-Table LocalAddress, LocalPort, State
} else {
    Write-Host "   ✅ Port 8081 is available" -ForegroundColor Green
}

Write-Host ""

# Test network connectivity
Write-Host "🌐 Network Connectivity:" -ForegroundColor Yellow
Write-Host "   Testing connection to Google DNS (8.8.8.8)..." -ForegroundColor White
$ping = Test-Connection -ComputerName "8.8.8.8" -Count 1 -Quiet
if ($ping) {
    Write-Host "   ✅ Internet connectivity: OK" -ForegroundColor Green
} else {
    Write-Host "   ❌ Internet connectivity: Failed" -ForegroundColor Red
}

Write-Host ""

# Check Windows Firewall status
Write-Host "🔥 Windows Firewall Status:" -ForegroundColor Yellow
$firewallProfiles = Get-NetFirewallProfile
foreach ($profile in $firewallProfiles) {
    Write-Host "   $($profile.Name): $($profile.Enabled)" -ForegroundColor White
}

Write-Host ""

# Test UDP broadcast using PowerShell
Write-Host "📡 UDP Broadcast Test:" -ForegroundColor Yellow
Write-Host "   Sending test broadcast to 255.255.255.255:8080..." -ForegroundColor White

try {
    $udpClient = New-Object System.Net.Sockets.UdpClient
    $udpClient.EnableBroadcast = $true
    $message = [System.Text.Encoding]::ASCII.GetBytes('{"type":"test","ip":"' + $localIP + '","platform":"windows"}')
    $udpClient.Send($message, $message.Length, "255.255.255.255", 8080)
    $udpClient.Close()
    Write-Host "   ✅ Broadcast sent via PowerShell" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Broadcast failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Test UDP listening using PowerShell
Write-Host "👂 UDP Listening Test (5 seconds):" -ForegroundColor Yellow
Write-Host "   Listening on port 8080 for incoming broadcasts..." -ForegroundColor White

try {
    $udpListener = New-Object System.Net.Sockets.UdpClient(8080)
    $udpListener.Client.ReceiveTimeout = 5000
    
    $endpoint = New-Object System.Net.IPEndPoint([System.Net.IPAddress]::Any, 0)
    $data = $udpListener.Receive([ref]$endpoint)
    $message = [System.Text.Encoding]::ASCII.GetString($data)
    Write-Host "   📨 Received: $message" -ForegroundColor Green
    Write-Host "   📍 From: $($endpoint.Address)" -ForegroundColor Green
    $udpListener.Close()
} catch {
    Write-Host "   ⚠️  No messages received in 5 seconds" -ForegroundColor Yellow
    Write-Host "   💡 This is normal if no other devices are broadcasting" -ForegroundColor Yellow
}

Write-Host ""

# Check network interfaces
Write-Host "🌐 Network Interfaces:" -ForegroundColor Yellow
Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.*"} | Format-Table IPAddress, InterfaceAlias

Write-Host ""

# Test local network connectivity
Write-Host "🏠 Local Network Test:" -ForegroundColor Yellow
$network = $localIP -replace '\.\d+$', ''
Write-Host "   Network: $network.0/24" -ForegroundColor White
Write-Host "   Testing common gateway addresses..." -ForegroundColor White

$gateways = @("$network.1", "$network.2", "$network.254")
foreach ($gateway in $gateways) {
    $ping = Test-Connection -ComputerName $gateway -Count 1 -Quiet -TimeoutSeconds 1
    if ($ping) {
        Write-Host "   ✅ $gateway is reachable" -ForegroundColor Green
    } else {
        Write-Host "   ❌ $gateway is not reachable" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "🎯 Troubleshooting Tips:" -ForegroundColor Cyan
Write-Host "   1. Ensure both devices are on the same network ($network.0/24)" -ForegroundColor White
Write-Host "   2. Run this script as Administrator" -ForegroundColor White
Write-Host "   3. Check if Windows Defender is blocking the application" -ForegroundColor White
Write-Host "   4. Verify no antivirus is blocking network traffic" -ForegroundColor White
Write-Host "   5. Try running the Python application as Administrator" -ForegroundColor White
Write-Host ""
Write-Host "💡 Manual Test:" -ForegroundColor Cyan
Write-Host "   On Mac: nc -u -l 8080" -ForegroundColor White
Write-Host "   On Windows: Test-NetConnection -ComputerName [MAC_IP] -Port 8080" -ForegroundColor White
Write-Host ""
Read-Host "Press Enter to continue"
