#!/bin/bash

# Script to set up runtime directory for the pi user
# This should be run at boot time before the infotainment service starts

# Create XDG_RUNTIME_DIR for pi user
mkdir -p /tmp/runtime-pi
chown pi:pi /tmp/runtime-pi
chmod 700 /tmp/runtime-pi

echo "Runtime directory setup complete"
