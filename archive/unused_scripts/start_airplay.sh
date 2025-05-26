#!/bin/bash

# Script to start RPiPlay for AirPlay mirroring
# This script should be run from the project directory

# Set error handling
set -e

# Configuration
DISPLAY=:0
AIRPLAY_NAME="Car Display"
BACKGROUND_MODE="auto"  # Options: auto, fill, fit, stretch

# Function to check if X server is running
check_x_running() {
    if ps aux | grep -v grep | grep -q -E "(Xorg.*$DISPLAY|X.*$DISPLAY)"; then
        return 0  # X is running
    else
        return 1  # X is not running
    fi
}

# Function to check if RPiPlay is installed
check_rpiplay_installed() {
    if command -v rpiplay &> /dev/null; then
        return 0  # RPiPlay is installed
    else
        return 1  # RPiPlay is not installed
    fi
}

# Function to ensure X server is running
ensure_x_server() {
    if ! check_x_running; then
        echo "Starting X server on $DISPLAY..."
        # Try different X server commands
        if command -v X &> /dev/null; then
            /usr/bin/X $DISPLAY -nocursor -nolisten tcp &
        elif command -v Xorg &> /dev/null; then
            /usr/bin/Xorg $DISPLAY -nocursor -nolisten tcp &
        else
            echo "Error: No X server found"
            return 1
        fi

        # Wait for X server to start
        sleep 3

        # Verify it started
        if check_x_running; then
            echo "X server started successfully"
            return 0
        else
            echo "Failed to start X server"
            return 1
        fi
    else
        echo "X server is already running"
        return 0
    fi
}

# Main execution
echo "=== RPiPlay AirPlay Mirroring ==="

# Check if RPiPlay is installed
if ! check_rpiplay_installed; then
    echo "Error: RPiPlay is not installed."
    echo "Please follow the installation instructions in the README."
    exit 1
fi

# Ensure X server is running
if ! ensure_x_server; then
    echo "Error: Could not start X server"
    exit 1
fi

# Set DISPLAY environment variable
export DISPLAY=$DISPLAY

# Start RPiPlay with debug output
echo "Starting RPiPlay with name '$AIRPLAY_NAME' on display $DISPLAY..."
echo "Command: rpiplay -n \"$AIRPLAY_NAME\" -b \"$BACKGROUND_MODE\" -d"

# Start RPiPlay with debug output for troubleshooting
rpiplay -n "$AIRPLAY_NAME" -b "$BACKGROUND_MODE" -d

# Exit gracefully
echo "RPiPlay exited."
