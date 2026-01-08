# gui/network_dialogs.py

import subprocess
import threading
import time
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QLineEdit, QCheckBox, QMessageBox,
    QGroupBox, QFormLayout, QListWidgetItem, QApplication, QWidget
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
        self.scanning = False

        self.setup_ui()
        self.update_status()

        # Timer for updating status and device list
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_timer_tick)
        self.update_timer.start(2000) # Update every 2 seconds

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
        
        self.disconnect_all_button = QPushButton("Forget All")
        self.disconnect_all_button.setMinimumHeight(40)
        self.disconnect_all_button.clicked.connect(self.confirm_disconnect_all)

        self.scan_button = QPushButton("Start Scan")
        self.scan_button.setMinimumHeight(40)
        self.scan_button.clicked.connect(self.toggle_scan)

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

    def update_timer_tick(self):
        """Called periodically to update status and list."""
        self.update_status()
        self.update_device_list()

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

        # Update discoverability button
        self.update_discoverability_status()
        
        # Update Scan button text
        if self.scanning:
             self.scan_button.setText("Stop Scan")
             self.scan_button.setStyleSheet("background-color: #FF5555; color: white;")
        else:
             self.scan_button.setText("Start Scan")
             self.scan_button.setStyleSheet("")

    def update_discoverability_status(self):
        """Update the discoverability button text/style gracefully."""
        if not self.bluetooth_manager:
            return

        is_discoverable = self.bluetooth_manager.is_discoverable()
        
        # Logica del pulsante
        if is_discoverable:
            # Se visibile -> Verde
            self.toggle_discoverability_button.setText("Visible")
            self.toggle_discoverability_button.setStyleSheet("background-color: #44FF44; color: black; font-weight: bold;")
        else:
            # Se invisibile -> Normale
            self.toggle_discoverability_button.setText("Make Visible")
            self.toggle_discoverability_button.setStyleSheet("")
    
    def toggle_discoverability(self):
        """Toggle the device's discoverability status."""
        if not self.bluetooth_manager:
            return

        is_currently_discoverable = self.bluetooth_manager.is_discoverable()
        self.toggle_discoverability_button.setText("Working...")
        QApplication.processEvents() # Force UI update
        
        # Esegui l'azione opposta allo stato attuale
        success = self.bluetooth_manager.set_discoverability(not is_currently_discoverable)

        if not success:
            QMessageBox.warning(self, "Error", "Failed to change discoverability status. Check logs.")
        
        self.update_discoverability_status()

    def toggle_scan(self):
        """Toggle scanning state."""
        if not self.bluetooth_manager:
             return
        
        if self.scanning:
             self.bluetooth_manager.stop_scan()
             self.scanning = False
        else:
             self.bluetooth_manager.start_scan()
             self.scanning = True
        
        self.update_status()

    def update_device_list(self):
        """Fetches available devices and updates the list."""
        if not self.bluetooth_manager:
            return
            
        devices = self.bluetooth_manager.get_available_devices()
        
        # Store current selected item to restore if possible (optional, maybe complicated)
        self.device_list.clear()
        
        for dev in devices:
            name = dev['name']
            path = dev['path']
            connected = dev['connected']
            paired = dev['paired']
            rssi = dev['rssi']
            
            # Create a custom widget for the item
            item_widget = QWidget()
            item_layout = QHBoxLayout(item_widget)
            item_layout.setContentsMargins(5, 5, 5, 5)
            
            # Icon/Status
            status_icon = "🟢" if connected else ("🔵" if paired else "⚪️")
            label_text = f"{status_icon} {name}"
            if rssi > -100:
                 label_text += f" ({rssi} dBm)"
            
            label = QLabel(label_text)
            label.setFont(QFont("Arial", 12))
            item_layout.addWidget(label)
            item_layout.addStretch()
            
            # Action Button
            btn = QPushButton()
            btn.setFixedWidth(100)
            
            if connected:
                btn.setText("Disconnect")
                btn.clicked.connect(lambda checked, p=path: self.disconnect_device(p))
            elif paired:
                btn.setText("Connect")
                btn.clicked.connect(lambda checked, p=path: self.connect_device(p))
            else:
                btn.setText("Pair")
                btn.clicked.connect(lambda checked, p=path: self.pair_device(p))
                
            item_layout.addWidget(btn)
            
            # Forget Button (only for paired/connected)
            if paired or connected:
                 forget_btn = QPushButton("Forget")
                 forget_btn.setFixedWidth(70)
                 forget_btn.setStyleSheet("color: #FF5555;")
                 forget_btn.clicked.connect(lambda checked, p=path: self.forget_device_path(p))
                 item_layout.addWidget(forget_btn)

            # Create QListWidgetItem
            item = QListWidgetItem(self.device_list)
            item.setSizeHint(item_widget.sizeHint())
            self.device_list.addItem(item)
            self.device_list.setItemWidget(item, item_widget)

    def connect_device(self, path):
         self.bluetooth_manager.connect_device(path)
         QTimer.singleShot(500, self.update_device_list) # Update UI soon

    def disconnect_device(self, path):
         # There isn't a direct disconnect method in manager yet, but typically 'Disconnect' method on device interface
         # Use the manager to do it (we need to add disconnect_device to manager or just call DBus directly)
         # For now let's add a disconnect_device to manager if not exists, or implement here
         # Actually manager.connect_device is there. Let's assume manager.disconnect_device logic.
         # Wait, I didn't add disconnect_device to manager. I should.
         # But I can use remove_device_dbus which removes it.
         # For disconnect, we can use DBus directly here or add method.
         # Let's add disconnect_device to manager in next step if needed, or just use DBus here.
         # I'll implement a simple disconnect helper here.
         try:
            device = QDBusInterface(BLUEZ_SERVICE, path, DEVICE_IFACE, QDBusConnection.systemBus())
            device.call("Disconnect")
         except:
            pass
         QTimer.singleShot(500, self.update_device_list)

    def pair_device(self, path):
         self.bluetooth_manager.pair_device(path)
         QTimer.singleShot(500, self.update_device_list)
         
    def forget_device_path(self, path):
         self.bluetooth_manager.remove_device_dbus(path)
         QTimer.singleShot(500, self.update_device_list)

    def confirm_disconnect_all(self):
        """Show a confirmation dialog before disconnecting all devices."""
        reply = QMessageBox.question(
            self, "Confirm Action",
            "Are you sure you want to forget ALL Bluetooth devices?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Use the manager's remove method on all devices
            devices = self.bluetooth_manager.get_available_devices()
            for dev in devices:
                 if dev['paired']:
                      self.bluetooth_manager.remove_device_dbus(dev['path'])

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
    
    def closeEvent(self, event):
        """Clean up when dialog is closed."""
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
        if self.scanning and self.bluetooth_manager:
             self.bluetooth_manager.stop_scan()
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


        layout.setContentsMargins(15, 15, 15, 15)


        layout.setSpacing(10)





        # Title


        title_label = QLabel("WiFi Settings")


        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)


        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))


        layout.addWidget(title_label)





        # WiFi Control & Status Group


        control_group = QGroupBox("WiFi Status")


        control_layout = QHBoxLayout(control_group)





        self.wifi_status_label = QLabel("Checking...")


        self.wifi_status_label.setFont(QFont("Arial", 12))


        


        # Toggle Switch (QCheckBox styled)


        self.wifi_toggle = QCheckBox("Enable WiFi")


        self.wifi_toggle.setStyleSheet("""


            QCheckBox::indicator { width: 40px; height: 20px; }


            QCheckBox::indicator:checked { background-color: #44FF44; border-radius: 10px; }


            QCheckBox::indicator:unchecked { background-color: #888; border-radius: 10px; }


        """)


        self.wifi_toggle.clicked.connect(self.toggle_wifi) # Use clicked to avoid programmatic toggle loops





        self.refresh_button = QPushButton("Refresh Networks")


        self.refresh_button.clicked.connect(self.refresh_networks)





        control_layout.addWidget(self.wifi_status_label)


        control_layout.addStretch()


        control_layout.addWidget(self.wifi_toggle)


        control_layout.addWidget(self.refresh_button)





        layout.addWidget(control_group)





        # Current connection section


        current_group = QGroupBox("Current Connection")


        current_layout = QHBoxLayout(current_group)





        self.current_ssid_label = QLabel("None")


        self.current_ssid_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))


        self.disconnect_button = QPushButton("Disconnect")


        self.disconnect_button.clicked.connect(self.disconnect_current)





        current_layout.addWidget(QLabel("Connected to: "))


        current_layout.addWidget(self.current_ssid_label)


        current_layout.addStretch()


        current_layout.addWidget(self.disconnect_button)





        layout.addWidget(current_group)





        # Available networks section


        networks_group = QGroupBox("Available Networks")


        networks_layout = QVBoxLayout(networks_group)





        self.networks_list = QListWidget()


        self.networks_list.setStyleSheet("font-size: 14px; padding: 5px;")


        self.networks_list.itemDoubleClicked.connect(self.connect_to_selected)


        networks_layout.addWidget(self.networks_list)





        # Connection controls


        connect_layout = QHBoxLayout()


        self.password_input = QLineEdit()


        self.password_input.setPlaceholderText("Password (if required)")


        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)


        self.password_input.mousePressEvent = lambda event: self.show_keyboard(self.password_input)


        


        self.show_password_check = QCheckBox("Show")


        self.show_password_check.toggled.connect(self.toggle_password_visibility)


        


        self.connect_button = QPushButton("Connect")


        self.connect_button.setMinimumHeight(40)


        self.connect_button.clicked.connect(self.connect_to_selected)





        connect_layout.addWidget(self.password_input)


        connect_layout.addWidget(self.show_password_check)


        connect_layout.addWidget(self.connect_button)





        networks_layout.addLayout(connect_layout)


        layout.addWidget(networks_group)





        # Close button


        close_button = QPushButton("Close")


        close_button.setMinimumHeight(40)


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


        self.wifi_status_label.setText("WiFi is ON" if enabled else "WiFi is OFF")


        self.wifi_status_label.setStyleSheet(f"color: {'#44FF44' if enabled else '#FF5555'}; font-weight: bold;")


        


        # Block signals to prevent triggering toggle_wifi logic


        self.wifi_toggle.blockSignals(True)


        self.wifi_toggle.setChecked(enabled)


        self.wifi_toggle.setText("Enabled" if enabled else "Disabled")


        self.wifi_toggle.blockSignals(False)


        


        self.networks_list.setEnabled(enabled)


        self.connect_button.setEnabled(enabled)


        self.refresh_button.setEnabled(enabled)


        self.disconnect_button.setEnabled(enabled)





    def toggle_wifi(self):


        """Handle toggle switch click."""


        should_enable = self.wifi_toggle.isChecked()


        


        if self.wifi_manager:


            if should_enable:


                self.wifi_status_label.setText("Enabling...")


                self.wifi_manager.enable_wifi()


            else:


                self.wifi_status_label.setText("Disabling...")


                self.wifi_manager.disable_wifi()


        


        # Status update will come via signal





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





            item_text = f"{ssid}   {signal_bars} {signal}%   {security_text}"





            item = QListWidgetItem(item_text)


            item.setData(Qt.ItemDataRole.UserRole, network)


            self.networks_list.addItem(item)





    def on_connection_changed(self, connected, ssid):


        """Handle connection status change."""


        if connected:


            self.current_ssid_label.setText(ssid)


            self.current_ssid_label.setStyleSheet("color: #44FF44;")


            self.disconnect_button.setEnabled(True)


        else:


            self.current_ssid_label.setText("None")


            self.current_ssid_label.setStyleSheet("color: gray;")


            self.disconnect_button.setEnabled(False)





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





        # Attempt connection (Run in background or make async in future if blocking UI too much)


        # For now, it's blocking but calls subprocess which has timeout.


        QApplication.processEvents() # Refresh UI before blocking call


        


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

