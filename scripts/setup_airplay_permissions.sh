#!/bin/bash

# Script to set up proper permissions for AirPlay functionality
# This script should be run with sudo

# Set error handling
set -e

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (use sudo)"
  exit 1
fi

echo "=== Setting up AirPlay Permissions ==="

# Add pi user to video group for framebuffer access
echo "Adding pi user to video group..."
usermod -a -G video pi

# Create udev rule for console access
echo "Creating udev rule for console access..."
cat > /etc/udev/rules.d/99-console-access.rules << 'EOF'
# Allow members of video group to access console
KERNEL=="tty[0-9]*", GROUP="video", MODE="0664"
SUBSYSTEM=="vc-mem", GROUP="video", MODE="0664"
EOF

# Create X11 wrapper script that doesn't require console access
echo "Creating X11 wrapper script..."
cat > /usr/local/bin/X-airplay << 'EOF'
#!/bin/bash
# X11 wrapper for AirPlay that uses existing framebuffer
export DISPLAY=:0
exec /usr/bin/Xorg :0 -novtswitch -sharevts -nolisten tcp "$@"
EOF

chmod +x /usr/local/bin/X-airplay

# Create sudoers rule for X server
echo "Creating sudoers rule for X server..."
cat > /etc/sudoers.d/airplay-x11 << 'EOF'
# Allow pi user to start X server for AirPlay
pi ALL=(root) NOPASSWD: /usr/bin/X, /usr/bin/Xorg, /usr/local/bin/X-airplay
EOF

# Reload udev rules
echo "Reloading udev rules..."
udevadm control --reload-rules
udevadm trigger

echo "✓ AirPlay permissions setup complete!"
echo
echo "The following changes were made:"
echo "1. Added pi user to video group"
echo "2. Created udev rules for console access"
echo "3. Created X11 wrapper script"
echo "4. Added sudoers rule for X server"
echo
echo "You may need to reboot for all changes to take effect."
echo "After reboot, try the AirPlay functionality again."
