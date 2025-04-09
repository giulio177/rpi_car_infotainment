# gui/obd_screen.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QGridLayout,
                             QPushButton, QHBoxLayout, QSpacerItem, QSizePolicy)
from PyQt6.QtCore import QTimer, QDateTime, pyqtSlot, Qt

# --- Import scale_value helper ---
from .styling import scale_value

class OBDScreen(QWidget):
    # --- ADDED: Screen Title ---
    screen_title = "OBD"
    
    def __init__(self, parent=None): # parent is likely MainWindow
        super().__init__(parent)
        self.main_window = parent

        # --- Store base sizes ---
        self.base_margin = 10
        self.base_top_section_spacing = 15
        self.base_grid_spacing = 8
        self.base_media_spacing = 10
        self.base_media_playback_button_spacing = 5

        # --- Main Layout (Vertical) ---
        self.main_layout = QVBoxLayout(self)
        # Margins/Spacing set by update_scaling

        self.status_label = QLabel("Status: Initializing...")
        self.status_label.setObjectName("obdStatusLabel") # ID for styling
        self.main_layout.addWidget(self.status_label)

        # Grid layout for data
        self.grid_layout = QGridLayout() # Store reference
        # Spacing set by update_scaling
        self.main_layout.addLayout(self.grid_layout)

        # --- Labels for specific data points ---
        self.speed_label = QLabel("Speed:")
        self.speed_value = QLabel("---")
        self.speed_value.setObjectName("speed_value") # Use ID for styling

        self.rpm_label = QLabel("RPM:")
        self.rpm_value = QLabel("---")
        self.rpm_value.setObjectName("rpm_value")

        self.coolant_label = QLabel("Coolant Temp:")
        self.coolant_value = QLabel("---")
        self.coolant_value.setObjectName("coolant_value")

        self.fuel_label = QLabel("Fuel Level:")
        self.fuel_value = QLabel("---")
        self.fuel_value.setObjectName("fuel_value")

        # Remove direct styling - Handled by QSS via objectName
        # value_style = "font-size: 22pt; font-weight: bold; color: #007bff;" # REMOVE
        # self.speed_value.setStyleSheet(value_style) # REMOVE
        # ... REMOVE for others ...

        # Add widgets to grid (Row, Column, RowSpan, ColSpan)
        self.grid_layout.addWidget(self.speed_label, 0, 0)
        self.grid_layout.addWidget(self.speed_value, 0, 1)
        self.grid_layout.addWidget(self.rpm_label, 1, 0)
        self.grid_layout.addWidget(self.rpm_value, 1, 1)
        self.grid_layout.addWidget(self.coolant_label, 0, 2)
        self.grid_layout.addWidget(self.coolant_value, 0, 3)
        self.grid_layout.addWidget(self.fuel_label, 1, 2)
        self.grid_layout.addWidget(self.fuel_value, 1, 3)

        # Add more data points similarly...

        self.main_layout.addStretch(1) # Push content towards the top


    def update_scaling(self, scale_factor, scaled_main_margin):
        """Applies scaling to internal layouts."""
        scaled_top_section_spacing = scale_value(self.base_top_section_spacing, scale_factor)
        scaled_grid_spacing = scale_value(self.base_grid_spacing, scale_factor)
        scaled_media_spacing = scale_value(self.base_media_spacing, scale_factor)
        scaled_playback_spacing = scale_value(self.base_media_playback_button_spacing, scale_factor)

        # Apply to layouts
        self.main_layout.setContentsMargins(scaled_main_margin, scaled_main_margin, scaled_main_margin, scaled_main_margin)
        self.main_layout.setSpacing(scaled_main_margin) # Main spacing between top section / (nothing else now)

        self.top_section_layout.setSpacing(scaled_top_section_spacing)
        self.grid_layout.setSpacing(scaled_grid_spacing)
        self.media_layout.setSpacing(scaled_media_spacing)
        self.playback_layout.setSpacing(scaled_playback_spacing)

    @pyqtSlot(dict)
    def update_data(self, data_dict):
        """Slot to receive data updates from OBDManager."""
        speed = data_dict.get('SPEED')
        self.speed_value.setText(f"{speed} km/h" if speed is not None else "---")
        rpm = data_dict.get('RPM')
        self.rpm_value.setText(f"{int(rpm)}" if rpm is not None else "---")
        coolant_temp = data_dict.get('COOLANT_TEMP')
        self.coolant_value.setText(f"{coolant_temp} °C" if coolant_temp is not None else "---")
        fuel_level = data_dict.get('FUEL_LEVEL')
        self.fuel_value.setText(f"{fuel_level} %" if fuel_level is not None else "---")
        # Update other labels...

    @pyqtSlot(str)
    def update_connection_status(self, status_text):
        self.status_label.setText(f"Status: {status_text.replace('OBD: ', '')}")
