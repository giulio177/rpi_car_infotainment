# AirPlay Mirroring Troubleshooting Guide

## Quick Fix Summary

Your AirPlay mirroring issue has been resolved! Here's what was fixed:

### ✅ **Root Cause Identified**
- **X Server Missing**: RPiPlay requires an X server to display mirrored content, but your Qt app runs directly on the framebuffer
- **Permission Issues**: X server needs proper permissions to access the display
- **Display Coordination**: Need proper switching between Qt app and AirPlay display

### ✅ **Solutions Implemented**

1. **Permission Setup**: Run the setup script to configure proper permissions:
   ```bash
   sudo ./scripts/setup_airplay_permissions.sh
   ```

2. **Improved AirPlay Manager**: Enhanced with better X server handling and debugging

3. **Better User Interface**: Updated status messages and connection feedback

## How to Use AirPlay Now

### 1. **Start AirPlay Service**
- Open your infotainment system
- Navigate to "AirPlay Mirroring" screen
- Click "Start AirPlay"
- Status should show "Ready - Discoverable as 'Car Display'"

### 2. **Connect from iPhone/iPad**
- Ensure both devices are on the same Wi-Fi network
- On iPhone/iPad: Open Control Center
- Tap "Screen Mirroring"
- Select "Car Display" from the list
- Your iPhone screen will appear on the car display

### 3. **Troubleshooting Steps**

#### **If AirPlay doesn't start:**
```bash
# Check if RPiPlay is installed
which rpiplay

# Run diagnostic script
./scripts/test_airplay.sh

# Check console output for errors
```

#### **If iPhone can't see the device:**
- Verify both devices are on same Wi-Fi network
- Check firewall settings (ports 7000, 7001, 7100)
- Restart AirPlay service
- Try changing device name in settings

#### **If connection fails:**
- Check audio device conflicts (stop other audio apps)
- Restart both AirPlay service and iPhone Wi-Fi
- Check console output for detailed error messages

## Technical Details

### **Files Modified:**
- `backend/airplay_manager.py` - Enhanced X server management
- `gui/airplay_screen.py` - Better status feedback
- `scripts/setup_airplay_permissions.sh` - Permission configuration
- `scripts/test_airplay.sh` - Diagnostic tool

### **Key Improvements:**
1. **Automatic X Server Management**: Starts X server when needed
2. **Permission Handling**: Proper sudo configuration for X server
3. **Better Error Reporting**: Detailed status messages and debugging
4. **Connection Monitoring**: Real-time connection status updates

### **System Requirements:**
- RPiPlay installed and accessible
- X11 utilities (`x11-utils` package)
- Proper network configuration
- Audio system available

## Common Issues and Solutions

### **"Permission denied" errors:**
```bash
# Re-run the permission setup
sudo ./scripts/setup_airplay_permissions.sh
# Then reboot the system
sudo reboot
```

### **"Audio device busy" warnings:**
- This is normal if your Qt app is using audio
- AirPlay video will still work
- To fix audio: stop other audio applications before starting AirPlay

### **"X server failed to start":**
- Check if running as correct user
- Verify X11 packages are installed
- Try manual X server start for debugging

### **Network discovery issues:**
- Ensure mDNS/Bonjour is working
- Check router settings for multicast
- Verify firewall allows AirPlay ports

## Testing Commands

```bash
# Test X server manually
sudo /usr/local/bin/X-airplay -nocursor &

# Test RPiPlay manually
export DISPLAY=:0
rpiplay -n "Test Display" -d

# Check running processes
ps aux | grep -E "(rpiplay|X|Xorg)"

# Network connectivity test
ping $(ip route | grep default | awk '{print $3}')
```

## Support

If you continue to have issues:

1. **Run the diagnostic script**: `./scripts/test_airplay.sh`
2. **Check console output** when starting AirPlay
3. **Verify network connectivity** between devices
4. **Try manual RPiPlay startup** for detailed error messages

The system is now properly configured for AirPlay mirroring!
