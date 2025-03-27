# gui/main_window.py

import os
import sys

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QStackedWidget, QApplication, QLabel, QMessageBox,
                             QSlider) # Keep QPushButton if used elsewhere
from PyQt6.QtCore import pyqtSlot, Qt, QTimer, QDateTime, QSize

from PyQt6.QtGui import QIcon # Added QIcon


# Keep these imports
from .home_screen import HomeScreen
from .radio_screen import RadioScreen
from .obd_screen import OBDScreen
from .setting_screen import SettingsScreen # Corrected import name
from .styling import apply_theme

from backend.obd_manager import OBDManager
from backend.radio_manager import RadioManager
# from backend.audio_manager import AudioManager

# --- Define Icon Paths (adjust paths if your folder structure is different) ---
ICON_PATH = "assets/icons/" # Base path for icons
ICON_HOME = os.path.join(ICON_PATH, "home.png")
ICON_SETTINGS = os.path.join(ICON_PATH, "settings.png")
ICON_VOLUME = os.path.join(ICON_PATH, "volume.png")
ICON_VOLUME_MUTED = os.path.join(ICON_PATH, "volume_muted.png")
ICON_RESTART = os.path.join(ICON_PATH, "restart.png")
ICON_POWER = os.path.join(ICON_PATH, "power.png")
# ---

class MainWindow(QMainWindow):
    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager

        # --- ADD State Variables ---
        self.is_muted = False
        # Initialize last_volume_level with a sensible default or load from settings
        self.last_volume_level = 50 # Use the same default as the slider
        # TODO: Consider loading self.last_volume_level from settings_manager if you save volume
        # ---
      
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



        # --- Keep Status Labels (but don't put in status bar) ---
        self.obd_status_label = QLabel("OBD: Disconnected")
        self.obd_status_label.setObjectName("statusBarObdLabel") # For styling
        self.radio_status_label = QLabel("Radio: Idle")
        self.radio_status_label.setObjectName("statusBarRadioLabel") # For styling
        # ---
      
        # --- PERSISTENT BOTTOM BAR ---
        self.bottom_bar_widget = QWidget()
        self.bottom_bar_widget.setObjectName("persistentBottomBar") # For styling
        bottom_bar_layout = QHBoxLayout(self.bottom_bar_widget)
        bottom_bar_layout.setContentsMargins(5, 5, 5, 5)
        bottom_bar_layout.setSpacing(10)

        icon_size = QSize(32, 32) # Define a size for the icons
        button_size = QSize(45, 45) # Slightly larger button size for padding
      
        # --- Home Button ---
        self.home_button_bar = QPushButton() # Create empty button
        home_icon = QIcon(ICON_HOME)
        if home_icon.isNull(): print(f"Warning: Failed to load icon: {ICON_HOME}")
        self.home_button_bar.setIcon(home_icon)
        self.home_button_bar.setIconSize(icon_size)
        self.home_button_bar.setFixedSize(button_size) # Use QSize
        self.home_button_bar.setObjectName("homeNavButton")
        self.home_button_bar.setToolTip("Go to Home Screen")
        self.home_button_bar.clicked.connect(self.go_to_home)
        bottom_bar_layout.addWidget(self.home_button_bar)
        
      
        # --- Settings Button ---
        self.settings_button = QPushButton() # Create empty button
        settings_icon = QIcon(ICON_SETTINGS)
        if settings_icon.isNull(): print(f"Warning: Failed to load icon: {ICON_SETTINGS}")
        self.settings_button.setIcon(settings_icon)
        self.settings_button.setIconSize(icon_size)
        self.settings_button.setFixedSize(button_size)
        self.settings_button.setObjectName("settingsNavButton")
        self.settings_button.setToolTip("Open Settings")
        self.settings_button.clicked.connect(self.go_to_settings)
        bottom_bar_layout.addWidget(self.settings_button)

        # --- ADD Status Labels HERE ---
        bottom_bar_layout.addWidget(self.obd_status_label)
        # Optional separator - use a styled QLabel or just spacing
        separator_label = QLabel("|")
        separator_label.setStyleSheet("color: #888;") # Example style
        bottom_bar_layout.addWidget(separator_label)
        bottom_bar_layout.addWidget(self.radio_status_label)
        # --- END ADD Status Labels ---

        bottom_bar_layout.addStretch(1) # Center volume

        # --- Volume Icon ---
        self.volume_icon_button = QPushButton()
        self.volume_normal_icon = QIcon(ICON_VOLUME) # Store normal icon
        self.volume_muted_icon = QIcon(ICON_VOLUME_MUTED) # Store muted icon
        if self.volume_normal_icon.isNull(): print(f"Warning: Failed to load icon: {ICON_VOLUME}")
        if self.volume_muted_icon.isNull(): print(f"Warning: Failed to load icon: {ICON_VOLUME_MUTED}")

        self.volume_icon_button.setIcon(self.volume_normal_icon) # Set initial icon
        self.volume_icon_button.setIconSize(icon_size)
        self.volume_icon_button.setFixedSize(button_size)
        self.volume_icon_button.setObjectName("volumeIcon")
        self.volume_icon_button.setToolTip("Mute / Unmute Volume")
        # self.volume_icon_button.setEnabled(False) # REMOVE THIS LINE
        self.volume_icon_button.setCheckable(True) # Make it act like a toggle visually (optional)
        self.volume_icon_button.clicked.connect(self.toggle_mute) # Connect click signal
        bottom_bar_layout.addWidget(self.volume_icon_button)

        # --- Volume Slider ---
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        # TODO: Load initial volume from SettingsManager if saved
        initial_volume = self.settings_manager.get("volume") or 50 # Example load with default
        self.last_volume_level = initial_volume # Set last level based on loaded/default
        self.volume_slider.setValue(initial_volume)
        self.volume_slider.setFixedWidth(150)
        self.volume_slider.valueChanged.connect(self.volume_slider_changed) # Connect value changed signal
        # TODO: Connect valueChanged also to AudioManager if applicable
        # self.volume_slider.valueChanged.connect(self.audio_manager.set_volume)
        bottom_bar_layout.addWidget(self.volume_slider)

        bottom_bar_layout.addStretch(1) # Push buttons to the right

        # --- Restart Button ---
        self.restart_button_bar = QPushButton() # Create empty button
        restart_icon = QIcon(ICON_RESTART)
        if restart_icon.isNull(): print(f"Warning: Failed to load icon: {ICON_RESTART}")
        self.restart_button_bar.setIcon(restart_icon)
        self.restart_button_bar.setIconSize(icon_size)
        self.restart_button_bar.setFixedSize(button_size)
        self.restart_button_bar.setObjectName("restartNavButton")
        self.restart_button_bar.setToolTip("Restart Application")
        self.restart_button_bar.clicked.connect(self.restart_application)
        bottom_bar_layout.addWidget(self.restart_button_bar)
      
        # --- Power Button ---
        self.power_button = QPushButton() # Create empty button
        power_icon = QIcon(ICON_POWER)
        if power_icon.isNull(): print(f"Warning: Failed to load icon: {ICON_POWER}")
        self.power_button.setIcon(power_icon)
        self.power_button.setIconSize(icon_size)
        self.power_button.setFixedSize(button_size)
        self.power_button.setObjectName("powerNavButton") # Typo fixed: power_button
        self.power_button.setToolTip("Exit Application")
        self.power_button.clicked.connect(self.close)
        bottom_bar_layout.addWidget(self.power_button)

      
        # Add bottom bar widget
        self.main_layout.addWidget(self.bottom_bar_widget)
        self.bottom_bar_widget.setFixedHeight(70) # Adjust height if needed based on button size
        # --- END PERSISTENT BOTTOM BAR ---


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

    def restart_application(self):
        """Gracefully stops threads and restarts the current Python application."""
        print("Attempting to restart application...")
        confirm = QMessageBox.warning(self, "Restart Confirmation",
                                      "Are you sure you want to restart the application?",
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                      QMessageBox.StandardButton.No)

        if confirm == QMessageBox.StandardButton.Yes:
            try:
                # Cleanly stop threads before restarting
                print("Stopping background threads before restart...")
                if hasattr(self, 'radio_manager') and self.radio_manager.isRunning():
                    self.radio_manager.stop()
                    self.radio_manager.wait(1500) # Wait max 1.5s
                if hasattr(self, 'obd_manager') and self.obd_manager.isRunning():
                    self.obd_manager.stop()
                    self.obd_manager.wait(1500) # Wait max 1.5s
                print("Threads stopped.")

                # Get executable and script arguments
                python_executable = sys.executable
                script_args = sys.argv
                print(f"Restarting with: {python_executable} {' '.join(script_args)}")

                # Flush outputs
                sys.stdout.flush()
                sys.stderr.flush()

                # Replace the current process
                os.execv(python_executable, [python_executable] + script_args)

            except Exception as e:
                print(f"Error attempting to restart application: {e}")
                QMessageBox.critical(self, "Restart Error", f"Could not restart application:\n{e}")
                # Fallback: Just exit if restart fails critically
                QApplication.quit()
        else:
            print("Restart cancelled by user.")

    def closeEvent(self, event):
        # Optional: Save the last NON-MUTED volume level
        current_volume = self.volume_slider.value()
        save_volume = self.last_volume_level if self.is_muted and self.last_volume_level > 0 else current_volume
        if save_volume > 0: # Don't save 0 if muted, save last level instead
             self.settings_manager.set("volume", save_volume)
        elif current_volume == 0 and not self.is_muted: # If user manually set to 0
             self.settings_manager.set("volume", 0)

        print("Close event triggered. Stopping background threads...")
        # ... (rest of closeEvent: stop threads, accept event) ...
        if hasattr(self, 'radio_manager') and self.radio_manager.isRunning(): self.radio_manager.stop(); self.radio_manager.wait(1500)
        if hasattr(self, 'obd_manager') and self.obd_manager.isRunning(): self.obd_manager.stop(); self.obd_manager.wait(1500)
        if hasattr(self, 'radio_manager') and self.radio_manager.radio_type != "none": self.settings_manager.set("last_fm_station", self.radio_manager.current_frequency)
        print("Threads stopped. Exiting.")
        event.accept()


    def toggle_mute(self):
        """Toggles volume mute state."""
        if self.is_muted:
            # --- Unmuting ---
            # Restore slider to last known non-zero level (or a default if last was 0)
            restore_level = self.last_volume_level if self.last_volume_level > 0 else 50 # Restore to 50 if last level was 0
            self.volume_slider.setValue(restore_level)
            self.volume_icon_button.setIcon(self.volume_normal_icon)
            self.is_muted = False
            self.volume_icon_button.setChecked(False) # Update toggle state
            print(f"Volume Unmuted. Restored level to {restore_level}")
        else:
            # --- Muting ---
            current_volume = self.volume_slider.value()
            # Store the current level ONLY if it's not already 0
            if current_volume > 0:
                self.last_volume_level = current_volume
            # Set slider to 0
            self.volume_slider.setValue(0)
            self.volume_icon_button.setIcon(self.volume_muted_icon)
            self.is_muted = True
            self.volume_icon_button.setChecked(True) # Update toggle state
            print(f"Volume Muted. Last level was {self.last_volume_level}")
        # TODO: Tell AudioManager about the mute/unmute or new volume level (0 or restored)
        # self.audio_manager.set_mute(self.is_muted)
        # or self.audio_manager.set_volume(self.volume_slider.value())

    # --- ADD THIS METHOD ---
    @pyqtSlot(int)
    def volume_slider_changed(self, value):
        """Handles manual slider changes, potentially unmuting."""
        # If the slider is moved manually WHILE muted, unmute visually and functionally
        if self.is_muted and value > 0:
            self.is_muted = False
            self.volume_icon_button.setIcon(self.volume_normal_icon)
            self.volume_icon_button.setChecked(False)
            print("Unmuted due to slider movement.")
            # Update last_volume_level to the new user-set value
            self.last_volume_level = value
        # If user slides TO 0 manually (not muted), update last level before it becomes 0
        # But only if the previous value wasn't already 0
        # This is tricky, maybe handle only the unmute case above is sufficient
        # elif not self.is_muted and value > 0:
        #     self.last_volume_level = value # Keep track of last non-zero setting

        # TODO: Send the 'value' to the AudioManager
        # self.audio_manager.set_volume(value)
        # print(f"Volume set to {value}") # Debug

  
    # --- ADD THIS METHOD TO MainWindow ---
    def go_to_home(self):
        """Navigates to the home screen."""
        print("Home button clicked, navigating...")
        self.navigate_to(self.home_screen)
    # --- END ADD METHOD ---

  
    # --- ADD THIS METHOD TO MainWindow ---
    def go_to_settings(self):
        """Navigates to the settings screen."""
        print("Settings button clicked, navigating...")
        self.navigate_to(self.settings_screen)
    # --- END ADD METHOD ---
  
    # --- Add a helper method for navigation if desired ---
    def navigate_to(self, screen_widget):
        """Sets the current screen in the stacked widget."""
        if screen_widget in self.stacked_widget.findChildren(QWidget):
            self.stacked_widget.setCurrentWidget(screen_widget)
        else:
            print(f"Error: Cannot navigate to {screen_widget}. Not found in stack.")
