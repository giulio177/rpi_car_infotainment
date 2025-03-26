from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QComboBox, QLineEdit, QFormLayout, QGroupBox)
from PyQt6.QtCore import pyqtSlot

class SettingsScreen(QWidget):
    def __init__(self, settings_manager, main_window, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.main_window = main_window # To call theme switch, config updates

        self.layout = QVBoxLayout(self)

        self.title_label = QLabel("Settings")
        self.title_label.setStyleSheet("font-size: 24pt; font-weight: bold; margin-bottom: 15px;")
        self.layout.addWidget(self.title_label)

        # --- General Settings ---
        general_group = QGroupBox("General")
        general_layout = QFormLayout()
        general_group.setLayout(general_layout)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["light", "dark"])
        self.theme_combo.setCurrentText(self.settings_manager.get("theme"))
        general_layout.addRow("UI Theme:", self.theme_combo)

        self.layout.addWidget(general_group)

        # --- OBD Settings ---
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

        # --- Apply OBD Settings ---
        obd_port = self.obd_port_edit.text().strip()
        obd_baud_str = self.obd_baud_edit.text().strip()
        obd_baud = None
        try:
             if obd_baud_str: obd_baud = int(obd_baud_str)
        except ValueError:
             print("Invalid OBD baudrate entered. Ignoring.")

        # Check if OBD settings actually changed before restarting manager
        obd_changed = (self.settings_manager.get("obd_port") != (obd_port or None) or
                       self.settings_manager.get("obd_baudrate") != obd_baud)

        self.settings_manager.set("obd_port", obd_port if obd_port else None)
        self.settings_manager.set("obd_baudrate", obd_baud)

        if obd_changed:
            self.main_window.update_obd_config()


        # --- Apply Radio Settings ---
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

        print("Settings applied.")
        # Optionally show a confirmation message