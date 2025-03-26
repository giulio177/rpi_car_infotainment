from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGridLayout
from PyQt6.QtCore import pyqtSlot, Qt

class OBDScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)

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

        self.layout.addStretch(1) # Push content towards the top

    @pyqtSlot(dict)
    def update_data(self, data_dict):
        """Slot to receive data updates from OBDManager."""
        # Update labels based on the keys in the dictionary
        speed = data_dict.get('SPEED')
        if speed is not None:
            self.speed_value.setText(f"{speed} km/h") # Assuming km/h from python-obd
        else:
            self.speed_value.setText("---")

        rpm = data_dict.get('RPM')
        if rpm is not None:
            self.rpm_value.setText(f"{int(rpm)}") # RPM is usually integer
        else:
             self.rpm_value.setText("---")

        coolant_temp = data_dict.get('COOLANT_TEMP')
        if coolant_temp is not None:
            self.coolant_value.setText(f"{coolant_temp} °C") # Assuming Celsius
        else:
             self.coolant_value.setText("---")

        fuel_level = data_dict.get('FUEL_LEVEL')
        if fuel_level is not None:
            self.fuel_value.setText(f"{fuel_level} %")
        else:
            self.fuel_value.setText("---") # Often not supported

        # Update other labels...


    @pyqtSlot(str)
    def update_connection_status(self, status_text):
        self.status_label.setText(f"Status: {status_text.replace('OBD: ', '')}")