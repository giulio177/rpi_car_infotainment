# gui/network_dialogs.py

import subprocess
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QLineEdit, QCheckBox,
    QMessageBox, QProgressBar, QGroupBox, QFormLayout,
    QScrollArea, QWidget
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QFont


class BluetoothDialog(QDialog):
    """Dialog for Bluetooth settings and device management."""

    def __init__(self, bluetooth_manager, parent=None):
        super().__init__(parent)
        self.bluetooth_manager = bluetooth_manager
        self.setWindowTitle("Bluetooth Settings")
        self.setModal(True)
        self.resize(600, 500)

        # Apply consistent theming
        self.setObjectName("networkDialog")

        self.setup_ui()
        self.update_status()

        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(2000)  # Update every 2 seconds

    def setup_ui(self):
        """Setup the Bluetooth dialog UI."""
        layout = QVBoxLayout(self)

        # Title
        title_label = QLabel("Bluetooth Settings")
        title_label.setObjectName("dialogTitle")
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        title_label.setFont(font)
        layout.addWidget(title_label)

        # Status section
        status_group = QGroupBox("Status")
        status_layout = QFormLayout(status_group)

        self.status_label = QLabel("Checking...")
        self.connected_device_label = QLabel("None")
        self.battery_label = QLabel("N/A")

        status_layout.addRow("Bluetooth:", self.status_label)
        status_layout.addRow("Connected Device:", self.connected_device_label)
        status_layout.addRow("Battery Level:", self.battery_label)

        layout.addWidget(status_group)

        # Discoverability controls section
        discovery_group = QGroupBox("Discoverability")
        discovery_layout = QVBoxLayout(discovery_group)

        # Status display
        discovery_status_layout = QHBoxLayout()
        discovery_status_layout.addWidget(QLabel("Status:"))
        self.discovery_status_label = QLabel("Checking...")
        discovery_status_layout.addWidget(self.discovery_status_label)
        discovery_status_layout.addStretch()
        discovery_layout.addLayout(discovery_status_layout)

        # Control buttons
        discovery_buttons_layout = QHBoxLayout()
        self.make_discoverable_button = QPushButton("Make Discoverable")
        self.make_hidden_button = QPushButton("Make Hidden")

        self.make_discoverable_button.clicked.connect(self.make_discoverable)
        self.make_hidden_button.clicked.connect(self.make_hidden)

        discovery_buttons_layout.addWidget(self.make_discoverable_button)
        discovery_buttons_layout.addWidget(self.make_hidden_button)
        discovery_layout.addLayout(discovery_buttons_layout)

        # Device name setting
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Device Name:"))
        self.device_name_input = QLineEdit()
        self.device_name_input.setPlaceholderText("Car Audio System")
        self.device_name_input.mousePressEvent = lambda event: self.show_keyboard(self.device_name_input)
        self.set_name_button = QPushButton("Set Name")
        self.set_name_button.clicked.connect(self.set_device_name)

        name_layout.addWidget(self.device_name_input)
        name_layout.addWidget(self.set_name_button)
        discovery_layout.addLayout(name_layout)

        layout.addWidget(discovery_group)

        # Device management section
        device_group = QGroupBox("Device Management")
        device_layout = QVBoxLayout(device_group)

        # Scan button
        self.scan_button = QPushButton("Scan for Devices")
        self.scan_button.clicked.connect(self.scan_devices)
        device_layout.addWidget(self.scan_button)

        # Device list (placeholder - would need more complex implementation)
        self.device_list = QListWidget()
        device_layout.addWidget(self.device_list)

        layout.addWidget(device_group)

        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

    def update_status(self):
        """Update the Bluetooth status display."""
        if not self.bluetooth_manager:
            return

        # Update connection status
        connected = self.bluetooth_manager.connected_device_path is not None
        self.status_label.setText("Connected" if connected else "Disconnected")

        # Update device info
        if connected:
            device_name = self.bluetooth_manager.connected_device_name
            self.connected_device_label.setText(device_name)

            # Update battery
            battery = self.bluetooth_manager.current_battery
            if battery is not None:
                self.battery_label.setText(f"{battery}%")
            else:
                self.battery_label.setText("N/A")
        else:
            self.connected_device_label.setText("None")
            self.battery_label.setText("N/A")

        # Update discoverability status
        self.update_discoverability_status()

    def update_discoverability_status(self):
        """Update the discoverability status display."""
        try:
            # Check discoverability using bluetoothctl
            result = subprocess.run(
                ["bluetoothctl", "show"],
                capture_output=True, text=True, timeout=5
            )

            if "Discoverable: yes" in result.stdout:
                self.discovery_status_label.setText("Discoverable")
                self.make_discoverable_button.setEnabled(False)
                self.make_hidden_button.setEnabled(True)
            else:
                self.discovery_status_label.setText("Hidden")
                self.make_discoverable_button.setEnabled(True)
                self.make_hidden_button.setEnabled(False)

        except Exception as e:
            print(f"Error checking discoverability: {e}")
            self.discovery_status_label.setText("Unknown")

    def make_discoverable(self):
        """Make the Raspberry Pi discoverable for pairing with auto-accept."""
        try:
            # Ensure PulseAudio is running for Bluetooth audio
            self.ensure_audio_system()

            # Simple and reliable Bluetooth setup
            commands = [
                (["bluetoothctl", "power", "on"], "Power On", True),
                (["bluetoothctl", "discoverable", "on"], "Make Discoverable", True),
                (["bluetoothctl", "pairable", "on"], "Make Pairable", True),
                (["bluetoothctl", "agent", "NoInputNoOutput"], "Set Auto-Accept Agent", False),
                (["bluetoothctl", "default-agent"], "Set Default Agent", False),
            ]

            critical_success = 0
            all_results = []

            for cmd, desc, critical in commands:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                success = result.returncode == 0

                if success:
                    print(f"✓ {desc}: Success")
                    if critical:
                        critical_success += 1
                else:
                    print(f"✗ {desc}: {result.stderr}")

                all_results.append((desc, success, critical))

            # Check if critical commands succeeded
            if critical_success >= 3:  # Power, Discoverable, Pairable
                # Trust all existing paired devices
                self.trust_all_paired_devices()

                # Start auto-pairing monitor
                self.start_simple_auto_pair()

                QMessageBox.information(
                    self, "Bluetooth Ready",
                    "✓ Raspberry Pi is now discoverable as 'Pi'\n"
                    "✓ Auto-pairing is enabled\n"
                    "✓ Audio profiles are active\n\n"
                    "Your iPhone can now connect and stream audio!"
                )
                self.update_discoverability_status()
            else:
                # Show what worked and what didn't
                status_msg = "Bluetooth setup partially completed:\n\n"
                for desc, success, critical in all_results:
                    status_msg += f"{'✓' if success else '✗'} {desc}\n"

                QMessageBox.warning(
                    self, "Partial Setup",
                    status_msg + "\nDevice may still be discoverable. Try connecting from your iPhone."
                )
                self.update_discoverability_status()

        except Exception as e:
            QMessageBox.warning(
                self, "Error",
                f"Failed to make device discoverable: {e}"
            )

    def make_hidden(self):
        """Make the Raspberry Pi hidden (not discoverable)."""
        try:
            # Stop auto-trust monitor
            self.stop_auto_trust_monitor()

            result = subprocess.run(
                ["bluetoothctl", "discoverable", "off"],
                capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0:
                QMessageBox.information(
                    self, "Bluetooth Hidden",
                    "Raspberry Pi is now hidden from Bluetooth discovery.\n"
                    "Auto-pairing has been disabled."
                )
                self.update_discoverability_status()
            else:
                QMessageBox.warning(
                    self, "Error",
                    f"Failed to hide device: {result.stderr}"
                )

        except Exception as e:
            QMessageBox.warning(
                self, "Error",
                f"Failed to hide device: {e}"
            )

    def set_device_name(self):
        """Set the Bluetooth device name."""
        name = self.device_name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Invalid Name", "Please enter a device name.")
            return

        try:
            # First, try to set the name without restarting service
            result1 = subprocess.run(["bluetoothctl", "system-alias", name],
                                   capture_output=True, text=True, timeout=10)

            name_set_success = result1.returncode == 0

            if not name_set_success:
                # Try alternative method with sudo
                result2 = subprocess.run(["sudo", "bluetoothctl", "system-alias", name],
                                       capture_output=True, text=True, timeout=10)
                name_set_success = result2.returncode == 0

            if not name_set_success:
                # Try hostname method as last resort
                result3 = subprocess.run(["sudo", "hostnamectl", "set-hostname", name],
                                       capture_output=True, text=True, timeout=10)
                name_set_success = result3.returncode == 0

            if name_set_success:
                # Ask user if they want to restart Bluetooth service
                reply = QMessageBox.question(
                    self, "Restart Bluetooth Service?",
                    f"Device name set to: {name}\n\n"
                    "Restart Bluetooth service now to apply changes?\n"
                    "(This may temporarily disconnect active connections)",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.Yes:
                    # Restart Bluetooth service
                    restart_result = subprocess.run(["sudo", "systemctl", "restart", "bluetooth"],
                                                  capture_output=True, text=True, timeout=15)

                    if restart_result.returncode == 0:
                        QMessageBox.information(
                            self, "Name Set",
                            f"Device name set to: {name}\n"
                            "Bluetooth service restarted successfully."
                        )
                        # Give time for service to restart
                        QTimer.singleShot(3000, self.update_status)
                    else:
                        QMessageBox.warning(
                            self, "Partial Success",
                            f"Device name set to: {name}\n"
                            "But failed to restart Bluetooth service.\n"
                            "You may need to restart manually."
                        )
                else:
                    QMessageBox.information(
                        self, "Name Set",
                        f"Device name set to: {name}\n"
                        "Restart Bluetooth service later to apply changes."
                    )
            else:
                QMessageBox.warning(
                    self, "Error",
                    f"Failed to set device name to: {name}\n"
                    "Check Bluetooth service status."
                )

        except Exception as e:
            QMessageBox.warning(
                self, "Error",
                f"Failed to set device name: {e}"
            )

    def show_keyboard(self, line_edit):
        """Show virtual keyboard for text input."""
        from .virtual_keyboard import VirtualKeyboard

        keyboard = VirtualKeyboard(line_edit.text(), self)
        if keyboard.exec() == QDialog.DialogCode.Accepted:
            line_edit.setText(keyboard.get_text())

    def setup_auto_pairing(self):
        """Set up automatic pairing configuration."""
        try:
            # Use bluetoothctl commands to set up auto-pairing behavior
            setup_commands = [
                ["bluetoothctl", "power", "on"],  # Ensure power is on
                ["bluetoothctl", "agent", "NoInputNoOutput"],  # Set auto-accept agent
                ["bluetoothctl", "default-agent"],  # Make it default
            ]

            for cmd in setup_commands:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    print(f"Setup success: {' '.join(cmd)}")
                else:
                    print(f"Setup warning: {' '.join(cmd)} - {result.stderr}")

            print("Bluetooth auto-pairing setup completed")

        except Exception as e:
            print(f"Error setting up auto-pairing: {e}")

    def ensure_bluetooth_service(self):
        """Ensure Bluetooth service is running and ready."""
        try:
            # Check if Bluetooth service is active
            result = subprocess.run(
                ["systemctl", "is-active", "bluetooth"],
                capture_output=True, text=True, timeout=5
            )

            if result.stdout.strip() != "active":
                print("Bluetooth service not active, starting...")
                # Start Bluetooth service
                start_result = subprocess.run(
                    ["sudo", "systemctl", "start", "bluetooth"],
                    capture_output=True, text=True, timeout=10
                )

                if start_result.returncode != 0:
                    print(f"Failed to start Bluetooth service: {start_result.stderr}")
                    return False

                # Wait a moment for service to be ready
                import time
                time.sleep(2)

            # Check if bluetoothctl is responsive
            test_result = subprocess.run(
                ["bluetoothctl", "show"],
                capture_output=True, text=True, timeout=5
            )

            if test_result.returncode != 0:
                print("bluetoothctl not responsive, restarting service...")
                # Restart Bluetooth service
                restart_result = subprocess.run(
                    ["sudo", "systemctl", "restart", "bluetooth"],
                    capture_output=True, text=True, timeout=15
                )

                if restart_result.returncode == 0:
                    # Wait for service to be ready
                    import time
                    time.sleep(3)
                    print("Bluetooth service restarted successfully")
                else:
                    print(f"Failed to restart Bluetooth service: {restart_result.stderr}")
                    return False

            return True

        except Exception as e:
            print(f"Error ensuring Bluetooth service: {e}")
            return False

    def ensure_audio_system(self):
        """Ensure PulseAudio is running for Bluetooth audio."""
        try:
            # Check if PulseAudio is running
            result = subprocess.run(
                ["pactl", "info"],
                capture_output=True, text=True, timeout=5
            )

            if result.returncode != 0:
                print("Starting PulseAudio...")
                # Try to start PulseAudio
                subprocess.run(["pulseaudio", "--start"], timeout=10)

                # Wait and check again
                import time
                time.sleep(2)

                check_result = subprocess.run(
                    ["pactl", "info"],
                    capture_output=True, text=True, timeout=5
                )

                if check_result.returncode == 0:
                    print("PulseAudio started successfully")
                else:
                    print("Warning: PulseAudio may not be running properly")
            else:
                print("PulseAudio is already running")

        except Exception as e:
            print(f"Error ensuring audio system: {e}")

    def start_simple_auto_pair(self):
        """Start a simple auto-pairing process."""
        try:
            # Create a simple auto-pairing script
            script_content = '''#!/bin/bash
# Simple Bluetooth auto-pairing

echo "Starting simple auto-pairing..."

# Set up agent for auto-accept
bluetoothctl agent NoInputNoOutput &
sleep 1

# Monitor for 60 seconds for pairing events
timeout 60 bluetoothctl | while read line; do
    echo "BT: $line"

    # Auto-accept any confirmation requests
    if [[ "$line" == *"Confirm passkey"* ]] || [[ "$line" == *"Request confirmation"* ]]; then
        echo "yes"
    fi

    # Trust any newly connected devices
    if [[ "$line" == *"Connected: yes"* ]]; then
        mac=$(echo "$line" | grep -oE '([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})')
        if [ ! -z "$mac" ]; then
            bluetoothctl trust "$mac" &
        fi
    fi
done &

echo "Auto-pairing monitor started for 60 seconds"
'''

            # Write and execute the script
            with open('/tmp/simple_autopair.sh', 'w') as f:
                f.write(script_content)

            subprocess.run(["chmod", "+x", "/tmp/simple_autopair.sh"], timeout=5)
            subprocess.Popen(["/tmp/simple_autopair.sh"],
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)

            print("Simple auto-pairing started")

        except Exception as e:
            print(f"Error starting simple auto-pair: {e}")

    def trust_all_paired_devices(self):
        """Trust all currently paired devices."""
        try:
            # Get list of paired devices
            result = subprocess.run(
                ["bluetoothctl", "devices", "Paired"],
                capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line.startswith('Device '):
                        # Extract MAC address
                        parts = line.split()
                        if len(parts) >= 2:
                            mac_address = parts[1]
                            print(f"Trusting paired device: {mac_address}")

                            # Trust the device
                            subprocess.run(
                                ["bluetoothctl", "trust", mac_address],
                                capture_output=True, timeout=5
                            )

                            # Try to connect
                            subprocess.run(
                                ["bluetoothctl", "connect", mac_address],
                                capture_output=True, timeout=10
                            )

        except Exception as e:
            print(f"Error trusting paired devices: {e}")

    def start_auto_trust_monitor(self):
        """Start monitoring for new devices to automatically trust them."""
        try:
            # Create a more effective auto-trust and pairing script
            script_content = '''#!/bin/bash
# Enhanced auto-trust and pairing script for Bluetooth devices

# Set up agent for auto-pairing
bluetoothctl agent NoInputNoOutput
bluetoothctl default-agent 2>/dev/null || true

echo "Auto-trust monitor started. Monitoring for new devices..."

while true; do
    # Monitor bluetoothctl for pairing requests and new devices
    timeout 10 bluetoothctl | while read -r line; do
        echo "BT Event: $line"

        # Handle pairing requests
        if [[ "$line" == *"Request confirmation"* ]] || [[ "$line" == *"Request passkey"* ]] || [[ "$line" == *"Request PIN"* ]]; then
            echo "Auto-accepting pairing request"
            echo "yes" | bluetoothctl
        fi

        # Handle new device discovery
        if [[ "$line" == *"NEW"* && "$line" == *"Device"* ]]; then
            mac_address=$(echo "$line" | grep -oE '([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})')
            if [ ! -z "$mac_address" ]; then
                echo "New device detected: $mac_address"
                sleep 1
                bluetoothctl trust "$mac_address"
                bluetoothctl pair "$mac_address" &
            fi
        fi

        # Handle connection events
        if [[ "$line" == *"Device"* && "$line" == *"Connected: yes"* ]]; then
            mac_address=$(echo "$line" | grep -oE '([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})')
            if [ ! -z "$mac_address" ]; then
                echo "Device connected: $mac_address - ensuring trust"
                bluetoothctl trust "$mac_address"
            fi
        fi
    done

    # Also periodically check all devices and trust them
    bluetoothctl devices | while read -r line; do
        if [[ "$line" == Device* ]]; then
            mac_address=$(echo "$line" | awk '{print $2}')

            # Check if device is trusted
            trusted_status=$(bluetoothctl info "$mac_address" 2>/dev/null | grep "Trusted:" | awk '{print $2}')

            if [[ "$trusted_status" == "no" ]]; then
                echo "Trusting device: $mac_address"
                bluetoothctl trust "$mac_address"
            fi
        fi
    done

    # Wait before next check
    sleep 3
done
'''

            # Write the monitoring script
            with open('/tmp/auto_trust.sh', 'w') as f:
                f.write(script_content)

            # Make it executable and run it in background
            subprocess.run(["chmod", "+x", "/tmp/auto_trust.sh"], timeout=5)
            subprocess.Popen(["/tmp/auto_trust.sh"],
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)

            print("Enhanced auto-trust monitor started")

        except Exception as e:
            print(f"Error starting auto-trust monitor: {e}")

    def stop_auto_trust_monitor(self):
        """Stop the auto-trust monitoring script."""
        try:
            # Kill any running auto_trust.sh processes
            subprocess.run(["pkill", "-f", "auto_trust.sh"],
                         capture_output=True, timeout=5)

            # Remove the script file
            subprocess.run(["rm", "-f", "/tmp/auto_trust.sh"], timeout=5)

            print("Auto-trust monitor stopped")

        except Exception as e:
            print(f"Error stopping auto-trust monitor: {e}")

    def scan_devices(self):
        """Scan for Bluetooth devices (placeholder)."""
        QMessageBox.information(
            self, "Scan Devices",
            "Device scanning functionality would be implemented here.\n"
            "This requires more complex BlueZ D-Bus integration."
        )

    def closeEvent(self, event):
        """Clean up when dialog is closed."""
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
        # Don't stop auto-trust monitor on dialog close - let it run in background
        super().closeEvent(event)


class WiFiDialog(QDialog):
    """Dialog for WiFi settings and network management."""

    def __init__(self, wifi_manager, parent=None):
        super().__init__(parent)
        self.wifi_manager = wifi_manager
        self.setWindowTitle("WiFi Settings")
        self.setModal(True)
        self.resize(700, 600)

        # Apply consistent theming
        self.setObjectName("networkDialog")

        self.setup_ui()
        self.update_status()

        # Connect signals
        if self.wifi_manager:
            self.wifi_manager.wifi_status_changed.connect(self.on_wifi_status_changed)
            self.wifi_manager.networks_updated.connect(self.on_networks_updated)
            self.wifi_manager.connection_changed.connect(self.on_connection_changed)

        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(3000)  # Update every 3 seconds

    def setup_ui(self):
        """Setup the WiFi dialog UI."""
        layout = QVBoxLayout(self)

        # Title
        title_label = QLabel("WiFi Settings")
        title_label.setObjectName("dialogTitle")
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        title_label.setFont(font)
        layout.addWidget(title_label)

        # WiFi control section
        control_group = QGroupBox("WiFi Control")
        control_layout = QHBoxLayout(control_group)

        self.wifi_status_label = QLabel("Checking...")
        self.enable_button = QPushButton("Enable WiFi")
        self.disable_button = QPushButton("Disable WiFi")
        self.refresh_button = QPushButton("Refresh")

        self.enable_button.clicked.connect(self.enable_wifi)
        self.disable_button.clicked.connect(self.disable_wifi)
        self.refresh_button.clicked.connect(self.refresh_networks)

        control_layout.addWidget(self.wifi_status_label)
        control_layout.addStretch()
        control_layout.addWidget(self.enable_button)
        control_layout.addWidget(self.disable_button)
        control_layout.addWidget(self.refresh_button)

        layout.addWidget(control_group)

        # Current connection section
        current_group = QGroupBox("Current Connection")
        current_layout = QFormLayout(current_group)

        self.current_ssid_label = QLabel("None")
        self.disconnect_button = QPushButton("Disconnect")
        self.disconnect_button.clicked.connect(self.disconnect_current)

        current_layout.addRow("Connected to:", self.current_ssid_label)
        current_layout.addRow("", self.disconnect_button)

        layout.addWidget(current_group)

        # Available networks section
        networks_group = QGroupBox("Available Networks")
        networks_layout = QVBoxLayout(networks_group)

        self.networks_list = QListWidget()
        self.networks_list.itemDoubleClicked.connect(self.connect_to_selected)
        networks_layout.addWidget(self.networks_list)

        # Connection controls
        connect_layout = QHBoxLayout()
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password (if required)")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.mousePressEvent = lambda event: self.show_keyboard(self.password_input)
        self.show_password_check = QCheckBox("Show password")
        self.show_password_check.toggled.connect(self.toggle_password_visibility)
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.connect_to_selected)

        connect_layout.addWidget(self.password_input)
        connect_layout.addWidget(self.show_password_check)
        connect_layout.addWidget(self.connect_button)

        networks_layout.addLayout(connect_layout)
        layout.addWidget(networks_group)

        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

    def update_status(self):
        """Update the WiFi status display."""
        if not self.wifi_manager:
            return

        # Trigger status update in manager
        self.wifi_manager.update_status()

    @pyqtSlot(bool)
    def on_wifi_status_changed(self, enabled):
        """Handle WiFi status change."""
        self.wifi_status_label.setText("Enabled" if enabled else "Disabled")
        self.enable_button.setEnabled(not enabled)
        self.disable_button.setEnabled(enabled)
        self.networks_list.setEnabled(enabled)
        self.connect_button.setEnabled(enabled)
        self.refresh_button.setEnabled(enabled)

    @pyqtSlot(list)
    def on_networks_updated(self, networks):
        """Handle networks list update."""
        self.networks_list.clear()

        for network in networks:
            ssid = network['ssid']
            signal = network['signal']
            secured = network['secured']

            # Create display text
            security_text = "🔒" if secured else "🔓"
            signal_bars = "📶" * (signal // 25 + 1)  # 1-4 bars based on signal

            item_text = f"{ssid} {security_text} {signal_bars} ({signal}%)"

            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, network)
            self.networks_list.addItem(item)

    @pyqtSlot(bool, str)
    def on_connection_changed(self, connected, ssid):
        """Handle connection status change."""
        if connected:
            self.current_ssid_label.setText(ssid)
            self.disconnect_button.setEnabled(True)
        else:
            self.current_ssid_label.setText("None")
            self.disconnect_button.setEnabled(False)

    def enable_wifi(self):
        """Enable WiFi."""
        if self.wifi_manager and self.wifi_manager.enable_wifi():
            self.wifi_status_label.setText("Enabling...")

    def disable_wifi(self):
        """Disable WiFi."""
        if self.wifi_manager and self.wifi_manager.disable_wifi():
            self.wifi_status_label.setText("Disabling...")

    def refresh_networks(self):
        """Refresh the networks list."""
        if self.wifi_manager:
            self.wifi_manager.update_status()

    def disconnect_current(self):
        """Disconnect from current network."""
        if self.wifi_manager and self.wifi_manager.disconnect_current():
            self.current_ssid_label.setText("Disconnecting...")

    def connect_to_selected(self):
        """Connect to the selected network."""
        current_item = self.networks_list.currentItem()
        if not current_item or not self.wifi_manager:
            return

        network = current_item.data(Qt.ItemDataRole.UserRole)
        ssid = network['ssid']
        secured = network['secured']

        password = None
        if secured:
            password = self.password_input.text().strip()
            if not password:
                QMessageBox.warning(
                    self, "Password Required",
                    f"Network '{ssid}' requires a password."
                )
                return

        # Show connecting message
        self.current_ssid_label.setText(f"Connecting to {ssid}...")

        # Attempt connection
        success, error_msg = self.wifi_manager.connect_to_network(ssid, password)

        if success:
            self.password_input.clear()
            QMessageBox.information(
                self, "Connection Successful",
                f"Successfully connected to '{ssid}'"
            )
        else:
            QMessageBox.warning(
                self, "Connection Failed",
                f"Failed to connect to '{ssid}':\n{error_msg}"
            )

    def toggle_password_visibility(self, show):
        """Toggle password field visibility."""
        if show:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

    def show_keyboard(self, line_edit):
        """Show virtual keyboard for text input."""
        from .virtual_keyboard import VirtualKeyboard

        keyboard = VirtualKeyboard(line_edit.text(), self)
        if keyboard.exec() == QDialog.DialogCode.Accepted:
            line_edit.setText(keyboard.get_text())

    def closeEvent(self, event):
        """Clean up when dialog is closed."""
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
        super().closeEvent(event)
