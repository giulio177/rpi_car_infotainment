#!/bin/bash

# Test script for the complete AirPlay flow

echo "=== AirPlay Flow Test ==="
echo

# Function to check process
check_process() {
    local process_name="$1"
    if pgrep -f "$process_name" > /dev/null; then
        echo "✅ $process_name is running"
        return 0
    else
        echo "❌ $process_name is not running"
        return 1
    fi
}

# Check initial state
echo "1. Initial State Check:"
check_process "python3 main.py"
check_process "rpiplay"
check_process "X.*:0"

echo

# Instructions for manual testing
echo "=== Manual Test Instructions ==="
echo
echo "🎯 **Expected Behavior:**"
echo
echo "1. **Before AirPlay:**"
echo "   - You should see the car infotainment UI on the display"
echo "   - Navigate to AirPlay screen"
echo
echo "2. **Start AirPlay:**"
echo "   - Press 'Start AirPlay' button"
echo "   - UI should remain visible"
echo "   - RPiPlay should start in background"
echo "   - Device becomes discoverable as 'Car Display'"
echo
echo "3. **Connect iPhone/iPad:**"
echo "   - Open Control Center on your device"
echo "   - Tap Screen Mirroring"
echo "   - Select 'Car Display'"
echo "   - Your phone screen should appear on the car display"
echo "   - Car UI should be replaced by phone content"
echo
echo "4. **Disconnect Device:**"
echo "   - Stop screen mirroring on your device"
echo "   - OR disconnect from 'Car Display'"
echo "   - Car infotainment UI should automatically reappear"
echo "   - No manual intervention needed"
echo
echo "5. **Stop AirPlay:**"
echo "   - Press 'Stop AirPlay' button"
echo "   - RPiPlay should stop"
echo "   - Device no longer discoverable"
echo

echo "=== Troubleshooting ==="
echo
echo "🔧 **If phone screen doesn't appear:**"
echo "   - Check that X server is running: ps aux | grep 'X.*:0'"
echo "   - Check RPiPlay logs: journalctl -f | grep rpiplay"
echo "   - Ensure both devices are on same Wi-Fi network"
echo
echo "🔧 **If UI doesn't return after disconnect:**"
echo "   - Check if Qt application is still running"
echo "   - Try restarting the service: sudo systemctl restart rpi-infotainment"
echo
echo "🔧 **If AirPlay won't start:**"
echo "   - Check if RPiPlay binary exists: ls -la /home/pi/RPiPlay/build/rpiplay"
echo "   - Check permissions and dependencies"
echo

echo "=== Live Monitoring ==="
echo
echo "Run these commands in separate terminals to monitor:"
echo
echo "# Monitor main application logs:"
echo "journalctl -u rpi-infotainment.service -f"
echo
echo "# Monitor all processes:"
echo "watch 'ps aux | grep -E \"(python3|rpiplay|X)\" | grep -v grep'"
echo
echo "# Monitor network discovery:"
echo "avahi-browse -t _airplay._tcp"
echo

echo "=== Current Status ==="
echo
echo "Main App: $(pgrep -f "python3 main.py" > /dev/null && echo "✅ Running (PID: $(pgrep -f "python3 main.py"))" || echo "❌ Not running")"
echo "RPiPlay:  $(pgrep -f "rpiplay" > /dev/null && echo "✅ Running (PID: $(pgrep -f "rpiplay"))" || echo "❌ Not running")"
echo "X Server: $(pgrep -f "X.*:0" > /dev/null && echo "✅ Running (PID: $(pgrep -f "X.*:0"))" || echo "❌ Not running")"

echo
echo "🚀 **Ready for testing!** Go to the AirPlay screen and start testing."
