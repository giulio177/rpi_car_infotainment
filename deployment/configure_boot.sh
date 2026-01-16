#!/bin/bash

# This script configures the Raspberry Pi's boot settings for faster startup.

CONFIG_FILE="/boot/firmware/config.txt"

# Function to add or replace a setting in the config file
set_config() {
  local key="$1"
  local value="$2"
  # Check if the key exists, ignoring leading/trailing whitespace
  if grep -q -E "^\s*${key}\s*=" "$CONFIG_FILE"; then
    # Key exists, so replace its value using sed.
    # The regex allows for whitespace around the '='.
    sudo sed -i "s/^\s*${key}\s*=.*/${key}=${value}/" "$CONFIG_FILE"
    echo "Updated '${key}' to '${value}' in ${CONFIG_FILE}"
  else
    # Key does not exist, so append it to the file.
    echo "${key}=${value}" | sudo tee -a "$CONFIG_FILE" > /dev/null
    echo "Added '${key}=${value}' to ${CONFIG_FILE}"
  fi
}

# Function to add a specific line to the config file if it's not already there
add_line_if_not_exists() {
  local line="$1"
  # Check for an exact match of the line
  if ! grep -Fxq "$line" "$CONFIG_FILE"; then
    # Line does not exist, so append it.
    echo "$line" | sudo tee -a "$CONFIG_FILE" > /dev/null
    echo "Added '${line}' to ${CONFIG_FILE}"
  else
    echo "'${line}' already exists in ${CONFIG_FILE}"
  fi
}

echo "Applying boot configurations..."

# Disable the splash screen
set_config "disable_splash" "1"

# Set boot delay to 0 seconds
set_config "boot_delay" "0"

# Set GPIO 17 to output and high to keep the device powered
add_line_if_not_exists "gpio=17=op,dh"

echo "Boot configuration applied successfully."
echo "Please reboot for the changes to take effect."



# This script configures the Bluetooth discoverable timeout on a Raspberry Pi.
# It sets the timeout to 0, meaning the device will stay discoverable until
# manually turned off. This gives the application full control over the timeout.

# Path to the Bluetooth configuration file
CONFIG_FILE="/etc/bluetooth/main.conf"

# Check if the config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Bluetooth config file not found at $CONFIG_FILE"
    echo "This script is intended to be run on a Raspberry Pi with standard Bluetooth configurations."
    exit 1
fi

echo "Configuring Bluetooth discoverable timeout in $CONFIG_FILE..."

# Check if DiscoverableTimeout is already present (commented or not)
if grep -q "^\s*#*\s*DiscoverableTimeout" "$CONFIG_FILE"; then
    # It exists, so we uncomment and set its value to 0.
    # This command first removes any leading '#' and whitespace, then sets the value.
    sudo sed -i 's/^\s*#*\s*DiscoverableTimeout\s*=.*/DiscoverableTimeout = 0/' "$CONFIG_FILE"
    echo "Updated DiscoverableTimeout to 0."
else
    # The setting is not present at all. We need to add it.
    # We will add it under the [General] section.
    # Check if [General] section exists
    if grep -q "^\s*\[General\]" "$CONFIG_FILE"; then
        # Add the timeout setting right after the [General] line.
        sudo sed -i '/^\s*\[General\]/a DiscoverableTimeout = 0' "$CONFIG_FILE"
        echo "Added DiscoverableTimeout = 0 under [General] section."
    else
        # The [General] section is missing, which is highly unusual.
        # We'll just append it to the end of the file as a fallback.
        echo "Warning: [General] section not found. Appending configuration to the end of the file."
        echo -e "\n[General]\nDiscoverableTimeout = 0" | sudo tee -a "$CONFIG_FILE" > /dev/null
    fi
fi

echo "Bluetooth configuration updated successfully."
echo "Please restart the Bluetooth service ('sudo systemctl restart bluetooth') or reboot for the changes to take effect."
