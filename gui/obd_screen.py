# gui/obd_screen.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QGridLayout,
                             QPushButton, QHBoxLayout) # Added QPushButton, QHBoxLayout
from PyQt6.QtCore import pyqtSlot, Qt

# Try importing MainWindow for type hinting
try:
    from .main_window import MainWindow
except ImportError:
    MainWindow = None

class OBDScreen(QWidget):
    def __init__(self, parent=None): # parent is likely MainWindow
        super().__init__(parent)
        self.main_window = parent # Store reference

        self.layout = QVBoxLayout(self)
        # Remove AlignTop if you want the home button strictly at the top edge
        # self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.layout.setSpacing(10) # Add some spacing

        # --- Add Top Bar with Home Button ---
        top_bar_layout = QHBoxLayout()
        top_bar_layout.setContentsMargins(0, 0, 0, 0) # No extra margins for this bar

        self.home_button = QPushButton("🏠") # Home symbol
        self.home_button.setFixedSize(40, 40) # Make it small
        self.home_button.setObjectName("homeNavButton") # For styling
        self.home_button.clicked.connect(self.go_home)

        top_bar_layout.addWidget(self.home_button)
        top_bar_layout.addStretch(1) # Push button to the left

        # Add top bar to the main layout *first*
        self.layout.addLayout(top_bar_layout)
        # --- End Top Bar ---

        # --- Existing OBD Screen Content ---
        self.title_label = QLabel("OBD-II Data")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-size: 24pt; font-weight: bold; margin-bottom: 15px;")
        self.layout.addWidget(self.title_label)

        self.status_label = QLabel("Status: Initializing...")
        self.layout.addWidget(self.status_label)

        # Grid layout for data
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(10)
        self.layout.addLayout(self.grid_layout)

        # --- Labels for specific data points ---
        self.speed_label = QLabel("Speed:")
        self.speed_value = QLabel("---")
        # ... (rest of the labels: rpm, coolant, fuel) ...
        self.rpm_label = QLabel("RPM:")
        self.rpm_value = QLabel("---")
        self.coolant_label = QLabel("Coolant Temp:")
        self.coolant_value = QLabel("---")
        self.fuel_label = QLabel("Fuel Level:")
        self.fuel_value = QLabel("---")


        # Style value labels
        value_style = "font-size: 22pt; font-weight: bold; color: #007bff;"
        self.speed_value.setStyleSheet(value_style)
        # ... (style other value labels) ...
        self.rpm_value.setStyleSheet(value_style)
        self.coolant_value.setStyleSheet(value_style)
        self.fuel_value.setStyleSheet(value_style)


        # Add widgets to grid
        self.grid_layout.addWidget(self.speed_label, 0, 0)
        self.grid_layout.addWidget(self.speed_value, 0, 1)
        # ... (add other labels/values to grid) ...
        self.grid_layout.addWidget(self.rpm_label, 1, 0)
        self.grid_layout.addWidget(self.rpm_value, 1, 1)
        self.grid_layout.addWidget(self.coolant_label, 0, 2)
        self.grid_layout.addWidget(self.coolant_value, 0, 3)
        self.grid_layout.addWidget(self.fuel_label, 1, 2)
        self.grid_layout.addWidget(self.fuel_value, 1, 3)


        self.layout.addStretch(1) # Push content towards the top (below home button)

    @pyqtSlot(dict)
    def update_data(self, data_dict):
        # ... (implementation remains the same) ...
        speed = data_dict.get('SPEED'); self.speed_value.setText(f"{speed} km/h" if speed is not None else "---")
        rpm = data_dict.get('RPM'); self.rpm_value.setText(f"{int(rpm)}" if rpm is not None else "---")
        coolant_temp = data_dict.get('COOLANT_TEMP'); self.coolant_value.setText(f"{coolant_temp} °C" if coolant_temp is not None else "---")
        fuel_level = data_dict.get('FUEL_LEVEL'); self.fuel_value.setText(f"{fuel_level} %" if fuel_level is not None else "---")


    @pyqtSlot(str)
    def update_connection_status(self, status_text):
        # ... (implementation remains the same) ...
        self.status_label.setText(f"Status: {status_text.replace('OBD: ', '')}")

    def go_home(self):
        """Navigate back to the HomeScreen."""
        if self.main_window and isinstance(self.main_window, MainWindow):
            self.main_window.navigate_to(self.main_window.home_screen)
        else:
            print("Error: Cannot navigate home. MainWindow not found.")
