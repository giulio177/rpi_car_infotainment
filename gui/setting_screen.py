# setting_screen.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QComboBox, QLineEdit, QFormLayout, QGroupBox)
from PyQt6.QtCore import pyqtSlot

class SettingsScreen(QWidget):
    # Predefined common resolutions (Add/modify as needed)
    AVAILABLE_RESOLUTIONS = [
        "800x480",
        "1024x600",
        "1280x720",
        "1920x1080", # Example Full HD
    ]

    def __init__(self, settings_manager, main_window, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.main_window = main_window

        self.layout = QVBoxLayout(self)

        self.title_label = QLabel("Settings")
        self.title_label.setStyleSheet("font-size: 24pt; font-weight: bold; margin-bottom: 15px;")
        self.layout.addWidget(self.title_label)

        # --- General Settings ---
        general_group = QGroupBox("General")
        general_layout = QFormLayout()
        general_group.setLayout(general_layout)

        # Theme
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["light", "dark"])
        self.theme_combo.setCurrentText(self.settings_manager.get("theme"))
        general_layout.addRow("UI Theme:", self.theme_combo)

        # Resolution
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(self.AVAILABLE_RESOLUTIONS)
        # Get current setting and format it as "WxH" to select in combo box
        current_res_list = self.settings_manager.get("window_resolution")
        current_res_str = f"{current_res_list[0]}x{current_res_list[1]}"
        if current_res_str in self.AVAILABLE_RESOLUTIONS:
             self.resolution_combo.setCurrentText(current_res_str)
        else:
             print(f"Warning: Current resolution {current_res_str} not in available list.")
             # Optionally add it dynamically or default to first item
             # self.resolution_combo.addItem(current_res_str) # Add if needed
             # self.resolution_combo.setCurrentText(current_res_str)

        resolution_layout = QHBoxLayout()
        resolution_layout.addWidget(self.resolution_combo)
        resolution_layout.addWidget(QLabel("(Restart required)"))
        general_layout.addRow("Resolution:", resolution_layout)


        self.layout.addWidget(general_group)

        # --- OBD Settings ---
        # ... (keep existing OBD settings group) ...
        obd_group = QGroupBox("OBD-II")
        obd_layout = QFormLayout()
        obd_group.setLayout(obd_layout)
        self.obd_port_edit = QLineEdit()
        self.obd_port_edit.setPlaceholderText("e.g., /dev/rfcomm0 or /dev/ttyUSB0 (leave blank for auto)")
        self.obd_port_edit.setText(self.settings_manager.get("obd_port") or "")
        obd_layout.addRow("OBD Port:", self.obd_port_edit)
        self.obd_baud_edit = QLineEdit()
        self.obd_baud_edit.setPlaceholderText("e.g., 38400 (leave blank for auto)")
        obd_baud = self.settings_manager.get("obd_baudrate")
        self.obd_baud_edit.setText(str(obd_baud) if obd_baud else "")
        obd_layout.addRow("Baudrate:", self.obd_baud_edit)
        self.layout.addWidget(obd_group)


        # --- Radio Settings ---
        # ... (keep existing Radio settings group) ...
        radio_group = QGroupBox("Radio")
        radio_layout = QFormLayout()
        radio_group.setLayout(radio_layout)
        self.radio_type_combo = QComboBox()
        self.radio_type_combo.addItems(["none", "sdr", "si4703", "si4735"]) # Add relevant types
        self.radio_type_combo.setCurrentText(self.settings_manager.get("radio_type"))
        radio_layout.addRow("Radio Type:", self.radio_type_combo)
        self.radio_i2c_addr_edit = QLineEdit()
        self.radio_i2c_addr_edit.setPlaceholderText("e.g., 0x10 (for I2C type)")
        i2c_addr = self.settings_manager.get("radio_i2c_address")
        self.radio_i2c_addr_edit.setText(hex(i2c_addr) if i2c_addr else "")
        radio_layout.addRow("I2C Address:", self.radio_i2c_addr_edit)
        self.layout.addWidget(radio_group)


        # --- Save Button ---
        self.save_button = QPushButton("Apply Settings")
        self.save_button.clicked.connect(self.apply_settings)
        self.layout.addWidget(self.save_button)

        self.layout.addStretch(1)


    def apply_settings(self):
        print("Applying settings...")

        # --- Apply General Settings ---
        new_theme = self.theme_combo.currentText()
        self.main_window.switch_theme(new_theme) # Calls settings_manager.set internally

        # Apply Resolution Setting
        selected_res_str = self.resolution_combo.currentText()
        try:
            width_str, height_str = selected_res_str.split('x')
            new_resolution = [int(width_str), int(height_str)]
            self.settings_manager.set("window_resolution", new_resolution)
            print(f"Resolution set to {new_resolution}. Restart required.")
        except ValueError:
            print(f"Error parsing selected resolution: {selected_res_str}")
        except Exception as e:
             print(f"Error saving resolution setting: {e}")


        # --- Apply OBD Settings ---
        # ... (keep existing OBD apply logic) ...
        obd_port = self.obd_port_edit.text().strip()
        obd_baud_str = self.obd_baud_edit.text().strip()
        obd_baud = None
        try:
             if obd_baud_str: obd_baud = int(obd_baud_str)
        except ValueError:
             print("Invalid OBD baudrate entered. Ignoring.")
        obd_changed = (self.settings_manager.get("obd_port") != (obd_port or None) or
                       self.settings_manager.get("obd_baudrate") != obd_baud)
        self.settings_manager.set("obd_port", obd_port if obd_port else None)
        self.settings_manager.set("obd_baudrate", obd_baud)
        if obd_changed:
            self.main_window.update_obd_config()


        # --- Apply Radio Settings ---
        # ... (keep existing Radio apply logic) ...
        radio_type = self.radio_type_combo.currentText()
        i2c_addr_str = self.radio_i2c_addr_edit.text().strip()
        i2c_addr = None
        try:
            if i2c_addr_str: i2c_addr = int(i2c_addr_str, 0) # Auto-detect base (0x for hex)
        except ValueError:
            print("Invalid I2C address entered. Ignoring.")
        radio_changed = (self.settings_manager.get("radio_type") != radio_type or
                         self.settings_manager.get("radio_i2c_address") != i2c_addr)
        self.settings_manager.set("radio_type", radio_type)
        self.settings_manager.set("radio_i2c_address", i2c_addr)
        if radio_changed:
             self.main_window.update_radio_config()


        print("Settings applied. Restart may be required for some changes.")
        # Optionally show a confirmation message pop-up
