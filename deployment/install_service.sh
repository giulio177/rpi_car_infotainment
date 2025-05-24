#!/bin/bash

# Script to install the RPi Car Infotainment service
# This script should be run with sudo

# Set error handling
set -e

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (use sudo)"
  exit 1
fi

# Configuration
SERVICE_NAME="rpi-infotainment"
SERVICE_FILE="$SERVICE_NAME.service"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_PATH="$SCRIPT_DIR/$SERVICE_FILE"
SYSTEMD_PATH="/etc/systemd/system/$SERVICE_FILE"

# Check if service file exists
if [ ! -f "$SERVICE_PATH" ]; then
  echo "Error: Service file not found at $SERVICE_PATH"
  exit 1
fi

# Copy service file to systemd directory
echo "Installing service file to $SYSTEMD_PATH..."
cp "$SERVICE_PATH" "$SYSTEMD_PATH"
chmod 644 "$SYSTEMD_PATH"

# Reload systemd
echo "Reloading systemd..."
systemctl daemon-reload

# Enable service to start on boot
echo "Enabling service to start on boot..."
systemctl enable "$SERVICE_NAME"

# Start service
echo "Starting service..."
systemctl start "$SERVICE_NAME"

# Check service status
echo "Service status:"
systemctl status "$SERVICE_NAME"

echo "Installation complete!"
echo "You can manage the service with:"
echo "  sudo systemctl start $SERVICE_NAME"
echo "  sudo systemctl stop $SERVICE_NAME"
echo "  sudo systemctl restart $SERVICE_NAME"
echo "  sudo systemctl status $SERVICE_NAME"
