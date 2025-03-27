# gui/obd_screen.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QGridLayout,
                             QPushButton, QHBoxLayout, QSpacerItem, QSizePolicy)
from PyQt6.QtCore import QTimer, QDateTime, pyqtSlot, Qt

# REMOVE OR COMMENT OUT THIS LINE:
# from .main_window import MainWindow


class OBDScreen(QWidget):
    def __init__(self, parent=None): # parent is likely MainWindow
        super().__init__(parent)
        # Store the parent (which should be the MainWindow instance)
        self.main_window = parent

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(10) # Add some spacing

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(5, 5, 5, 5) # Adjust margins as needed
        header_layout.setSpacing(10)
        
        # --- NEW: Header Title Label ---
        # CHANGE "Screen Title" for each screen
        self.header_title_label = QLabel("OBD-II Data") # e.g., "Home", "OBD-II Data", "FM Radio", "Settings"
        self.header_title_label.setObjectName("headerTitle")
        self.header_title_label.setStyleSheet("font-size: 16pt; font-weight: bold;") # Basic style
        header_layout.addWidget(self.header_title_label)
        
        # --- NEW: Spacer to push elements right ---
        spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        header_layout.addItem(spacer)
        
        # --- MOVE Home Button Here ---
        # (Copy the existing home_button creation logic here)
        self.home_button = QPushButton("🏠")
        self.home_button.setFixedSize(40, 40)
        self.home_button.setObjectName("homeNavButton")
        self.home_button.clicked.connect(self.go_home) # Assumes go_home exists
        header_layout.addWidget(self.home_button) # Add to header
        
        # --- MOVE Restart Button Here ---
        # (Copy the existing restart_button creation logic here)
        self.restart_button = QPushButton("🔄")
        self.restart_button.setFixedSize(40, 40)
        self.restart_button.setObjectName("restartNavButton")
        self.restart_button.setToolTip("Restart Application")
        self.restart_button.clicked.connect(self.on_restart_clicked) # Assumes on_restart_clicked exists
        header_layout.addWidget(self.restart_button) # Add to header
        
        # --- NEW: Clock Label ---
        self.clock_label = QLabel("00:00")
        self.clock_label.setObjectName("headerClock")
        self.clock_label.setStyleSheet("font-size: 16pt;") # Basic style
        header_layout.addWidget(self.clock_label)
        
        # --- NEW: Clock Timer Setup ---
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(10000) # Update every 10 seconds (1000ms = 1 sec) - adjust as needed
        self._update_clock() # Initial update
        
        # --- ADD Header Layout to Main Layout (at the TOP) ---
        self.main_layout.addLayout(header_layout)


        # --- Existing OBD Screen Content ---
        self.title_label = QLabel("OBD-II Data")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-size: 24pt; font-weight: bold; margin-bottom: 15px;")
        self.main_layout.addWidget(self.title_label)

        self.status_label = QLabel("Status: Initializing...")
        self.layout.addWidget(self.status_label)

        # Grid layout for data
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(10)
        self.layout.addLayout(self.grid_layout)

        # --- Labels for specific data points ---
        self.speed_label = QLabel("Speed:")
        self.speed_value = QLabel("---")
        self.rpm_label = QLabel("RPM:")
        self.rpm_value = QLabel("---")
        self.coolant_label = QLabel("Coolant Temp:")
        self.coolant_value = QLabel("---")
        self.fuel_label = QLabel("Fuel Level:")
        self.fuel_value = QLabel("---")
        # Add more labels/values as needed

        # Style value labels
        value_style = "font-size: 22pt; font-weight: bold; color: #007bff;" # Example blue color
        self.speed_value.setStyleSheet(value_style)
        self.rpm_value.setStyleSheet(value_style)
        self.coolant_value.setStyleSheet(value_style)
        self.fuel_value.setStyleSheet(value_style)

        # Add widgets to grid (Row, Column, RowSpan, ColSpan)
        self.grid_layout.addWidget(self.speed_label, 0, 0)
        self.grid_layout.addWidget(self.speed_value, 0, 1)
        self.grid_layout.addWidget(self.rpm_label, 1, 0)
        self.grid_layout.addWidget(self.rpm_value, 1, 1)
        self.grid_layout.addWidget(self.coolant_label, 0, 2)
        self.grid_layout.addWidget(self.coolant_value, 0, 3)
        self.grid_layout.addWidget(self.fuel_label, 1, 2)
        self.grid_layout.addWidget(self.fuel_value, 1, 3)

        self.main_layout.addStretch(1) # Push content towards the top (below home button)

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

    @pyqtSlot(str)
    def update_connection_status(self, status_text):
        self.status_label.setText(f"Status: {status_text.replace('OBD: ', '')}")

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

    def _update_clock(self):
        """Updates the clock label with the current time."""
        current_time = QDateTime.currentDateTime()
        time_str = current_time.toString("HH:mm") # Format as Hour:Minute
        self.clock_label.setText(time_str)
