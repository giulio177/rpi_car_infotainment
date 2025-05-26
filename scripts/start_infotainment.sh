#!/bin/bash

# Script to start the RPi Car Infotainment system with a minimal X server
# This script should be run from the project directory

# Set error handling
set -e

# Configuration
DISPLAY=:0
XSERVER_ARGS="-nocursor"  # Hide cursor by default
RESOLUTION="1024x600"     # Default resolution for RPi touchscreens
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(dirname "$SCRIPT_DIR")"  # Project root directory
VENV_DIR="$APP_DIR/venv"  # Virtual environment directory

# Function to check if X server is already running
check_x_running() {
    if ps aux | grep -v grep | grep -q "Xorg.*$DISPLAY"; then
        return 0  # X is running
    else
        return 1  # X is not running
    fi
}

# Function to start X server if not already running
start_x_server() {
    if ! check_x_running; then
        echo "Starting X server on $DISPLAY..."
        # Start X server in the background
        /usr/bin/Xorg $DISPLAY $XSERVER_ARGS &
        sleep 2  # Give X server time to start
    else
        echo "X server already running on $DISPLAY"
    fi
}

# Function to activate virtual environment
activate_venv() {
    if [ -d "$VENV_DIR" ] && [ -f "$VENV_DIR/bin/activate" ]; then
        echo "Activating virtual environment..."
        source "$VENV_DIR/bin/activate"
    else
        echo "Error: Virtual environment not found at $VENV_DIR"
        exit 1
    fi
}

# Function to start the application
start_application() {
    echo "Starting RPi Car Infotainment application..."
    # Change to the project root directory
    cd "$APP_DIR"

    # Set Qt platform based on environment
    if [ -c /dev/fb0 ] && [ -w /dev/fb0 ]; then
        echo "Using linuxfb platform (framebuffer available and writable)"
        export QT_QPA_PLATFORM=linuxfb
    else
        echo "Framebuffer not available or not writable, using eglfs platform"
        export QT_QPA_PLATFORM=eglfs
    fi

    # Start the application
    python3 main.py
}

# Clear screen and hide cursor
clear
echo -e "\033[?25l"  # Hide cursor

# Wait for framebuffer to be ready (when running as service)
if [ -n "$SYSTEMD_EXEC_PID" ]; then
    echo "Running as systemd service, waiting for framebuffer..."
    sleep 5
    # Check if framebuffer is available
    if [ ! -c /dev/fb0 ]; then
        echo "Warning: Framebuffer /dev/fb0 not available"
    fi
fi

# Main execution
echo "=== RPi Car Infotainment Launcher ==="
echo "Current directory: $APP_DIR"

# Note: Using Qt platform for embedded systems, no X server needed
echo "Using Qt platform for direct framebuffer access"

# Activate virtual environment
activate_venv

# Start application
start_application

# Exit gracefully
echo "Application exited."
