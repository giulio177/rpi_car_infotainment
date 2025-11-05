#!/bin/bash

# Test script for the new AirPlay popup control system

echo "=== AirPlay Popup Control Test ==="
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

# Instructions for testing the new popup system
echo "=== New Popup Control System Test ==="
echo
echo "🎯 **How the New System Works:**"
echo
echo "1. **Start AirPlay Mirroring:**"
echo "   - Go to AirPlay screen in the car infotainment"
echo "   - Press 'Start AirPlay'"
echo "   - Device becomes discoverable as 'Car Display'"
echo
echo "2. **Connect Your Device:**"
echo "   - Connect iPhone/iPad to 'Car Display'"
echo "   - Your phone screen will appear on the car display"
echo "   - A transparent click overlay is now active"
echo
echo "3. **Access Control Popup:**"
echo "   - 🖱️ **Click anywhere on the screen** during mirroring"
echo "   - A popup will appear with two options:"
echo "     • 'Continue Mirroring' - closes popup, continues AirPlay"
echo "     • 'Stop AirPlay' - stops mirroring completely"
echo "   - Popup auto-hides after 10 seconds if no action"
echo
echo "4. **Popup Features:**"
echo "   - ✅ Green 'Continue Mirroring' button"
echo "   - ❌ Red 'Stop AirPlay' button"
echo "   - Auto-hide timer (10 seconds)"
echo "   - ESC key closes popup"
echo "   - Click outside popup area is ignored"
echo

echo "=== Test Scenarios ==="
echo
echo "📋 **Test Case 1: Basic Popup**"
echo "   1. Start AirPlay and connect device"
echo "   2. Click anywhere on the mirrored screen"
echo "   3. Verify popup appears with both buttons"
echo "   4. Click 'Continue Mirroring'"
echo "   5. Verify popup disappears and mirroring continues"
echo
echo "📋 **Test Case 2: Stop AirPlay**"
echo "   1. During mirroring, click screen to show popup"
echo "   2. Click 'Stop AirPlay' button"
echo "   3. Verify mirroring stops and UI returns"
echo "   4. Verify device is no longer discoverable"
echo
echo "📋 **Test Case 3: Auto-Hide**"
echo "   1. During mirroring, click screen to show popup"
echo "   2. Wait 10 seconds without clicking anything"
echo "   3. Verify popup disappears automatically"
echo "   4. Verify mirroring continues normally"
echo
echo "📋 **Test Case 4: ESC Key**"
echo "   1. During mirroring, click screen to show popup"
echo "   2. Press ESC key"
echo "   3. Verify popup disappears"
echo "   4. Verify mirroring continues"
echo

echo "=== Troubleshooting ==="
echo
echo "🔧 **If popup doesn't appear when clicking:**"
echo "   - Check that device is actually connected and mirroring"
echo "   - Verify click overlay is active (check logs)"
echo "   - Try clicking different areas of the screen"
echo
echo "🔧 **If buttons don't work:**"
echo "   - Check Qt application logs for errors"
echo "   - Verify popup is properly created and styled"
echo "   - Try using ESC key as alternative"
echo
echo "🔧 **If AirPlay doesn't stop properly:**"
echo "   - Check RPiPlay process status"
echo "   - Verify X server is still running"
echo "   - Try manual stop from AirPlay screen"
echo

echo "=== Live Monitoring Commands ==="
echo
echo "# Monitor application logs:"
echo "journalctl -u rpi-infotainment.service -f | grep -E '(popup|overlay|click)'"
echo
echo "# Monitor all AirPlay related processes:"
echo "watch 'ps aux | grep -E \"(python3|rpiplay|X)\" | grep -v grep'"
echo
echo "# Monitor Qt application output:"
echo "journalctl -u rpi-infotainment.service -f | grep -E '(AirPlay|popup|overlay)'"
echo

echo "=== Current Status ==="
echo
echo "Main App: $(pgrep -f "python3 main.py" > /dev/null && echo "✅ Running (PID: $(pgrep -f "python3 main.py"))" || echo "❌ Not running")"
echo "RPiPlay:  $(pgrep -f "rpiplay" > /dev/null && echo "✅ Running (PID: $(pgrep -f "rpiplay"))" || echo "❌ Not running")"
echo "X Server: $(pgrep -f "X.*:0" > /dev/null && echo "✅ Running (PID: $(pgrep -f "X.*:0"))" || echo "❌ Not running")"

echo
echo "🚀 **Ready for popup testing!**"
echo "   Go to AirPlay screen → Start AirPlay → Connect device → Click screen!"
