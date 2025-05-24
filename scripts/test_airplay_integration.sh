#!/bin/bash

# Test script for AirPlay integration with the infotainment system

echo "=== AirPlay Integration Test ==="
echo

# Check if main application is running
echo "1. Checking main application status..."
if pgrep -f "python3 main.py" > /dev/null; then
    echo "✅ Main application is running"
    MAIN_PID=$(pgrep -f "python3 main.py")
    echo "   PID: $MAIN_PID"
else
    echo "❌ Main application is not running"
    echo "   Starting application first..."
    sudo systemctl start rpi-infotainment.service
    sleep 5
fi

echo

# Check if RPiPlay is running
echo "2. Checking RPiPlay status..."
if pgrep -f "rpiplay" > /dev/null; then
    echo "✅ RPiPlay is running"
    RPIPLAY_PID=$(pgrep -f "rpiplay")
    echo "   PID: $RPIPLAY_PID"
    
    # Show RPiPlay command line
    echo "   Command: $(ps -p $RPIPLAY_PID -o cmd --no-headers)"
else
    echo "❌ RPiPlay is not running"
fi

echo

# Check network discovery
echo "3. Checking network discovery..."
if command -v avahi-browse &> /dev/null; then
    echo "   Scanning for AirPlay services..."
    timeout 5s avahi-browse -t _airplay._tcp 2>/dev/null | grep -i "car display" && echo "✅ Car Display is discoverable" || echo "⚠️ Car Display not found in scan"
else
    echo "⚠️ avahi-browse not available for network scan"
fi

echo

# Check X server
echo "4. Checking X server status..."
if pgrep -f "X.*:0" > /dev/null; then
    echo "✅ X server is running on :0"
    X_PID=$(pgrep -f "X.*:0")
    echo "   PID: $X_PID"
else
    echo "⚠️ X server not running on :0"
fi

echo

# Show process tree
echo "5. Process tree:"
if command -v pstree &> /dev/null; then
    pstree -p $(pgrep -f "start_infotainment.sh") 2>/dev/null || echo "   Could not show process tree"
else
    echo "   pstree not available"
fi

echo

# Instructions
echo "=== Test Instructions ==="
echo "1. The main infotainment UI should be visible on the display"
echo "2. Go to AirPlay screen and start AirPlay mirroring"
echo "3. Connect your iPhone/iPad to 'Car Display'"
echo "4. You should see:"
echo "   - Phone screen content overlaid on the UI"
echo "   - Green border indicating AirPlay is active"
echo "   - UI still accessible underneath"
echo "5. When you disconnect the phone:"
echo "   - Overlay should disappear"
echo "   - Normal UI should be fully visible again"

echo
echo "=== Current Status Summary ==="
echo "Main App: $(pgrep -f "python3 main.py" > /dev/null && echo "✅ Running" || echo "❌ Not running")"
echo "RPiPlay:  $(pgrep -f "rpiplay" > /dev/null && echo "✅ Running" || echo "❌ Not running")"
echo "X Server: $(pgrep -f "X.*:0" > /dev/null && echo "✅ Running" || echo "⚠️ Not running")"

echo
echo "Test completed. Check the display for visual confirmation."
