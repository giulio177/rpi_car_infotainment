# gui/setting_screen.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QComboBox, QLineEdit, QFormLayout, QGroupBox)
from PyQt6.QtCore import pyqtSlot, Qt

# REMOVE OR COMMENT OUT THIS LINE:
# from .main_window import MainWindow


class SettingsScreen(QWidget):
    AVAILABLE_RESOLUTIONS = ["800x480", "1024x600", "1280x720", "1920x1080"]

    # Note: __init__ signature was already correct, accepting main_window_ref
    def __init__(self, settings_manager, main_window_ref, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        # Store the explicitly passed main window reference
        self.main_window = main_window_ref

        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(10) # Add some spacing

        # --- Add Top Bar with Home Button ---
        top_bar_layout = QHBoxLayout()
        top_bar_layout.setContentsMargins(0, 0, 0, 0)

        self.home_button = QPushButton("🏠") # Home symbol
        self.home_button.setFixedSize(40, 40)
        self.home_button.setObjectName("homeNavButton")
        self.home_button.clicked.connect(self.go_home)

        top_bar_layout.addWidget(self.home_button)
        top_bar_layout.addStretch(1) # Push button to the left

        self.restart_button = QPushButton("🔄") # Restart symbol (Or use text "Restart")
        self.restart_button.setFixedSize(40, 40)
        self.restart_button.setObjectName("restartNavButton")
        self.restart_button.setToolTip("Restart Application") # Optional tooltip
        self.restart_button.clicked.connect(self.on_restart_clicked)

        top_bar_layout.addWidget(self.restart_button) # Add to the right

        # Add top bar to the main layout first
        self.layout.addLayout(top_bar_layout)
        # --- End Top Bar ---

        # --- Existing Settings Screen Content ---
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
        current_res_list = self.settings_manager.get("window_resolution")
        current_res_str = f"{current_res_list[0]}x{current_res_list[1]}"
        if current_res_str in self.AVAILABLE_RESOLUTIONS:
             self.resolution_combo.setCurrentText(current_res_str)
        else:
             print(f"Warning: Current resolution {current_res_str} not in predefined list.")
             self.resolution_combo.addItem(current_res_str)
             self.resolution_combo.setCurrentText(current_res_str)
        resolution_layout = QHBoxLayout()
        resolution_layout.addWidget(self.resolution_combo)
        resolution_layout.addWidget(QLabel("(Restart required)"))
        general_layout.addRow("Resolution:", resolution_layout)
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
        self.radio_type_combo.addItems(["none", "sdr", "si4703", "si4735"])
        self.radio_type_combo.setCurrentText(self.settings_manager.get("radio_type"))
        radio_layout.addRow("Radio Type:", self.radio_type_combo)
        self.radio_i2c_addr_edit = QLineEdit()
        self.radio_i2c_addr_edit.setPlaceholderText("e.g., 0x10 (for I2C type)")
        i2c_addr = self.settings_manager.get("radio_i2c_address")
        self.radio_i2c_addr_edit.setText(hex(i2c_addr) if i2c_addr is not None else "")
        radio_layout.addRow("I2C Address:", self.radio_i2c_addr_edit)
        self.layout.addWidget(radio_group)

        # --- Save Button ---
        self.save_button = QPushButton("Apply Settings")
        self.save_button.clicked.connect(self.apply_settings)
        self.layout.addWidget(self.save_button)

        self.layout.addStretch(1) # Push content towards the top (below home button)


    def apply_settings(self):
        """Apply and save all settings."""
        print("Applying settings...")
        settings_changed = False

        # --- Apply General Settings ---
        new_theme = self.theme_combo.currentText()
        if new_theme != self.settings_manager.get("theme"):
            if self.main_window is not None and hasattr(self.main_window, 'switch_theme'):
                 self.main_window.switch_theme(new_theme)
                 settings_changed = True # Theme changes immediately
            else: print("Warning: Could not apply theme - main window reference invalid.")

        selected_res_str = self.resolution_combo.currentText()
        try:
            width_str, height_str = selected_res_str.split('x')
            new_resolution = [int(width_str), int(height_str)]
            if new_resolution != self.settings_manager.get("window_resolution"):
                 self.settings_manager.set("window_resolution", new_resolution)
                 print(f"Resolution set to {new_resolution}. Restart required.")
                 settings_changed = True # Indicate restart needed
        except ValueError: print(f"Error parsing selected resolution: {selected_res_str}")
        except Exception as e: print(f"Error saving resolution setting: {e}")

        # --- Apply OBD Settings ---
        obd_port = self.obd_port_edit.text().strip() or None
        obd_baud_str = self.obd_baud_edit.text().strip(); obd_baud = None
        try:
             if obd_baud_str: obd_baud = int(obd_baud_str)
        except ValueError: print("Invalid OBD baudrate entered. Ignoring.")
        obd_changed = (self.settings_manager.get("obd_port") != obd_port or
                       self.settings_manager.get("obd_baudrate") != obd_baud)
        if obd_changed:
            self.settings_manager.set("obd_port", obd_port)
            self.settings_manager.set("obd_baudrate", obd_baud)
            if self.main_window is not None and hasattr(self.main_window, 'update_obd_config'):
                 self.main_window.update_obd_config()
                 settings_changed = True
            else: print("Warning: Could not update OBD config - main window reference invalid.")

        # --- Apply Radio Settings ---
        radio_type = self.radio_type_combo.currentText()
        i2c_addr_str = self.radio_i2c_addr_edit.text().strip(); i2c_addr = None
        try:
            if i2c_addr_str: i2c_addr = int(i2c_addr_str, 0)
        except ValueError: print("Invalid I2C address entered. Ignoring.")
        radio_changed = (self.settings_manager.get("radio_type") != radio_type or
                         self.settings_manager.get("radio_i2c_address") != i2c_addr)
        if radio_changed:
            self.settings_manager.set("radio_type", radio_type)
            self.settings_manager.set("radio_i2c_address", i2c_addr)
            if self.main_window is not None and hasattr(self.main_window, 'update_radio_config'):
                 self.main_window.update_radio_config()
                 settings_changed = True
            else: print("Warning: Could not update Radio config - main window reference invalid.")

        if settings_changed:
            print("Settings applied. Restart may be required for some changes.")
        else:
            print("Settings applied (No changes detected that require action now).")

    def on_restart_clicked(self):
        """Triggers the application restart via MainWindow."""
        print(f"Restart requested from {self.__class__.__name__}")
        # Use self.main_window which should hold the MainWindow instance
        if self.main_window is not None and hasattr(self.main_window, 'restart_application'):
            self.main_window.restart_application()
        else:
            print("Error: Cannot trigger restart. Main window reference is invalid or missing 'restart_application' method.")
  
    def go_home(self):
        """Navigate back to the HomeScreen."""
        # Check if self.main_window exists AND has the 'navigate_to' and 'home_screen' methods/attributes
        if self.main_window is not None and hasattr(self.main_window, 'navigate_to') and hasattr(self.main_window, 'home_screen'):
            self.main_window.navigate_to(self.main_window.home_screen)
        else:
            print("Error: Cannot navigate home. Main window reference is invalid or missing required attributes.")
            if self.main_window is None:
                print("Reason: self.main_window is None.")
            elif not hasattr(self.main_window, 'navigate_to'):
                print(f"Reason: Main window object {type(self.main_window)} does not have 'navigate_to' method.")
            elif not hasattr(self.main_window, 'home_screen'):
                 print(f"Reason: Main window object {type(self.main_window)} does not have 'home_screen' attribute.")
