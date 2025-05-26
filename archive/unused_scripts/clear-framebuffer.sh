#!/bin/bash

# Clear the framebuffer and prepare for GUI application
# This script runs early in the boot process

# Clear the framebuffer
if [ -c /dev/fb0 ]; then
    # Get framebuffer info
    FB_SIZE=$(cat /sys/class/graphics/fb0/virtual_size 2>/dev/null || echo "1024,600")
    FB_WIDTH=$(echo $FB_SIZE | cut -d, -f1)
    FB_HEIGHT=$(echo $FB_SIZE | cut -d, -f2)

    # Calculate buffer size (assuming 32-bit color depth)
    BUFFER_SIZE=$((FB_WIDTH * FB_HEIGHT * 4))

    # Clear framebuffer to black
    dd if=/dev/zero of=/dev/fb0 bs=$BUFFER_SIZE count=1 2>/dev/null
fi

# Hide cursor on all VTs
for vt in /dev/tty[1-6]; do
    if [ -c "$vt" ]; then
        echo -e "\033[?25l" > "$vt" 2>/dev/null
        # Clear the VT
        echo -e "\033[2J\033[H" > "$vt" 2>/dev/null
        # Switch to graphics mode
        echo -e "\033[?1c" > "$vt" 2>/dev/null
    fi
done

# Clear console and switch to graphics mode
clear > /dev/tty1 2>/dev/null
echo -e "\033[2J\033[H" > /dev/tty1 2>/dev/null

# Disable console blanking
echo 0 > /sys/class/graphics/fbcon/cursor_blink 2>/dev/null || true
echo 1 > /sys/module/kernel/parameters/consoleblank 2>/dev/null || true

# Note: Removed chvt command as it causes display issues

exit 0
