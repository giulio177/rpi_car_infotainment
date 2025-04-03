# gui/setting_screen.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QComboBox, QLineEdit, QFormLayout,
                             QGroupBox, QSpacerItem, QSizePolicy,
                             QScrollArea) # <-- ADD QScrollArea
from PyQt6.QtCore import QTimer, QDateTime, pyqtSlot, Qt

from .styling import scale_value

class SettingsScreen(QWidget):
    AVAILABLE_RESOLUTIONS = ["800x480", "1024x600", "1280x720", "1920x1080"] # Keep static

    def __init__(self, settings_manager, main_window_ref, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.main_window = main_window_ref # Reference to MainWindow

        # --- Base sizes ---
        self.base_margin = 10
        self.base_spacing = 15
        self.base_scroll_content_spacing = 10
        self.base_form_h_spacing = 8
        self.base_form_v_spacing = 8
        self.base_button_layout_spacing = 10 # Spacing between the two buttons

        # --- Main Layout (Vertical: Header, Button, ScrollArea) ---
        self.main_layout = QVBoxLayout(self)
        # Margins/Spacing set by update_scaling

        # --- Header Layout (Stays at the top) ---
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
        self.main_layout.addLayout(self.header_layout) # Add header first

        # --- MODIFIED: Button Layout ---
        # Create a horizontal layout to hold the buttons
        self.button_layout = QHBoxLayout()
        # Spacing set by update_scaling

        # Apply Settings Button (Existing)
        self.save_button = QPushButton("Apply Settings")
        self.save_button.setObjectName("settingsSaveButton")
        self.save_button.clicked.connect(self.apply_settings)

        # ADDED: Apply and Restart Button
        self.restart_button = QPushButton("Apply and Restart")
        self.restart_button.setObjectName("settingsRestartButton") # ID for styling
        self.restart_button.clicked.connect(self.apply_and_restart) # Connect to new method

        # Add buttons to the horizontal layout, centered
        self.button_layout.addStretch(1) # Push buttons to center
        self.button_layout.addWidget(self.save_button)
        self.button_layout.addWidget(self.restart_button)
        self.button_layout.addStretch(1) # Push buttons to center

        # Add the button layout to the main vertical layout
        self.main_layout.addLayout(self.button_layout)
        # --- End Button Layout ---


      
        # --- SCROLL AREA SETUP ---
        self.scroll_area = QScrollArea() # Create Scroll Area
        self.scroll_area.setObjectName("settingsScrollArea") # ID for styling
        self.scroll_area.setWidgetResizable(True) # CRUCIAL for vertical scrolling
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff) # Hide horizontal bar
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded) # Show vertical only when needed

        # Container widget THAT WILL HOLD the settings groups
        self.scroll_content_widget = QWidget()
        self.scroll_content_widget.setObjectName("settingsScrollContent") # ID for styling

        # Layout FOR THE CONTAINER WIDGET (inside the scroll area)
        self.scroll_layout = QVBoxLayout(self.scroll_content_widget)
        # Spacing set by update_scaling

        # --- Settings Groups (Now added to scroll_layout) ---

        # --- General Settings ---
        self.general_group = QGroupBox("General")
        self.general_group.setObjectName("settingsGeneralGroup")
        self.general_layout = QFormLayout() # Store ref
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
             self.resolution_combo.setCurrentIndex(0) # Default to first

        self.resolution_note_label = QLabel("(Restart required)")
        self.resolution_note_label.setObjectName("resolutionNoteLabel") # Style via QSS
        resolution_layout = QHBoxLayout()
        resolution_layout.addWidget(self.resolution_combo, 1) # Combo expands
        resolution_layout.addWidget(self.resolution_note_label) # Label takes preferred size
        resolution_layout.setSpacing(scale_value(5, 1.0)) # Initial small spacing for this layout
        self.general_layout.addRow("Resolution:", resolution_layout)

        # ADD Group Box to the SCROLL LAYOUT
        self.scroll_layout.addWidget(self.general_group)

        # --- OBD Settings ---
        self.obd_group = QGroupBox("OBD-II")
        self.obd_group.setObjectName("settingsObdGroup")
        self.obd_layout = QFormLayout() # Store ref
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

        # ADD Group Box to the SCROLL LAYOUT
        self.scroll_layout.addWidget(self.obd_group)

        # --- Radio Settings ---
        self.radio_group = QGroupBox("Radio")
        self.radio_group.setObjectName("settingsRadioGroup")
        self.radio_layout = QFormLayout() # Store ref
         # Spacing set by update_scaling
        self.radio_group.setLayout(self.radio_layout)

        self.radio_type_combo = QComboBox()
        self.radio_type_combo.setObjectName("radioTypeCombo")
        self.radio_type_combo.addItems(["none", "sdr", "si4703", "si4735"])
        self.radio_type_combo.setCurrentText(self.settings_manager.get("radio_type"))
        self.radio_layout.addRow("Radio Type:", self.radio_type_combo)

        self.radio_i2c_addr_edit = QLineEdit()
        self.radio_i2c_addr_edit.setObjectName("radioI2cAddrEdit")
        self.radio_i2c_addr_edit.setPlaceholderText("e.g., 0x10 (for I2C type)")
        i2c_addr = self.settings_manager.get("radio_i2c_address")
        self.radio_i2c_addr_edit.setText(hex(i2c_addr) if i2c_addr is not None else "")
        self.radio_layout.addRow("I2C Address:", self.radio_i2c_addr_edit)

        # ADD Group Box to the SCROLL LAYOUT
        self.scroll_layout.addWidget(self.radio_group)

        # Add a stretch at the END of the scroll layout to push groups up
        self.scroll_layout.addStretch(1)

        # Set the container widget as the widget for the scroll area
        self.scroll_area.setWidget(self.scroll_content_widget)

        # Add the Scroll Area to the MAIN layout
        # Give it stretch factor 1 so it expands vertically to fill space
        self.main_layout.addWidget(self.scroll_area, 1)


    def update_scaling(self, scale_factor, scaled_main_margin):
        """Applies scaling to internal layouts."""
        scaled_spacing = scale_value(self.base_spacing, scale_factor)
        scaled_scroll_content_spacing = scale_value(self.base_scroll_content_spacing, scale_factor)
        scaled_form_h_spacing = scale_value(self.base_form_h_spacing, scale_factor)
        scaled_form_v_spacing = scale_value(self.base_form_v_spacing, scale_factor)
        scaled_button_layout_spacing = scale_value(self.base_button_layout_spacing, scale_factor)

        # Apply to MAIN layouts
        self.main_layout.setContentsMargins(scaled_main_margin, scaled_main_margin, scaled_main_margin, scaled_main_margin)
        self.main_layout.setSpacing(scaled_spacing)
        self.header_layout.setSpacing(scaled_spacing)

        # --- Scale button layout spacing ---
        self.button_layout.setSpacing(scaled_button_layout_spacing)

        # Apply to the layout INSIDE the scroll area
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(scaled_scroll_content_spacing)

        # Apply spacing to form layouts within group boxes
        self.general_layout.setHorizontalSpacing(scaled_form_h_spacing)
        self.general_layout.setVerticalSpacing(scaled_form_v_spacing)
        self.obd_layout.setHorizontalSpacing(scaled_form_h_spacing)
        self.obd_layout.setVerticalSpacing(scaled_form_v_spacing)
        self.radio_layout.setHorizontalSpacing(scaled_form_h_spacing)
        self.radio_layout.setVerticalSpacing(scaled_form_v_spacing)

        # Also scale the spacing in the specific resolution layout
        resolution_layout = self.general_layout.itemAt(1, QFormLayout.ItemRole.FieldRole).layout()
        if resolution_layout:
            resolution_layout.setSpacing(scale_value(5, scale_factor))


    def apply_settings(self, show_feedback=True): # Added optional feedback flag
        """Apply and save all settings. Returns True if a restart-requiring change was made."""
        print("Applying settings...")
        settings_changed = False
        restart_required = False

        # --- Apply General Settings ---
        new_theme = self.theme_combo.currentText()
        if new_theme != self.settings_manager.get("theme"):
            if self.main_window is not None and hasattr(self.main_window, 'switch_theme'):
                 self.main_window.switch_theme(new_theme)
                 settings_changed = True
            # Theme change doesn't require app restart itself

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

        # --- Optional Feedback ---
        if show_feedback:
            if settings_changed:
                status_message = "Settings applied."
                if restart_required:
                    status_message += " Restart required."
                print(status_message)
                # Give feedback on button
                original_text = self.save_button.text()
                self.save_button.setText("Applied!")
                self.save_button.setEnabled(False); self.restart_button.setEnabled(False) # Disable both
                QTimer.singleShot(2000, lambda: (
                    self.save_button.setText(original_text),
                    self.save_button.setEnabled(True),
                    self.restart_button.setEnabled(True) # Re-enable both
                ))
            else:
                print("Settings applied (No changes detected).")
                original_text = self.save_button.text()
                self.save_button.setText("No Changes")
                self.save_button.setEnabled(False); self.restart_button.setEnabled(False)
                QTimer.singleShot(1500, lambda: (
                    self.save_button.setText(original_text),
                    self.save_button.setEnabled(True),
                    self.restart_button.setEnabled(True)
                ))

        return restart_required # Return the flag

    # --- ADDED: Method for the new button ---
    def apply_and_restart(self):
        """Applies settings and then initiates the application restart sequence."""
        print("Apply and Restart requested.")
        # Apply settings first (suppress the normal feedback message)
        self.apply_settings(show_feedback=False)

        # Now trigger the restart process in MainWindow
        if self.main_window and hasattr(self.main_window, 'restart_application'):
            # The restart_application method already includes a confirmation dialog
            self.main_window.restart_application()
        else:
            print("ERROR: Cannot restart. MainWindow reference is invalid or missing 'restart_application' method.")
            # Optionally show an error message box here

    def _update_clock(self):
        """Updates the clock label with the current time."""
        current_time = QDateTime.currentDateTime()
        time_str = current_time.toString("HH:mm")
        self.clock_label.setText(time_str)
