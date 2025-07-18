# gui/network_dialogs.py

import subprocess
import threading
import time
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QLineEdit, QCheckBox, QMessageBox,
    QGroupBox, QFormLayout
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont


class BluetoothDialog(QDialog):
    """Dialog for Bluetooth settings and device management."""

    def __init__(self, bluetooth_manager, parent=None):
        super().__init__(parent)
        self.bluetooth_manager = bluetooth_manager
        self.setWindowTitle("Bluetooth Settings")
        self.setModal(True)
        self.resize(600, 500)
        self.setObjectName("networkDialog")

        self.setup_ui()
        self.update_status()

        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(2000)

    def setup_ui(self):
        """Setup the Bluetooth dialog UI."""
        layout = QVBoxLayout(self)

        title_label = QLabel("Bluetooth Settings")
        title_label.setObjectName("dialogTitle")
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        title_label.setFont(font)
        layout.addWidget(title_label)

        status_group = QGroupBox("Status")
        status_layout = QFormLayout(status_group)
        self.status_label = QLabel("Checking...")
        self.connected_device_label = QLabel("None")
        self.battery_label = QLabel("N/A")
        status_layout.addRow("Bluetooth:", self.status_label)
        status_layout.addRow("Connected Device:", self.connected_device_label)
        status_layout.addRow("Battery Level:", self.battery_label)
        layout.addWidget(status_group)

        discovery_group = QGroupBox("Device Control")
        discovery_layout = QVBoxLayout(discovery_group)

        discovery_status_layout = QHBoxLayout()
        discovery_status_layout.addWidget(QLabel("Status:"))
        self.discovery_status_label = QLabel("Checking...")
        discovery_status_layout.addWidget(self.discovery_status_label)
        discovery_status_layout.addStretch()
        discovery_layout.addLayout(discovery_status_layout)

        # ## MODIFICATO: Layout dei pulsanti di controllo ##
        control_buttons_layout = QHBoxLayout()
        
        # Pulsante unico per discoverability
        self.toggle_discoverability_button = QPushButton("Loading...")
        self.toggle_discoverability_button.clicked.connect(self.toggle_discoverability)
        control_buttons_layout.addWidget(self.toggle_discoverability_button)

        # Pulsante per disconnettere tutti i dispositivi
        self.disconnect_all_button = QPushButton("Disconnect All")
        self.disconnect_all_button.clicked.connect(self.confirm_disconnect_all)
        control_buttons_layout.addWidget(self.disconnect_all_button)
        
        discovery_layout.addLayout(control_buttons_layout)

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

        device_group = QGroupBox("Device Management")
        device_layout = QVBoxLayout(device_group)
        self.scan_button = QPushButton("Scan for Devices")
        self.scan_button.clicked.connect(self.scan_devices)
        device_layout.addWidget(self.scan_button)
        self.device_list = QListWidget()
        device_layout.addWidget(self.device_list)
        layout.addWidget(device_group)

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

    def update_status(self):
        """Update the Bluetooth status display."""
        if not self.bluetooth_manager:
            return

        connected = self.bluetooth_manager.connected_device_path is not None
        self.status_label.setText("Connected" if connected else "Disconnected")

        if connected:
            device_name = self.bluetooth_manager.connected_device_name
            self.connected_device_label.setText(device_name)
            battery = self.bluetooth_manager.current_battery
            self.battery_label.setText(f"{battery}%" if battery is not None else "N/A")
        else:
            self.connected_device_label.setText("None")
            self.battery_label.setText("N/A")

        self.update_discoverability_status()
    
    # ## MODIFICATO: Logica di aggiornamento per il pulsante unico ##
    def update_discoverability_status(self):
        """Update the discoverability status display and button."""
        if not self.bluetooth_manager:
            self.discovery_status_label.setText("Unknown (No Manager)")
            self.toggle_discoverability_button.setEnabled(False)
            return

        is_discoverable = self.bluetooth_manager.is_discoverable()
        self.toggle_discoverability_button.setEnabled(True)

        if is_discoverable:
            self.discovery_status_label.setText("Discoverable")
            self.toggle_discoverability_button.setText("Make Hidden")
        else:
            self.discovery_status_label.setText("Hidden")
            self.toggle_discoverability_button.setText("Make Discoverable")
    
    # ## NUOVO: Funzione unica per gestire il click del pulsante discoverability ##
    def toggle_discoverability(self):
        """Toggle the device's discoverability status."""
        if not self.bluetooth_manager:
            return

        is_currently_discoverable = self.bluetooth_manager.is_discoverable()
        # Esegui l'azione opposta allo stato attuale
        success = self.bluetooth_manager.set_discoverability(not is_currently_discoverable)

        # Non è più necessario mostrare un pop-up, l'UI si aggiornerà da sola
        if not success:
            QMessageBox.warning(self, "Error", "Failed to change discoverability status. Check logs.")
        
        # Forza un aggiornamento immediato dell'UI
        self.update_discoverability_status()

    # ## NUOVO: Funzioni per il pulsante "Disconnect All" ##
    def confirm_disconnect_all(self):
        """Show a confirmation dialog before disconnecting all devices."""
        reply = QMessageBox.question(
            self, "Confirm Action",
            "Are you sure you want to make this Raspberry Pi forget all saved Bluetooth devices?\n"
            "You will need to pair them again.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Avvia la funzione in un thread separato per non bloccare la GUI
            thread = threading.Thread(target=self._disconnect_all_devices_worker)
            thread.start()

    def _disconnect_all_devices_worker(self):
        """
        Worker function to remove all known Bluetooth devices.
        This runs in a background thread.
        """
        print("Worker Thread: Starting removal of all Bluetooth devices...")
        try:
            get_devices_command = "bluetoothctl devices"
            result = subprocess.run(
                get_devices_command, shell=True, check=True, capture_output=True, text=True, timeout=15
            )
            
            devices_output = result.stdout
            if not devices_output.strip():
                print("Worker Thread: No known devices found.")
                return

            mac_addresses = [line.split()[1] for line in devices_output.strip().split('\n')]
            
            print(f"Worker Thread: Will remove these MACs: {mac_addresses}")

            for mac in mac_addresses:
                print(f"Worker Thread: Removing {mac}...")
                remove_command = f"bluetoothctl remove {mac}"
                subprocess.run(
                    remove_command, shell=True, check=True, capture_output=True, text=True, timeout=15
                )
                time.sleep(0.5)
            
            print("Worker Thread: All devices removed successfully.")

        except Exception as e:
            print(f"Worker Thread: An error occurred during device removal: {e}")


    # Le altre funzioni (set_device_name, show_keyboard, ecc.) rimangono invariate...
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

    def on_wifi_status_changed(self, enabled):
        """Handle WiFi status change."""
        self.wifi_status_label.setText("Enabled" if enabled else "Disabled")
        self.enable_button.setEnabled(not enabled)
        self.disable_button.setEnabled(enabled)
        self.networks_list.setEnabled(enabled)
        self.connect_button.setEnabled(enabled)
        self.refresh_button.setEnabled(enabled)

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