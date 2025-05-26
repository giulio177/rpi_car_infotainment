#!/bin/bash

# Test script for AirPlay video mirroring with popup controls

echo "=== AirPlay Video Mirroring Test ==="
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

echo "=== Video Mirroring with Popup Controls ==="
echo
echo "🎯 **How the New System Works:**"
echo
echo "1. **Start AirPlay:**"
echo "   - Go to AirPlay screen and press 'Start AirPlay'"
echo "   - X server starts automatically"
echo "   - Device becomes discoverable as 'Car Display'"
echo "   - UI may briefly show black screen during X server startup"
echo
echo "2. **Connect Device:**"
echo "   - Connect iPhone/iPad to 'Car Display'"
echo "   - Phone screen appears on car display (FULL VIDEO MIRRORING)"
echo "   - After 2 seconds, transparent click overlay activates"
echo
echo "3. **Control During Mirroring:**"
echo "   - 🖱️ **Click anywhere on the mirrored screen**"
echo "   - Popup appears with options:"
echo "     • 'Continue Mirroring' - close popup, keep mirroring"
echo "     • 'Stop AirPlay' - stop mirroring completely"
echo "   - Popup auto-hides after 10 seconds"
echo
echo "4. **Disconnect Device:**"
echo "   - When device disconnects, system automatically:"
echo "     • Clears framebuffer"
echo "     • Restores Qt UI"
echo "     • Hides all overlays"
echo

echo "=== Test Scenarios ==="
echo
echo "📋 **Test Case 1: Full Video Mirroring**"
echo "   1. Start AirPlay from car interface"
echo "   2. Connect iPhone/iPad"
echo "   3. ✅ Verify phone screen appears on car display"
echo "   4. ✅ Verify video content plays smoothly"
echo "   5. ✅ Verify audio works"
echo
echo "📋 **Test Case 2: Popup Control Access**"
echo "   1. During mirroring, click anywhere on screen"
echo "   2. ✅ Verify popup appears with control options"
echo "   3. Click 'Continue Mirroring'"
echo "   4. ✅ Verify popup disappears, mirroring continues"
echo
echo "📋 **Test Case 3: Stop via Popup**"
echo "   1. During mirroring, click screen to show popup"
echo "   2. Click 'Stop AirPlay'"
echo "   3. ✅ Verify mirroring stops"
echo "   4. ✅ Verify car UI returns"
echo "   5. ✅ Verify device no longer discoverable"
echo
echo "📋 **Test Case 4: Auto-Recovery**"
echo "   1. During mirroring, disconnect device"
echo "   2. ✅ Verify car UI returns automatically"
echo "   3. ✅ Verify no black screen or freezing"
echo "   4. ✅ Verify system remains responsive"
echo

echo "=== Expected Behavior ==="
echo
echo "✅ **Video Mirroring:** Full phone screen visible on car display"
echo "✅ **Audio Streaming:** Phone audio plays through car speakers"
echo "✅ **Touch Control:** Click screen to access controls"
echo "✅ **Popup Interface:** Clear options to continue or stop"
echo "✅ **Auto-Recovery:** Clean return to UI on disconnect"
echo "✅ **No Freezing:** System remains stable throughout"
echo

echo "=== Potential Issues & Solutions ==="
echo
echo "🔧 **If black screen persists:**"
echo "   - X server may be starting slowly"
echo "   - Wait 5-10 seconds for initialization"
echo "   - Check X server logs: journalctl -f | grep X"
echo
echo "🔧 **If video doesn't appear:**"
echo "   - Verify both devices on same Wi-Fi"
echo "   - Check RPiPlay logs: journalctl -u rpi-infotainment.service -f"
echo "   - Try disconnecting and reconnecting device"
echo
echo "🔧 **If popup doesn't appear:**"
echo "   - Ensure device is actually connected and streaming"
echo "   - Try clicking different areas of screen"
echo "   - Check that click overlay is active"
echo
echo "🔧 **If system freezes on disconnect:**"
echo "   - This should be fixed with new recovery system"
echo "   - If it still happens, restart service manually"
echo

echo "=== Monitoring Commands ==="
echo
echo "# Monitor all logs:"
echo "journalctl -u rpi-infotainment.service -f"
echo
echo "# Monitor X server:"
echo "journalctl -f | grep X"
echo
echo "# Monitor processes:"
echo "watch 'ps aux | grep -E \"(python3|rpiplay|X)\" | grep -v grep'"
echo
echo "# Monitor AirPlay discovery:"
echo "avahi-browse -t _airplay._tcp"
echo

echo "=== Current Status ==="
echo
echo "Main App: $(pgrep -f "python3 main.py" > /dev/null && echo "✅ Running (PID: $(pgrep -f "python3 main.py"))" || echo "❌ Not running")"
echo "RPiPlay:  $(pgrep -f "rpiplay" > /dev/null && echo "✅ Running (PID: $(pgrep -f "rpiplay"))" || echo "❌ Not running (starts when needed)")"
echo "X Server: $(pgrep -f "X.*:0" > /dev/null && echo "✅ Running (PID: $(pgrep -f "X.*:0"))" || echo "❌ Not running (starts when needed)")"

echo
echo "🚀 **Video Mirroring Ready!**"
echo "   Go to AirPlay screen → Start AirPlay → Connect device → See phone screen!"
echo "   Click screen during mirroring to access controls! 📱🖱️"
