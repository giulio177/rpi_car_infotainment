# gui/setting_screen.py
# NOTE: Consider renaming file to settings_screen.py for consistency

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QComboBox, QLineEdit, QFormLayout, QGroupBox, QSpacerItem, QSizePolicy)
from PyQt6.QtCore import QTimer, QDateTime, pyqtSlot, Qt

# --- Import scale_value helper ---
from .styling import scale_value

class SettingsScreen(QWidget):
    AVAILABLE_RESOLUTIONS = ["800x480", "1024x600", "1280x720", "1920x1080"] # Keep static

    def __init__(self, settings_manager, main_window_ref, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.main_window = main_window_ref # Reference to MainWindow

        # --- Base sizes ---
        self.base_margin = 10
        self.base_spacing = 15 # General vertical spacing
        self.base_group_spacing = 10 # Spacing within group boxes (form layout)
        self.base_form_h_spacing = 8 # Horizontal spacing in form layout
        self.base_form_v_spacing = 8 # Vertical spacing in form layout

        # --- Main Layout ---
        self.main_layout = QVBoxLayout(self)
        # Margins/Spacing set by update_scaling

        # --- Header Layout ---
        self.header_layout = QHBoxLayout() # Store reference
        # Spacing set by update_scaling
        self.header_title_label = QLabel("Settings")
        self.header_title_label.setObjectName("headerTitle")
        self.header_layout.addWidget(self.header_title_label)
        spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.header_layout.addItem(spacer)
        self.clock_label = QLabel("00:00")
        self.clock_label.setObjectName("headerClock")
        self.header_layout.addWidget(self.clock_label)
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(10000)
        self._update_clock()
        self.main_layout.addLayout(self.header_layout)
        # --- END Header ---

        # Removed the extra "Settings" title label, header is sufficient
        # self.title_label = QLabel("Settings")
        # self.title_label.setStyleSheet(...) # REMOVE
        # self.main_layout.addWidget(self.title_label) # REMOVE

        # --- General Settings ---
        self.general_group = QGroupBox("General") # Store reference to group
        self.general_group.setObjectName("settingsGeneralGroup")
        self.general_layout = QFormLayout() # Store reference to layout
        # Spacing set by update_scaling
        self.general_group.setLayout(self.general_layout)

        self.theme_combo = QComboBox()
        self.theme_combo.setObjectName("themeCombo")
        self.theme_combo.addItems(["light", "dark"])
        self.theme_combo.setCurrentText(self.settings_manager.get("theme"))
        self.general_layout.addRow("UI Theme:", self.theme_combo)

        self.resolution_combo = QComboBox()
        self.resolution_combo.setObjectName("resolutionCombo")
        self.resolution_combo.addItems(self.AVAILABLE_RESOLUTIONS)
        current_res_list = self.settings_manager.get("window_resolution")
        current_res_str = f"{current_res_list[0]}x{current_res_list[1]}"
        if current_res_str in self.AVAILABLE_RESOLUTIONS:
             self.resolution_combo.setCurrentText(current_res_str)
        else:
             print(f"Warning: Current resolution {current_res_str} not in predefined list.")
             # Optionally add it dynamically, or force selection from list
             # self.resolution_combo.addItem(current_res_str) # If adding dynamically
             self.resolution_combo.setCurrentIndex(0) # Default to first in list if not found
             # self.resolution_combo.setCurrentText(current_res_str)
        self.resolution_note_label = QLabel("(Restart required)")
        self.resolution_note_label.setObjectName("resolutionNoteLabel") # For styling (e.g., smaller font)
        resolution_layout = QHBoxLayout() # Layout for combo + label
        resolution_layout.addWidget(self.resolution_combo, 1) # Allow combo to stretch
        resolution_layout.addWidget(self.resolution_note_label)
        self.general_layout.addRow("Resolution:", resolution_layout)

        self.main_layout.addWidget(self.general_group)

        # --- OBD Settings ---
        self.obd_group = QGroupBox("OBD-II")
        self.obd_group.setObjectName("settingsObdGroup")
        self.obd_layout = QFormLayout() # Store reference
        # Spacing set by update_scaling
        self.obd_group.setLayout(self.obd_layout)

        self.obd_port_edit = QLineEdit()
        self.obd_port_edit.setObjectName("obdPortEdit")
        self.obd_port_edit.setPlaceholderText("e.g., /dev/rfcomm0 or /dev/ttyUSB0 (leave blank for auto)")
        self.obd_port_edit.setText(self.settings_manager.get("obd_port") or "")
        self.obd_layout.addRow("OBD Port:", self.obd_port_edit)

        self.obd_baud_edit = QLineEdit()
        self.obd_baud_edit.setObjectName("obdBaudEdit")
        self.obd_baud_edit.setPlaceholderText("e.g., 38400 (leave blank for auto)")
        obd_baud = self.settings_manager.get("obd_baudrate")
        self.obd_baud_edit.setText(str(obd_baud) if obd_baud else "")
        self.obd_layout.addRow("Baudrate:", self.obd_baud_edit)

        self.main_layout.addWidget(self.obd_group)

        # --- Radio Settings ---
        self.radio_group = QGroupBox("Radio")
        self.radio_group.setObjectName("settingsRadioGroup")
        self.radio_layout = QFormLayout() # Store reference
        # Spacing set by update_scaling
        self.radio_group.setLayout(self.radio_layout)

        self.radio_type_combo = QComboBox()
        self.radio_type_combo.setObjectName("radioTypeCombo")
        self.radio_type_combo.addItems(["none", "sdr", "si4703", "si4735"]) # Add more types if needed
        self.radio_type_combo.setCurrentText(self.settings_manager.get("radio_type"))
        self.radio_layout.addRow("Radio Type:", self.radio_type_combo)

        self.radio_i2c_addr_edit = QLineEdit()
        self.radio_i2c_addr_edit.setObjectName("radioI2cAddrEdit")
        self.radio_i2c_addr_edit.setPlaceholderText("e.g., 0x10 (for I2C type)")
        i2c_addr = self.settings_manager.get("radio_i2c_address")
        self.radio_i2c_addr_edit.setText(hex(i2c_addr) if i2c_addr is not None else "")
        self.radio_layout.addRow("I2C Address:", self.radio_i2c_addr_edit)

        self.main_layout.addWidget(self.radio_group)

        # --- Save Button ---
        self.save_button = QPushButton("Apply Settings")
        self.save_button.setObjectName("settingsSaveButton")
        self.save_button.clicked.connect(self.apply_settings)
        self.main_layout.addWidget(self.save_button, 0, Qt.AlignmentFlag.AlignCenter) # Center button

        self.main_layout.addStretch(1) # Push content towards the top


    def update_scaling(self, scale_factor, scaled_main_margin):
        """Applies scaling to internal layouts."""
        scaled_spacing = scale_value(self.base_spacing, scale_factor)
        scaled_form_h_spacing = scale_value(self.base_form_h_spacing, scale_factor)
        scaled_form_v_spacing = scale_value(self.base_form_v_spacing, scale_factor)
        # Group box margins are tricky, often better handled by QSS margin-top and padding
        # scaled_group_spacing = scale_value(self.base_group_spacing, scale_factor)

        # Apply to layouts
        self.main_layout.setContentsMargins(scaled_main_margin, scaled_main_margin, scaled_main_margin, scaled_main_margin)
        self.main_layout.setSpacing(scaled_spacing)
        self.header_layout.setSpacing(scaled_spacing) # Use general spacing or define base_header_spacing

        # Apply spacing to form layouts within group boxes
        self.general_layout.setHorizontalSpacing(scaled_form_h_spacing)
        self.general_layout.setVerticalSpacing(scaled_form_v_spacing)
        # self.general_layout.setContentsMargins(...) # Usually not needed for FormLayout

        self.obd_layout.setHorizontalSpacing(scaled_form_h_spacing)
        self.obd_layout.setVerticalSpacing(scaled_form_v_spacing)

        self.radio_layout.setHorizontalSpacing(scaled_form_h_spacing)
        self.radio_layout.setVerticalSpacing(scaled_form_v_spacing)


    def apply_settings(self):
        """Apply and save all settings."""
        print("Applying settings...")
        settings_changed = False
        restart_required = False

        # --- Apply General Settings ---
        new_theme = self.theme_combo.currentText()
        if new_theme != self.settings_manager.get("theme"):
            if self.main_window is not None and hasattr(self.main_window, 'switch_theme'):
                 self.main_window.switch_theme(new_theme)
                 settings_changed = True
            else: print("Warning: Could not apply theme - main window reference invalid.")

        selected_res_str = self.resolution_combo.currentText()
        try:
            width_str, height_str = selected_res_str.split('x')
            new_resolution = [int(width_str), int(height_str)]
            if new_resolution != self.settings_manager.get("window_resolution"):
                 self.settings_manager.set("window_resolution", new_resolution)
                 print(f"Resolution set to {new_resolution}. Restart required.")
                 settings_changed = True
                 restart_required = True # Flag restart
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
            if i2c_addr_str: i2c_addr = int(i2c_addr_str, 0) # Handle hex (0x...) or decimal
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
            status_message = "Settings applied."
            if restart_required:
                status_message += " Please restart the application for all changes to take effect."
            # TODO: Show a status message to the user (e.g., using a temporary label or dialog)
            print(status_message)
            # Could briefly change save button text:
            # self.save_button.setText("Applied!")
            # QTimer.singleShot(2000, lambda: self.save_button.setText("Apply Settings"))
        else:
            print("Settings applied (No changes detected).")
            # self.save_button.setText("No Changes")
            # QTimer.singleShot(1500, lambda: self.save_button.setText("Apply Settings"))


    def _update_clock(self):
        """Updates the clock label with the current time."""
        current_time = QDateTime.currentDateTime()
        time_str = current_time.toString("HH:mm")
        self.clock_label.setText(time_str)
