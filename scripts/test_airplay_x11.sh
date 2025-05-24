#!/bin/bash

# Test script for AirPlay X11 approach

echo "=== AirPlay X11 Integration Test ==="
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

echo "=== X11 AirPlay Approach ==="
echo
echo "🎯 **New Strategy: RPiPlay as X11 Application**"
echo
echo "✅ **How This Solves the Problems:**"
echo "   - RPiPlay runs as normal X11 application"
echo "   - No direct framebuffer conflicts"
echo "   - X server manages both Qt and RPiPlay windows"
echo "   - Clean window management and switching"
echo "   - No system freezes on disconnect"
echo
echo "🔧 **Technical Implementation:**"
echo "   - GStreamer with X11 video sinks (xvimagesink/ximagesink)"
echo "   - DISPLAY=:0 environment for RPiPlay"
echo "   - Automatic backend selection (-b auto)"
echo "   - Proper process lifecycle management"
echo

echo "=== Expected Behavior ==="
echo
echo "1. **Start AirPlay:**"
echo "   - ✅ X server starts if not running"
echo "   - ✅ RPiPlay starts as X11 application"
echo "   - ✅ Qt UI remains visible and functional"
echo "   - ✅ Device becomes discoverable"
echo
echo "2. **Connect Device:**"
echo "   - ✅ Phone screen appears in X11 window"
echo "   - ✅ Video mirroring works properly"
echo "   - ✅ Audio streams to car speakers"
echo "   - ✅ Small notification shows mirroring is active"
echo
echo "3. **During Mirroring:**"
echo "   - ✅ Both Qt UI and video window coexist"
echo "   - ✅ Window manager handles switching"
echo "   - ✅ No conflicts or freezes"
echo "   - ✅ Full video and audio functionality"
echo
echo "4. **Disconnect Device:**"
echo "   - ✅ Video window closes cleanly"
echo "   - ✅ Qt UI remains functional"
echo "   - ✅ No system freezes"
echo "   - ✅ Notification disappears"
echo

echo "=== GStreamer Verification ==="
echo
echo "Checking GStreamer X11 support:"
if gst-inspect-1.0 xvimagesink >/dev/null 2>&1; then
    echo "✅ xvimagesink available"
else
    echo "❌ xvimagesink not available"
fi

if gst-inspect-1.0 ximagesink >/dev/null 2>&1; then
    echo "✅ ximagesink available"
else
    echo "❌ ximagesink not available"
fi

if gst-inspect-1.0 glimagesink >/dev/null 2>&1; then
    echo "✅ glimagesink available"
else
    echo "❌ glimagesink not available"
fi

echo

echo "=== Test Instructions ==="
echo
echo "📋 **Test Case 1: X11 Startup**"
echo "   1. Go to AirPlay screen in car interface"
echo "   2. Press 'Start AirPlay'"
echo "   3. ✅ Verify X server starts (check ps aux | grep X)"
echo "   4. ✅ Verify RPiPlay starts with DISPLAY=:0"
echo "   5. ✅ Verify Qt UI remains visible"
echo
echo "📋 **Test Case 2: Video Mirroring**"
echo "   1. Connect iPhone/iPad to 'Car Display'"
echo "   2. ✅ Verify video window appears"
echo "   3. ✅ Verify phone screen is visible"
echo "   4. ✅ Verify audio works"
echo "   5. ✅ Verify notification appears"
echo
echo "📋 **Test Case 3: Window Coexistence**"
echo "   1. During mirroring, try to access car UI"
echo "   2. ✅ Verify both windows can coexist"
echo "   3. ✅ Verify window switching works"
echo "   4. ✅ Verify no conflicts"
echo
echo "📋 **Test Case 4: Clean Disconnection**"
echo "   1. Disconnect device from AirPlay"
echo "   2. ✅ Verify video window closes"
echo "   3. ✅ Verify no system freeze"
echo "   4. ✅ Verify Qt UI remains functional"
echo

echo "=== Monitoring Commands ==="
echo
echo "# Monitor X server startup:"
echo "watch 'ps aux | grep X | grep -v grep'"
echo
echo "# Monitor RPiPlay with environment:"
echo "ps aux | grep rpiplay"
echo
echo "# Check X11 windows:"
echo "DISPLAY=:0 xwininfo -root -tree"
echo
echo "# Monitor GStreamer debug:"
echo "GST_DEBUG=3 # Set this before starting RPiPlay for detailed logs"
echo
echo "# Application logs:"
echo "journalctl -u rpi-infotainment.service -f"
echo

echo "=== Troubleshooting ==="
echo
echo "🔧 **If video doesn't appear:**"
echo "   - Check X server is running: ps aux | grep X"
echo "   - Check DISPLAY variable: echo \$DISPLAY"
echo "   - Check GStreamer plugins: gst-inspect-1.0 xvimagesink"
echo "   - Check RPiPlay logs for GStreamer errors"
echo
echo "🔧 **If system still freezes:**"
echo "   - Verify RPiPlay is using X11 backend"
echo "   - Check for framebuffer access attempts"
echo "   - Monitor process termination"
echo
echo "🔧 **If windows don't coexist:**"
echo "   - Check window manager configuration"
echo "   - Try manual window management with wmctrl"
echo "   - Verify X11 compositing"
echo

echo "=== Current Status ==="
echo
echo "Main App: $(pgrep -f "python3 main.py" > /dev/null && echo "✅ Running (PID: $(pgrep -f "python3 main.py"))" || echo "❌ Not running")"
echo "RPiPlay:  $(pgrep -f "rpiplay" > /dev/null && echo "✅ Running (PID: $(pgrep -f "rpiplay"))" || echo "❌ Not running (starts when needed)")"
echo "X Server: $(pgrep -f "X.*:0" > /dev/null && echo "✅ Running (PID: $(pgrep -f "X.*:0"))" || echo "❌ Not running (starts when needed)")"

echo
echo "🚀 **X11 AirPlay Ready!**"
echo "   This approach should provide video mirroring without conflicts!"
echo "   Go test it: AirPlay screen → Start AirPlay → Connect device! 📱➡️🖥️"
