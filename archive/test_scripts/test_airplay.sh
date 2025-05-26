#!/bin/bash

# Script to test AirPlay functionality and diagnose issues
# This script should be run from the project directory

# Set error handling
set -e

# Configuration
DISPLAY=:0
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== AirPlay Diagnostics and Test ==="
echo "Current directory: $APP_DIR"
echo "Display: $DISPLAY"
echo

# Function to check if a process is running
check_process() {
    local process_name="$1"
    if ps aux | grep -v grep | grep -q "$process_name"; then
        echo "✓ $process_name is running"
        return 0
    else
        echo "✗ $process_name is NOT running"
        return 1
    fi
}

# Function to check if a command exists
check_command() {
    local cmd="$1"
    if command -v "$cmd" &> /dev/null; then
        echo "✓ $cmd is available"
        return 0
    else
        echo "✗ $cmd is NOT available"
        return 1
    fi
}

# Check system requirements
echo "--- System Requirements Check ---"
check_command "rpiplay"
check_command "X"
check_command "Xorg"
echo

# Check current processes
echo "--- Current Process Status ---"
check_process "python3 main.py"
check_process "rpiplay"
check_process "X :0"
check_process "Xorg :0"
echo

# Check display configuration
echo "--- Display Configuration ---"
echo "DISPLAY environment variable: ${DISPLAY:-'not set'}"
if [ -n "$DISPLAY" ]; then
    export DISPLAY=$DISPLAY
    if xdpyinfo &>/dev/null; then
        echo "✓ X server is accessible on $DISPLAY"
        echo "Display info:"
        xdpyinfo | head -10
    else
        echo "✗ X server is NOT accessible on $DISPLAY"
    fi
else
    echo "⚠ DISPLAY not set, setting to :0"
    export DISPLAY=:0
fi
echo

# Check audio configuration
echo "--- Audio Configuration ---"
if command -v aplay &> /dev/null; then
    echo "Available audio devices:"
    aplay -l 2>/dev/null || echo "No audio devices found"
else
    echo "aplay not available"
fi
echo

# Check network configuration
echo "--- Network Configuration ---"
echo "Network interfaces:"
ip addr show | grep -E "(inet |UP)" | head -10
echo

# Test X server startup
echo "--- Testing X Server ---"
if ! check_process "X :0" && ! check_process "Xorg :0"; then
    echo "Starting X server for testing..."
    /usr/bin/X :0 -nocursor -nolisten tcp &
    X_PID=$!
    sleep 3
    
    if check_process "X :0"; then
        echo "✓ X server started successfully"
        STARTED_X=true
    else
        echo "✗ Failed to start X server"
        STARTED_X=false
    fi
else
    echo "X server already running"
    STARTED_X=false
fi
echo

# Test RPiPlay startup
echo "--- Testing RPiPlay ---"
if ! check_process "rpiplay"; then
    echo "Starting RPiPlay for testing..."
    export DISPLAY=:0
    timeout 10s rpiplay -n "Test Display" -d &
    RPIPLAY_PID=$!
    sleep 3
    
    if check_process "rpiplay"; then
        echo "✓ RPiPlay started successfully"
        echo "Your device should now be discoverable as 'Test Display'"
        echo "Try connecting from your iPhone/iPad"
        echo "Press Ctrl+C to stop the test"
        
        # Wait for user input or timeout
        read -t 30 -p "Press Enter when done testing (or wait 30 seconds)..." || true
        
        # Stop RPiPlay
        kill $RPIPLAY_PID 2>/dev/null || true
        echo "RPiPlay test stopped"
    else
        echo "✗ Failed to start RPiPlay"
        echo "Check the logs above for error messages"
    fi
else
    echo "RPiPlay already running"
fi
echo

# Cleanup
if [ "$STARTED_X" = true ]; then
    echo "Stopping test X server..."
    kill $X_PID 2>/dev/null || true
fi

echo "--- Recommendations ---"
echo "1. Ensure your Raspberry Pi and iPhone/iPad are on the same network"
echo "2. Make sure your infotainment system is running before starting AirPlay"
echo "3. Check that no firewall is blocking AirPlay ports (TCP 7000, 7001, 7100)"
echo "4. Try restarting the AirPlay service if connection fails"
echo "5. Check the console output for detailed error messages"
echo
echo "=== Diagnostics Complete ==="
