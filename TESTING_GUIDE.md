# Single PC Testing Guide for Peer-to-Peer Chat

## 🧪 Testing Methods

### Method 1: Quick Test (Recommended)
```bash
./test_single_pc.sh quick
```
This starts 2 instances quickly and you can test peer discovery and chat.

### Method 2: Full Test with Custom Ports
```bash
./test_single_pc.sh start
```
This starts 2 instances with different ports to avoid conflicts.

### Method 3: Manual Testing
1. **Terminal 1**: `./run.sh`
2. **Terminal 2**: `./run.sh`
3. **Test**: Look for peers in both windows

## 🔍 What to Test

### ✅ Peer Discovery
- [ ] Both instances should appear in each other's peer list
- [ ] Peers should show as "Username (IP Address)"
- [ ] Status should show "Found X peer(s)"

### ✅ Chat Functionality
- [ ] Click on a peer to start chatting
- [ ] Send text messages
- [ ] Messages should appear in real-time
- [ ] Test sending files and images

### ✅ User Identity (UUID)
- [ ] Each instance should have a unique UUID
- [ ] Same user should be recognized even if IP changes
- [ ] Check console output for UUID generation

### ✅ Network Features
- [ ] Messages should be encrypted
- [ ] File sharing should work
- [ ] Application should close cleanly

## 🛠️ Troubleshooting

### If peers don't appear:
1. Check firewall settings
2. Ensure both instances are running
3. Check console output for errors
4. Try different ports

### If chat doesn't work:
1. Verify WebSocket connection
2. Check if ports 8765 and 8888 are available
3. Look for error messages in console

### If application hangs:
1. Use `./test_single_pc.sh stop` to clean up
2. Check for zombie processes
3. Restart terminal sessions

## 📊 Testing Checklist

- [ ] **Startup**: Application starts without errors
- [ ] **Peer Discovery**: Finds other instances automatically
- [ ] **Chat**: Can send/receive text messages
- [ ] **File Sharing**: Can send files and images
- [ ] **Encryption**: Messages are encrypted
- [ ] **UUID System**: Unique user identity works
- [ ] **Shutdown**: Application closes cleanly
- [ ] **Multiple Instances**: Can run 2+ instances simultaneously

## 🚀 Advanced Testing

### Test with Different Networks:
1. Connect to different WiFi networks
2. Test with VPN enabled/disabled
3. Test with firewall on/off

### Test with Different Users:
1. Run as different system users
2. Test with different hostnames
3. Test UUID persistence across restarts

### Test Edge Cases:
1. Close one instance while chatting
2. Restart application multiple times
3. Test with many instances (3-5)

## 📝 Test Results Template

```
Test Date: ___________
Tester: ___________
OS: ___________

✅ Peer Discovery: Working / Not Working
✅ Chat Messages: Working / Not Working  
✅ File Sharing: Working / Not Working
✅ Encryption: Working / Not Working
✅ UUID System: Working / Not Working
✅ Clean Shutdown: Working / Not Working

Notes:
- 
- 
- 

Issues Found:
- 
- 
- 
```
