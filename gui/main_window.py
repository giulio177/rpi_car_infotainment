# gui/main_window.py

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QStackedWidget, QApplication, QLabel, QStatusBar) # Keep QPushButton if used elsewhere
from PyQt6.QtCore import pyqtSlot, Qt

# Keep these imports
from .home_screen import HomeScreen
from .radio_screen import RadioScreen
from .obd_screen import OBDScreen
from .setting_screen import SettingsScreen # Corrected import name
from .styling import apply_theme

from backend.obd_manager import OBDManager
from backend.radio_manager import RadioManager
# from backend.audio_manager import AudioManager

class MainWindow(QMainWindow):
    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager

        self.setWindowTitle("RPi Car Infotainment")

        # --- Apply Resolution from Settings ---
        try:
            resolution = self.settings_manager.get("window_resolution")
            if isinstance(resolution, list) and len(resolution) == 2:
                 self.resize(resolution[0], resolution[1])
                 print(f"Window resized to: {resolution[0]}x{resolution[1]}")
            else:
                 print("Warning: Invalid resolution setting found, using default 1024x600.")
                 default_res = self.settings_manager.defaults.get("window_resolution", [1024, 600])
                 self.resize(default_res[0], default_res[1])
        except Exception as e:
            print(f"Error applying resolution setting: {e}. Using default 1024x600.")
            self.resize(1024, 600)

        self.current_theme = self.settings_manager.get("theme")
        apply_theme(QApplication.instance(), self.current_theme)

        # --- Central Widget Area ---
        self.central_widget = QWidget()
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.setCentralWidget(self.central_widget)

        # --- Stacked Widget for Screens (Keep This) ---
        self.stacked_widget = QStackedWidget()
        self.main_layout.addWidget(self.stacked_widget, 1) # Takes up main space

        # --- Navigation Bar (REMOVE THIS SECTION) ---
        # self.nav_bar = QWidget()
        # self.nav_layout = QHBoxLayout(self.nav_bar)
        # self.nav_layout.setContentsMargins(5, 5, 5, 5)
        # self.nav_layout.addStretch(1)
        # self.btn_home = QPushButton("Home") # Remove
        # self.btn_radio = QPushButton("Radio") # Remove
        # self.btn_obd = QPushButton("OBD") # Remove
        # self.btn_settings = QPushButton("Settings") # Remove
        # self.nav_layout.addWidget(self.btn_home) # Remove
        # self.nav_layout.addWidget(self.btn_radio) # Remove
        # self.nav_layout.addWidget(self.btn_obd) # Remove
        # self.nav_layout.addWidget(self.btn_settings) # Remove
        # self.nav_layout.addStretch(1)
        # self.main_layout.addWidget(self.nav_bar) # Remove this line

        # --- Status Bar (Keep This) ---
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.obd_status_label = QLabel("OBD: Disconnected")
        self.radio_status_label = QLabel("Radio: Idle")
        self.status_bar.addPermanentWidget(self.obd_status_label)
        self.status_bar.addPermanentWidget(QLabel("|")) # Separator
        self.status_bar.addPermanentWidget(self.radio_status_label)

        # --- Initialize Backend Managers (Keep This) ---
        self.obd_manager = OBDManager(
            port=self.settings_manager.get("obd_port"),
            baudrate=self.settings_manager.get("obd_baudrate")
        )
        self.radio_manager = RadioManager(
             radio_type=self.settings_manager.get("radio_type"),
             i2c_address=self.settings_manager.get("radio_i2c_address"),
             initial_freq=self.settings_manager.get("last_fm_station") # Use corrected get()
        )
        # self.audio_manager = AudioManager()

        # --- Initialize Screens (Keep This - Pass self for navigation) ---
        self.home_screen = HomeScreen(parent=self) # Pass self or main_window reference if needed
        self.radio_screen = RadioScreen(self.radio_manager, parent=self)
        self.obd_screen = OBDScreen(parent=self)
        # Pass self to settings screen to allow theme/config updates AND navigation back
        self.settings_screen = SettingsScreen(self.settings_manager, self)

        # --- Add Screens to Stack (Keep This) ---
        self.stacked_widget.addWidget(self.home_screen)
        self.stacked_widget.addWidget(self.radio_screen)
        self.stacked_widget.addWidget(self.obd_screen)
        self.stacked_widget.addWidget(self.settings_screen)

        # --- Connect Navigation Buttons (REMOVE THIS SECTION) ---
        # self.btn_home.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.home_screen))
        # self.btn_radio.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.radio_screen))
        # self.btn_obd.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.obd_screen))
        # self.btn_settings.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.settings_screen))

        # --- Connect Backend Signals to GUI Slots (Keep This) ---
        self.obd_manager.connection_status.connect(self.update_obd_status)
        self.obd_manager.data_updated.connect(self.obd_screen.update_data)
        self.radio_manager.radio_status.connect(self.update_radio_status)
        self.radio_manager.frequency_updated.connect(self.radio_screen.update_frequency)
        self.radio_manager.signal_strength.connect(self.radio_screen.update_signal_strength)

        # --- Start Backend Threads (Keep This) ---
        self.obd_manager.start()
        if self.radio_manager.radio_type != "none":
            self.radio_manager.start()
        else:
            self.update_radio_status("Disabled")

        # Set initial screen
        self.stacked_widget.setCurrentWidget(self.home_screen)


    # --- Keep Methods like update_obd_status, update_radio_status, etc. ---
    @pyqtSlot(bool, str)
    def update_obd_status(self, connected, message):
        # ... (implementation remains the same) ...
        status_text = f"OBD: {message}"
        self.obd_status_label.setText(status_text)
        style = "color: green;" if connected else "color: red;"
        self.obd_status_label.setStyleSheet(style)
        self.obd_screen.update_connection_status(status_text)

    @pyqtSlot(str)
    def update_radio_status(self, status):
        # ... (implementation remains the same) ...
        self.radio_status_label.setText(f"Radio: {status}")
        self.radio_screen.update_status_display(status)

    def switch_theme(self, theme_name):
        # ... (implementation remains the same) ...
        if theme_name != self.current_theme:
            print(f"Switching theme to: {theme_name}")
            self.current_theme = theme_name
            apply_theme(QApplication.instance(), self.current_theme)
            self.settings_manager.set("theme", theme_name)

    def update_obd_config(self):
        # ... (implementation remains the same) ...
        print("OBD configuration updated. Restarting OBD Manager...")
        # ... (stop, wait, create new, reconnect, start) ...
        self.obd_manager.stop()
        self.obd_manager.wait()
        self.obd_manager = OBDManager(
            port=self.settings_manager.get("obd_port"),
            baudrate=self.settings_manager.get("obd_baudrate")
        )
        self.obd_manager.connection_status.connect(self.update_obd_status)
        self.obd_manager.data_updated.connect(self.obd_screen.update_data)
        self.obd_manager.start()


    def update_radio_config(self):
        # ... (implementation remains the same) ...
        print("Radio configuration updated. Restarting Radio Manager...")
        # ... (stop, wait, create new, reconnect, start) ...
        self.radio_manager.stop()
        self.radio_manager.wait()
        self.radio_manager = RadioManager(
             radio_type=self.settings_manager.get("radio_type"),
             i2c_address=self.settings_manager.get("radio_i2c_address"),
             initial_freq=self.settings_manager.get("last_fm_station")
        )
        self.radio_manager.radio_status.connect(self.update_radio_status)
        self.radio_manager.frequency_updated.connect(self.radio_screen.update_frequency)
        self.radio_manager.signal_strength.connect(self.radio_screen.update_signal_strength)
        if self.radio_manager.radio_type != "none":
            self.radio_manager.start()
        else:
             self.update_radio_status("Disabled")


    def closeEvent(self, event):
        # ... (implementation remains the same) ...
        print("Close event triggered. Stopping background threads...")
        self.radio_manager.stop()
        self.obd_manager.stop()
        self.radio_manager.wait()
        self.obd_manager.wait()
        if self.radio_manager.radio_type != "none":
            self.settings_manager.set("last_fm_station", self.radio_manager.current_frequency)
        print("Threads stopped. Exiting.")
        event.accept()

    # --- Add a helper method for navigation if desired ---
    def navigate_to(self, screen_widget):
        """Sets the current screen in the stacked widget."""
        if screen_widget in self.stacked_widget.findChildren(QWidget):
            self.stacked_widget.setCurrentWidget(screen_widget)
        else:
            print(f"Error: Cannot navigate to {screen_widget}. Not found in stack.")
