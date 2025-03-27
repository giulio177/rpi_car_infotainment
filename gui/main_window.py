from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QStackedWidget, QApplication, QLabel, QStatusBar)
from PyQt6.QtCore import pyqtSlot, Qt

from .home_screen import HomeScreen
from .radio_screen import RadioScreen
from .obd_screen import OBDScreen
from .setting_screen import SettingsScreen
from .styling import apply_theme

from backend.obd_manager import OBDManager
from backend.radio_manager import RadioManager
# from backend.audio_manager import AudioManager # If you create one

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
                 # Fallback to default if setting is invalid
                 default_res = self.settings_manager.defaults.get("window_resolution", [1024, 600])
                 self.resize(default_res[0], default_res[1])
        except Exception as e:
            print(f"Error applying resolution setting: {e}. Using default 1024x600.")
            self.resize(1024, 600) # Hardcoded fallback

        # Consider setting flags for kiosk mode if needed:
        # self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

        self.current_theme = self.settings_manager.get("theme")
        apply_theme(QApplication.instance(), self.current_theme)

        # --- Central Widget Area ---
        self.central_widget = QWidget()
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0) # Use full window
        self.main_layout.setSpacing(0)
        self.setCentralWidget(self.central_widget)

        # --- Stacked Widget for Screens ---
        self.stacked_widget = QStackedWidget()
        self.main_layout.addWidget(self.stacked_widget, 1) # Give it stretch factor

        # --- Navigation Bar ---
        self.nav_bar = QWidget()
        self.nav_layout = QHBoxLayout(self.nav_bar)
        self.nav_layout.setContentsMargins(5, 5, 5, 5)
        # Make nav buttons, distribute evenly
        self.nav_layout.addStretch(1)
        self.btn_home = QPushButton("Home")
        self.btn_radio = QPushButton("Radio")
        self.btn_obd = QPushButton("OBD")
        self.btn_settings = QPushButton("Settings")
        self.nav_layout.addWidget(self.btn_home)
        self.nav_layout.addWidget(self.btn_radio)
        self.nav_layout.addWidget(self.btn_obd)
        self.nav_layout.addWidget(self.btn_settings)
        self.nav_layout.addStretch(1)
        self.main_layout.addWidget(self.nav_bar) # Add nav bar at the bottom

        # --- Status Bar ---
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.obd_status_label = QLabel("OBD: Disconnected")
        self.radio_status_label = QLabel("Radio: Idle")
        self.status_bar.addPermanentWidget(self.obd_status_label)
        self.status_bar.addPermanentWidget(QLabel("|")) # Separator
        self.status_bar.addPermanentWidget(self.radio_status_label)


        # --- Initialize Backend Managers ---
        self.obd_manager = OBDManager(
            port=self.settings_manager.get("obd_port"),
            baudrate=self.settings_manager.get("obd_baudrate")
        )
        self.radio_manager = RadioManager(
             radio_type=self.settings_manager.get("radio_type"),
             i2c_address=self.settings_manager.get("radio_i2c_address"),
             initial_freq = self.settings_manager.get("last_fm_station")
        )
        # self.audio_manager = AudioManager() # If needed

        # --- Initialize Screens ---
        self.home_screen = HomeScreen()
        self.radio_screen = RadioScreen(self.radio_manager)
        self.obd_screen = OBDScreen()
        self.setting_screen = SettingsScreen(self.settings_manager, self) # Pass self to allow theme changes

        # --- Add Screens to Stack ---
        self.stacked_widget.addWidget(self.home_screen)
        self.stacked_widget.addWidget(self.radio_screen)
        self.stacked_widget.addWidget(self.obd_screen)
        self.stacked_widget.addWidget(self.setting_screen)

        # --- Connect Navigation Buttons ---
        self.btn_home.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.home_screen))
        self.btn_radio.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.radio_screen))
        self.btn_obd.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.obd_screen))
        self.btn_settings.clicked.connect(lambda: self.stacked_widget.setCurrentWidget(self.setting_screen))

        # --- Connect Backend Signals to GUI Slots ---
        # OBD Connections
        self.obd_manager.connection_status.connect(self.update_obd_status)
        self.obd_manager.data_updated.connect(self.obd_screen.update_data) # Connect to OBD screen's slot

        # Radio Connections
        self.radio_manager.radio_status.connect(self.update_radio_status)
        self.radio_manager.frequency_updated.connect(self.radio_screen.update_frequency)
        self.radio_manager.signal_strength.connect(self.radio_screen.update_signal_strength)
        # Connect RDS signal if implemented:
        # self.radio_manager.rds_data_updated.connect(self.radio_screen.update_rds)

        # --- Start Backend Threads ---
        self.obd_manager.start()
        if self.radio_manager.radio_type != "none":
            self.radio_manager.start()
        else:
            self.update_radio_status("Disabled")

    @pyqtSlot(bool, str)
    def update_obd_status(self, connected, message):
        status_text = f"OBD: {message}"
        self.obd_status_label.setText(status_text)
        # Optionally change color based on status
        style = "color: green;" if connected else "color: red;"
        self.obd_status_label.setStyleSheet(style)
        # Update status on OBD screen as well?
        self.obd_screen.update_connection_status(status_text)


    @pyqtSlot(str)
    def update_radio_status(self, status):
        self.radio_status_label.setText(f"Radio: {status}")
        # Also update status label on the radio screen itself
        self.radio_screen.update_status_display(status)

    def switch_theme(self, theme_name):
        """Called by settings screen to change theme."""
        if theme_name != self.current_theme:
            print(f"Switching theme to: {theme_name}")
            self.current_theme = theme_name
            apply_theme(QApplication.instance(), self.current_theme)
            self.settings_manager.set("theme", theme_name)
            # You might need to force redraw on some custom widgets if styles don't apply automatically

    def update_obd_config(self):
        """Called by settings screen after OBD settings change."""
        print("OBD configuration updated. Restarting OBD Manager...")
        self.obd_manager.stop()
        self.obd_manager.wait() # Wait for thread to finish
        self.obd_manager = OBDManager( # Create new instance with new settings
            port=self.settings_manager.get("obd_port"),
            baudrate=self.settings_manager.get("obd_baudrate")
        )
        # Reconnect signals
        self.obd_manager.connection_status.connect(self.update_obd_status)
        self.obd_manager.data_updated.connect(self.obd_screen.update_data)
        self.obd_manager.start()

    def update_radio_config(self):
        """Called by settings screen after Radio settings change."""
        print("Radio configuration updated. Restarting Radio Manager...")
        self.radio_manager.stop()
        self.radio_manager.wait()
        self.radio_manager = RadioManager(
             radio_type=self.settings_manager.get("radio_type"),
             i2c_address=self.settings_manager.get("radio_i2c_address"),
             initial_freq=self.settings_manager.get("last_fm_station", 98.5)
        )
         # Reconnect signals
        self.radio_manager.radio_status.connect(self.update_radio_status)
        self.radio_manager.frequency_updated.connect(self.radio_screen.update_frequency)
        self.radio_manager.signal_strength.connect(self.radio_screen.update_signal_strength)
        # self.radio_manager.rds_data_updated.connect(self.radio_screen.update_rds)

        if self.radio_manager.radio_type != "none":
            self.radio_manager.start()
        else:
             self.update_radio_status("Disabled")


    def closeEvent(self, event):
        """Ensure threads are stopped cleanly on exit."""
        print("Close event triggered. Stopping background threads...")
        self.radio_manager.stop()
        self.obd_manager.stop()

        # Wait for threads to finish (add timeout?)
        self.radio_manager.wait()
        self.obd_manager.wait()

        # Save last radio frequency
        if self.radio_manager.radio_type != "none":
            self.settings_manager.set("last_fm_station", self.radio_manager.current_frequency)

        print("Threads stopped. Exiting.")
        event.accept() # Proceed with closing
