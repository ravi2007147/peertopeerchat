# Firewall Configuration Guide for Peer-to-Peer Chat

## 🔥 **Required Firewall Ports**

The application uses **consistent ports** that must be allowed through the firewall:

- **UDP Port 8080**: Peer discovery (broadcast/listen)
- **TCP Port 8081**: WebSocket communication

## 🍎 **macOS Firewall Configuration**

### **Method 1: System Preferences (Recommended)**
1. **Open System Preferences** → **Security & Privacy** → **Firewall**
2. **Click the lock** to make changes (enter password)
3. **Click "Firewall Options..."**
4. **Add Application**: Click "+" and navigate to:
   - Python executable: `/usr/bin/python3` or your virtual environment
   - Built app: `./dist/PeerToPeerChat`
5. **Set to "Allow incoming connections"**

### **Method 2: Command Line**
```bash
# Allow Python through firewall
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/bin/python3
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblock /usr/bin/python3

# Or allow the built executable
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add ./dist/PeerToPeerChat
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblock ./dist/PeerToPeerChat
```

### **Method 3: Allow Specific Ports**
```bash
# Allow UDP port 8080
sudo pfctl -f /etc/pf.conf
# Add rule: pass in proto udp from any to any port 8080

# Allow TCP port 8081  
# Add rule: pass in proto tcp from any to any port 8081
```

## 🪟 **Windows Firewall Configuration**

### **Method 1: Windows Defender Firewall (Recommended)**
1. **Open Windows Defender Firewall**
2. **Click "Allow an app or feature through Windows Defender Firewall"**
3. **Click "Change settings"** (admin required)
4. **Click "Allow another app..."**
5. **Browse to your Python executable** or the built .exe file
6. **Check both "Private" and "Public"** networks
7. **Click "OK"**

### **Method 2: Command Line (Advanced)**
```cmd
# Allow Python through firewall
netsh advfirewall firewall add rule name="Peer-to-Peer Chat" dir=in action=allow program="C:\Python\python.exe" enable=yes

# Allow specific ports
netsh advfirewall firewall add rule name="P2P Discovery" dir=in action=allow protocol=UDP localport=8080
netsh advfirewall firewall add rule name="P2P WebSocket" dir=in action=allow protocol=TCP localport=8081
```

### **Method 3: PowerShell (Advanced)**
```powershell
# Allow Python executable
New-NetFirewallRule -DisplayName "Peer-to-Peer Chat" -Direction Inbound -Action Allow -Program "C:\Python\python.exe"

# Allow specific ports
New-NetFirewallRule -DisplayName "P2P Discovery" -Direction Inbound -Action Allow -Protocol UDP -LocalPort 8080
New-NetFirewallRule -DisplayName "P2P WebSocket" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8081
```

## 🧪 **Testing Firewall Configuration**

### **Test Port Availability**
```bash
# macOS/Linux
python network_test.py

# Windows
python network_test.py
```

### **Manual Port Test**
```bash
# Test UDP port 8080
nc -u -l 8080

# Test TCP port 8081  
nc -l 8081
```

## 🚨 **Common Issues & Solutions**

### **Issue: "Port Already In Use"**
- **Solution**: Close the application using the port and try again
- **Check**: `lsof -i :8080` (macOS) or `netstat -an | findstr 8080` (Windows)

### **Issue: "No Peers Found"**
- **Solution**: Ensure firewall allows both ports 8080 and 8081
- **Check**: Both devices are on the same network
- **Verify**: No antivirus blocking network traffic

### **Issue: "Connection Failed"**
- **Solution**: Check WebSocket port 8081 is allowed through firewall
- **Verify**: TCP connections are not blocked

## 📋 **Firewall Checklist**

### **Before Running Application:**
- [ ] **UDP Port 8080**: Allowed for peer discovery
- [ ] **TCP Port 8081**: Allowed for WebSocket communication
- [ ] **Application**: Added to firewall exceptions
- [ ] **Network**: Both devices on same LAN
- [ ] **Antivirus**: Not blocking network traffic

### **After Configuration:**
- [ ] **Test**: Run `python network_test.py`
- [ ] **Verify**: Both ports show as "Available"
- [ ] **Launch**: Start the application
- [ ] **Check**: Peers appear in the list

## 🔧 **Troubleshooting Commands**

### **macOS:**
```bash
# Check what's using ports
lsof -i :8080
lsof -i :8081

# Check firewall status
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate
```

### **Windows:**
```cmd
# Check what's using ports
netstat -an | findstr 8080
netstat -an | findstr 8081

# Check firewall rules
netsh advfirewall firewall show rule name="Peer-to-Peer Chat"
```

## 💡 **Pro Tips**

1. **Consistent Ports**: Always use 8080 and 8081 for consistency
2. **Error Handling**: Application will show error if ports are busy
3. **Network Test**: Use `network_test.py` to diagnose issues
4. **Firewall First**: Configure firewall before testing the application
5. **Both Devices**: Configure firewall on both Mac and Windows

## 🎯 **Quick Setup**

1. **Configure firewall** on both devices (Mac + Windows)
2. **Allow ports 8080 and 8081** through firewall
3. **Add application** to firewall exceptions
4. **Test with** `python network_test.py`
5. **Launch application** on both devices
6. **Verify peers** appear in both GUIs
