# gui/network_dialogs.py

import subprocess
import threading
import time
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QLineEdit, QCheckBox, QMessageBox,
    QGroupBox, QFormLayout, QListWidgetItem
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
        """Setup the Bluetooth dialog UI (Compact Version)."""
        # Layout principale
        layout = QVBoxLayout(self)
        layout.setSpacing(10)  # Riduce spazio tra gli elementi
        layout.setContentsMargins(15, 15, 15, 15)

        # 1. Titolo (Semplificato)
        title_label = QLabel("Bluetooth Settings")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title_label)

        # 2. PANNELLO DI CONTROLLO (Stato + Pulsanti)
        control_group = QGroupBox("Control Panel")
        control_layout = QVBoxLayout(control_group)
        control_layout.setSpacing(8)

        # A) Grande Label di Stato (quella che cambia colore)
        self.status_label = QLabel("Disconnected")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-weight: bold; font-size: 18px; color: gray; margin: 5px;")
        control_layout.addWidget(self.status_label)

        # B) Riga Pulsanti Azione (Visibilità | Disconnetti | Scan)
        # Li mettiamo in orizzontale per risparmiare spazio
        actions_layout = QHBoxLayout()
        
        self.toggle_discoverability_button = QPushButton("Loading...")
        self.toggle_discoverability_button.setMinimumHeight(40) # Pulsanti comodi per il touch
        self.toggle_discoverability_button.clicked.connect(self.toggle_discoverability)
        
        self.disconnect_all_button = QPushButton("Disconnect All")
        self.disconnect_all_button.setMinimumHeight(40)
        self.disconnect_all_button.clicked.connect(self.confirm_disconnect_all)

        self.scan_button = QPushButton("Scan Devices")
        self.scan_button.setMinimumHeight(40)
        self.scan_button.clicked.connect(self.scan_devices)

        actions_layout.addWidget(self.toggle_discoverability_button)
        actions_layout.addWidget(self.disconnect_all_button)
        actions_layout.addWidget(self.scan_button)
        control_layout.addLayout(actions_layout)

        # C) Riga Rinonima (Compatta)
        rename_layout = QHBoxLayout()
        self.device_name_input = QLineEdit()
        self.device_name_input.setPlaceholderText("Car Audio System")
        self.device_name_input.mousePressEvent = lambda event: self.show_keyboard(self.device_name_input)
        
        self.set_name_button = QPushButton("Set Name")
        self.set_name_button.clicked.connect(self.set_device_name)
        
        rename_layout.addWidget(QLabel("Name:"))
        rename_layout.addWidget(self.device_name_input)
        rename_layout.addWidget(self.set_name_button)
        control_layout.addLayout(rename_layout)

        layout.addWidget(control_group)

        # 3. LISTA DISPOSITIVI (Prende tutto lo spazio rimanente)
        device_group = QGroupBox("Available Devices")
        device_layout = QVBoxLayout(device_group)
        device_layout.setContentsMargins(5, 5, 5, 5) # Meno bordi interni
        
        self.device_list = QListWidget()
        self.device_list.setStyleSheet("font-size: 14px;") # Testo lista leggibile
        device_layout.addWidget(self.device_list)
        
        layout.addWidget(device_group)

        # 4. Pulsante Chiudi (Bottom)
        close_button = QPushButton("Close")
        close_button.setMinimumHeight(40)
        close_button.setStyleSheet("background-color: #444; color: white;") # Un po' distinto
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

    def update_status(self):
        """Update the Bluetooth status display (Single Label Logic)."""
        if not self.bluetooth_manager:
            return

        # Verifica se c'è un dispositivo connesso
        connected = self.bluetooth_manager.connected_device_path is not None

        if not connected:
            # CASO DISCONNESSO: Scritta rossa "Disconnected"
            self.status_label.setText("Disconnected")
            self.status_label.setStyleSheet("font-weight: bold; font-size: 16px; color: #FF5555;")
        else:
            # CASO CONNESSO: Costruiamo la stringa "Nome (Batteria%)"
            
            # 1. Prendi il nome (o usa un default se vuoto)
            device_name = self.bluetooth_manager.connected_device_name
            if not device_name:
                device_name = "Unknown Device"
            
            # 2. Prendi la batteria
            battery = self.bluetooth_manager.current_battery
            
            # 3. Componi il testo
            display_text = device_name
            
            # Aggiungi la percentuale solo se il valore della batteria esiste
            if battery is not None:
                display_text += f" ({battery}%)"

            # 4. Applica il testo e il colore verde
            self.status_label.setText(display_text)
            self.status_label.setStyleSheet("font-weight: bold; font-size: 16px; color: #55FF55;")

        # Mantieni l'aggiornamento del pulsante discoverable (se serve ancora alla tua logica)
        self.update_discoverability_status()
    
    # ## MODIFICATO: Logica di aggiornamento per il pulsante unico ##
    def update_discoverability_status(self):
        """Update the discoverability button text/style gracefully."""
        if not self.bluetooth_manager:
            return

        # USA getattr PER EVITARE IL CRASH se le proprietà non esistono nel manager
        is_discoverable = getattr(self.bluetooth_manager, 'discoverable', False)
        timeout = getattr(self.bluetooth_manager, 'discoverable_timeout', 0)
        
        # Logica del pulsante
        if is_discoverable:
            # Se visibile -> Verde
            text = f"Visible ({timeout}s)" if timeout > 0 else "Visible"
            self.toggle_discoverability_button.setText(text)
            self.toggle_discoverability_button.setStyleSheet("background-color: #44FF44; color: black; font-weight: bold;")
        else:
            # Se invisibile -> Normale
            self.toggle_discoverability_button.setText("Make Visible")
            self.toggle_discoverability_button.setStyleSheet("")
    
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
            get_devices_command = ["bluetoothctl", "devices"]
            result = subprocess.run(
                get_devices_command, check=True, capture_output=True, text=True, timeout=15
            )
            
            devices_output = result.stdout
            if not devices_output.strip():
                print("Worker Thread: No known devices found.")
                return

            mac_addresses = [line.split()[1] for line in devices_output.strip().split('\n')]
            
            print(f"Worker Thread: Will remove these MACs: {mac_addresses}")

            import re
            mac_regex = re.compile(r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$")
            for mac in mac_addresses:
                if not mac_regex.match(mac):
                    print(f"Worker Thread: Skipping invalid MAC address: {mac}")
                    continue
                print(f"Worker Thread: Removing {mac}...")
                subprocess.run(
                    ["bluetoothctl", "remove", mac], check=True, capture_output=True, text=True, timeout=15
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