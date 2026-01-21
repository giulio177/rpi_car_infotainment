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

        # Timer for discoverability timeout
        self.discoverability_timer = QTimer(self)
        self.discoverability_timer.setSingleShot(True)
        self.discoverability_timer.timeout.connect(self._handle_discoverability_timeout)

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
        """Toggle the device's discoverability status and manage the timeout timer."""
        if not self.bluetooth_manager:
            return

        is_currently_discoverable = self.bluetooth_manager.is_discoverable()
        self.toggle_discoverability_button.setText("Working...")
        QApplication.processEvents()  # Force UI update

        # The action is to do the opposite of the current state
        new_state = not is_currently_discoverable
        success = self.bluetooth_manager.set_discoverability(new_state)

        if not success:
            QMessageBox.warning(self, "Error", "Failed to change discoverability status. Check logs.")
        else:
            if new_state is True:
                # If we just turned discoverability ON, start the 60-second timer
                print("Bluetooth discoverability is ON. Starting 60-second timeout.")
                self.discoverability_timer.start(60000)
            else:
                # If we just turned it OFF (manually), stop the timer
                print("Bluetooth discoverability was manually turned OFF. Stopping timer.")
                self.discoverability_timer.stop()

        self.update_discoverability_status()

    def _handle_discoverability_timeout(self):
        """Called when the discoverability timer expires."""
        print("Discoverability timeout reached. Automatically turning off discoverability.")
        
        # Check if it's still discoverable before turning it off
        if self.bluetooth_manager and self.bluetooth_manager.is_discoverable():
            self.bluetooth_manager.set_discoverability(False)
        
        # Update the UI to reflect the change
        self.update_status()

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
        """Fetches available devices and updates the list without clearing it (preserves scroll)."""
        if not self.bluetooth_manager:
            return
            
        devices = self.bluetooth_manager.get_available_devices()
        
        # 1. Map existing items by path
        existing_items = {}
        for i in range(self.device_list.count()):
            item = self.device_list.item(i)
            # Retrieve path from the widget (we need to store it there or in item data)
            # Actually we stored full network dict in item data in WiFi dialog, 
            # but here we didn't store anything in item.setData.
            # Let's fix that for future items, but for now we might have trouble identifying existing ones 
            # if we didn't store data.
            # Wait, line 611 in WiFiDialog sets UserRole. In BluetoothDialog it wasn't done.
            # We need to rely on what we can get. 
            # The previous code didn't set UserRole.
            # So, for this transition, if we can't identify, we clear. 
            # But the goal is to stop clearing.
            # So I will start setting UserRole now.
            path = item.data(Qt.ItemDataRole.UserRole)
            if path:
                existing_items[path] = item

        # 2. Update or Add items
        seen_paths = set()
        
        for dev in devices:
            name = dev['name']
            path = dev['path']
            connected = dev['connected']
            paired = dev['paired']
            rssi = dev['rssi']
            
            seen_paths.add(path)
            
            status_icon = "🟢" if connected else ("🔵" if paired else "⚪️")
            label_text = f"{status_icon} {name}"
            if rssi > -100:
                 label_text += f" ({rssi} dBm)"

            if path in existing_items:
                # UPDATE existing item
                item = existing_items[path]
                widget = self.device_list.itemWidget(item)
                
                # Update Label
                label = widget.findChild(QLabel)
                if label:
                    label.setText(label_text)
                
                # Update Buttons (Only regenerate if state changed to avoid flicker? 
                # Or just update text/connection? Simpler to recreate buttons layout part)
                # To be efficient, let's find the layout and check buttons.
                # However, connection state changes connection logic.
                # Let's rebuild the button part of the widget or just the widget content.
                # Rebuilding the widget content is safer for state consistency.
                
                # Check if state changed to decide if we need deep refresh
                last_state = item.data(Qt.ItemDataRole.UserRole + 1) # Let's store state hash
                current_state_hash = f"{connected}_{paired}"
                
                if last_state != current_state_hash:
                    # Rebuild widget content
                    new_widget = self._create_device_widget(dev)
                    self.device_list.setItemWidget(item, new_widget)
                    item.setData(Qt.ItemDataRole.UserRole + 1, current_state_hash)
                
            else:
                # ADD new item
                item = QListWidgetItem(self.device_list)
                item.setData(Qt.ItemDataRole.UserRole, path)
                item.setData(Qt.ItemDataRole.UserRole + 1, f"{connected}_{paired}")
                
                widget = self._create_device_widget(dev)
                
                item.setSizeHint(widget.sizeHint())
                self.device_list.addItem(item)
                self.device_list.setItemWidget(item, widget)

        # 3. Remove obsolete items
        for i in range(self.device_list.count() - 1, -1, -1):
            item = self.device_list.item(i)
            path = item.data(Qt.ItemDataRole.UserRole)
            if path and path not in seen_paths:
                self.device_list.takeItem(i)

    def _create_device_widget(self, dev):
        """Creates a widget for a device item."""
        name = dev['name']
        path = dev['path']
        connected = dev['connected']
        paired = dev['paired']
        rssi = dev['rssi']
        
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Icon/Status
        status_icon = "🟢" if connected else ("🔵" if paired else "⚪️")
        label_text = f"{status_icon} {name}"
        if rssi > -100:
                label_text += f" ({rssi} dBm)"
        
        label = QLabel(label_text)
        label.setFont(QFont("Arial", 12))
        layout.addWidget(label)
        layout.addStretch()
        
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
            
        layout.addWidget(btn)
        
        # Forget Button (only for paired/connected)
        if paired or connected:
                forget_btn = QPushButton("Forget")
                forget_btn.setFixedWidth(70)
                forget_btn.setStyleSheet("color: #FF5555;")
                forget_btn.clicked.connect(lambda checked, p=path: self.forget_device_path(p))
                layout.addWidget(forget_btn)
                
        return widget

    def connect_device(self, path):
         self.bluetooth_manager.connect_device(path)
         # Don't force full update immediately, let polling handle it or minimal delay
         QTimer.singleShot(500, self.update_device_list) 

    def disconnect_device(self, path):
         """Disconnects the device using the manager."""
         if self.bluetooth_manager:
            self.bluetooth_manager.disconnect_device(path)
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
        control_layout.setContentsMargins(5, 5, 5, 5)

        # Unified Status Label: Color dot + Text
        self.wifi_status_label = QLabel("⚫ Checking...")
        self.wifi_status_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.wifi_status_label.setStyleSheet("color: gray;")
        
        # Unified Toggle/Action Button
        self.wifi_action_button = QPushButton("Enable WiFi")
        self.wifi_action_button.setMinimumHeight(40)
        self.wifi_action_button.clicked.connect(self.toggle_wifi_action)

        # Refresh Icon Button
        self.refresh_button = QPushButton("↻")
        self.refresh_button.setFixedSize(40, 40)
        self.refresh_button.setFont(QFont("Arial", 18))
        self.refresh_button.clicked.connect(self.refresh_networks)

        control_layout.addWidget(self.wifi_status_label)
        control_layout.addStretch()
        control_layout.addWidget(self.wifi_action_button)
        control_layout.addWidget(self.refresh_button)

        layout.addWidget(control_group)

        # Available networks section
        networks_group = QGroupBox("Available Networks")
        networks_layout = QVBoxLayout(networks_group)

        self.networks_list = QListWidget()
        self.networks_list.setStyleSheet("font-size: 14px; padding: 5px;")
        self.networks_list.itemDoubleClicked.connect(self.connect_to_selected)
        networks_layout.addWidget(self.networks_list)

        # Action Buttons below list
        actions_layout = QHBoxLayout()
        
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setMinimumHeight(45)
        self.connect_btn.setStyleSheet("background-color: #44FF44; color: black; font-weight: bold;")
        self.connect_btn.clicked.connect(self.connect_to_selected)
        
        self.forget_btn = QPushButton("Forget Network")
        self.forget_btn.setMinimumHeight(45)
        self.forget_btn.setStyleSheet("background-color: #FF5555; color: white;")
        self.forget_btn.clicked.connect(self.forget_selected)
        
        actions_layout.addWidget(self.connect_btn)
        actions_layout.addWidget(self.forget_btn)
        
        networks_layout.addLayout(actions_layout)
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
        self.update_unified_status()
        
        # Enable/Disable interactive elements
        self.networks_list.setEnabled(enabled)
        self.refresh_button.setEnabled(enabled)
        self.connect_btn.setEnabled(enabled)
        self.forget_btn.setEnabled(enabled)

        # Update action button text/style
        if enabled:
            self.wifi_action_button.setText("Disable WiFi")
            self.wifi_action_button.setStyleSheet("background-color: #FF5555; color: white;")
        else:
            self.wifi_action_button.setText("Enable WiFi")
            self.wifi_action_button.setStyleSheet("background-color: #44FF44; color: black;")

    def on_connection_changed(self, connected, ssid):
        """Handle connection status change."""
        self.update_unified_status()

    def update_unified_status(self):
        """Update the single label that shows connection info."""
        if not self.wifi_manager:
            return
            
        enabled = self.wifi_manager.is_wifi_radio_enabled()
        current_ssid = self.wifi_manager.get_current_ssid()
        
        if not enabled:
            self.wifi_status_label.setText("⚪️ WiFi Disabled")
            self.wifi_status_label.setStyleSheet("color: gray;")
        elif current_ssid:
            self.wifi_status_label.setText(f"🟢 {current_ssid}")
            self.wifi_status_label.setStyleSheet("color: #44FF44;")
        else:
            self.wifi_status_label.setText("🔴 Disconnected")
            self.wifi_status_label.setStyleSheet("color: #FF5555;")

    def toggle_wifi_action(self):
        """Handle the unified action button (Enable/Disable)."""
        if not self.wifi_manager:
            return
            
        enabled = self.wifi_manager.is_wifi_radio_enabled()
        if enabled:
            self.wifi_status_label.setText("⚪️ Disabling...")
            self.wifi_manager.disable_wifi()
        else:
            self.wifi_status_label.setText("🟢 Enabling...")
            self.wifi_manager.enable_wifi()

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

    def refresh_networks(self):
        """Refresh the networks list."""
        if self.wifi_manager:
            self.wifi_manager.update_status()

    def disconnect_current(self):
        """Disconnect from current network."""
        if self.wifi_manager:
            self.wifi_status_label.setText("🔴 Disconnecting...")
            self.wifi_manager.disconnect_current()
            self.update_unified_status() # Force refresh

    def forget_selected(self):
        """Forget the selected network."""
        current_item = self.networks_list.currentItem()
        if not current_item or not self.wifi_manager:
            return

        network = current_item.data(Qt.ItemDataRole.UserRole)
        ssid = network['ssid']
        
        reply = QMessageBox.question(
            self, "Forget Network",
            f"Are you sure you want to forget '{ssid}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.wifi_manager.forget_network(ssid)
            self.refresh_networks()

    def connect_to_selected(self):
        """Connect to the selected network, checking for saved connections first."""
        current_item = self.networks_list.currentItem()
        if not current_item or not self.wifi_manager:
            return

        network = current_item.data(Qt.ItemDataRole.UserRole)
        ssid = network['ssid']
        secured = network['secured']

        saved_networks = self.wifi_manager.get_saved_networks()
        is_known_network = ssid in saved_networks

        password = None

        # If the network is secured but already known, we don't need a password.
        if secured and not is_known_network:
            # POPUP PASSWORD
            password, ok = self.ask_for_password(ssid)
            if not ok:
                return # User cancelled
            
            if not password:
                QMessageBox.warning(self, "Password Required", "Password cannot be empty.")
                return
        
        # UI Feedback
        self.wifi_status_label.setText(f"🟡 Connecting to {ssid}...")
        QApplication.processEvents()

        success, error_msg = self.wifi_manager.connect_to_network(ssid, password)

        if success:
            QMessageBox.information(
                self, "Connection Successful",
                f"Successfully connected to '{ssid}'"
            )
            # Clear selection or update UI handled by signals
        else:
            QMessageBox.warning(
                self, "Connection Failed",
                f"Failed to connect to '{ssid}':\n{error_msg}"
            )
            self.update_unified_status()

    def ask_for_password(self, ssid):
        """Shows a custom dialog to ask for WiFi password."""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Connect to {ssid}")
        dialog.setModal(True)
        dialog.resize(400, 200)
        
        layout = QVBoxLayout(dialog)
        
        label = QLabel(f"Enter password for network:\n{ssid}")
        label.setFont(QFont("Arial", 12))
        layout.addWidget(label)
        
        pass_input = QLineEdit()
        pass_input.setPlaceholderText("Password")
        pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        pass_input.mousePressEvent = lambda event: self.show_keyboard(pass_input)
        layout.addWidget(pass_input)
        
        show_cb = QCheckBox("Show Password")
        show_cb.toggled.connect(lambda checked: pass_input.setEchoMode(
            QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        ))
        layout.addWidget(show_cb)
        
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("Connect")
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(ok_btn)
        layout.addLayout(btn_layout)
        
        result = dialog.exec()
        return pass_input.text().strip(), result == QDialog.DialogCode.Accepted

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

