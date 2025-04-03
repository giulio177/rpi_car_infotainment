# gui/main_window.py

import os
import sys

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QStackedWidget, QApplication, QLabel, QMessageBox,
                             QSlider) # Keep QPushButton if used elsewhere
from PyQt6.QtCore import pyqtSlot, Qt, QTimer, QDateTime, QSize, QMargins

from PyQt6.QtGui import QIcon # Added QIcon


# Keep these imports
from .home_screen import HomeScreen
from .radio_screen import RadioScreen
from .obd_screen import OBDScreen
from .setting_screen import SettingsScreen # Corrected import name
from .styling import apply_theme, scale_value

from backend.obd_manager import OBDManager
from backend.radio_manager import RadioManager
from backend.audio_manager import AudioManager

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
    BASE_RESOLUTION = QSize(1024, 600) # Design resolution

    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.audio_manager = AudioManager()

        # --- Define Base Sizes used in code (not just QSS) ---
        self.base_icon_size = QSize(32, 32)
        self.base_bottom_bar_button_size = QSize(45, 45)
        self.base_bottom_bar_height = 70 # Base height for the bottom bar
        self.base_volume_slider_width = 150
        self.base_layout_spacing = 10
        self.base_layout_margin = 5 # For bottom bar contents margin
        self.base_main_margin = 10 # For main window content margins (used in child screens too)

        # ---  Volume Mute Variables ---
        # Get initial system mute status if possible, otherwise assume not muted
        initial_system_mute = self.audio_manager.get_mute_status()
        self.is_muted = initial_system_mute if initial_system_mute is not None else False

        # Load last saved volume level from settings, default to 50
        # This is the level we restore to when unmuting
        self.last_volume_level = self.settings_manager.get("volume") or 50
        # Ensure last_volume_level isn't 0 if we are not initially muted
        if not self.is_muted and self.last_volume_level == 0:
            self.last_volume_level = 50 # Default restore level if saved was 0
        # ---

        # --- Borderless Window ---
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setWindowTitle("RPi Car Infotainment")

        # --- Apply Resolution from Settings ---
        try:
            resolution = self.settings_manager.get("window_resolution")
            if isinstance(resolution, list) and len(resolution) == 2:
                 # self.resize(resolution[0], resolution[1]) # DEFER RESIZE until after UI setup
                 self._initial_width = resolution[0]
                 self._initial_height = resolution[1]
                 print(f"Target resolution set to: {resolution[0]}x{resolution[1]}")
            else:
                 print("Warning: Invalid resolution setting found, using default.")
                 default_res = self.settings_manager.defaults.get("window_resolution", [1024, 600])
                 # self.resize(default_res[0], default_res[1]) # DEFER RESIZE
                 self._initial_width = default_res[0]
                 self._initial_height = default_res[1]
        except Exception as e:
            print(f"Error applying resolution setting: {e}. Using default.")
            # self.resize(1024, 600) # DEFER RESIZE
            self._initial_width = 1024
            self._initial_height = 600


        # --- Apply Theme ---
        self.current_theme = self.settings_manager.get("theme")
        # apply_theme(QApplication.instance(), self.current_theme) # Moved lower

        # --- Central Widget Area ---
        self.central_widget = QWidget()
        self.main_layout = QVBoxLayout(self.central_widget)
        # self.main_layout.setContentsMargins(0, 0, 0, 0) # Margins set by scaling
        # self.main_layout.setSpacing(0) # Spacing set by scaling
        self.setCentralWidget(self.central_widget)

        # --- Stacked Widget for Screens (Keep This) ---
        self.stacked_widget = QStackedWidget()
        self.main_layout.addWidget(self.stacked_widget, 1) # Takes up main space

        # --- Status Labels ---
        self.obd_status_label = QLabel("OBD: Disconnected")
        self.obd_status_label.setObjectName("statusBarObdLabel") # For styling
        self.radio_status_label = QLabel("Radio: Idle")
        self.radio_status_label.setObjectName("statusBarRadioLabel") # For styling
        # ---
      
        # --- PERSISTENT BOTTOM BAR ---
        self.bottom_bar_widget = QWidget()
        self.bottom_bar_widget.setObjectName("persistentBottomBar") # For styling
        bottom_bar_layout = QHBoxLayout(self.bottom_bar_widget)
        # self.bottom_bar_layout.setContentsMargins(5, 5, 5, 5) # Set by scaling
        # self.bottom_bar_layout.setSpacing(10) # Set by scaling

        # --- Create bottom bar buttons (sizes set by scaling) ---
        self.home_button_bar = QPushButton()
        self.home_icon = QIcon(ICON_HOME) # Store icon ref
        self.home_button_bar.setIcon(self.home_icon)
        self.home_button_bar.setObjectName("homeNavButton")
        self.home_button_bar.setToolTip("Go to Home Screen")
        self.home_button_bar.clicked.connect(self.go_to_home)

        self.settings_button = QPushButton()
        self.settings_icon = QIcon(ICON_SETTINGS) # Store icon ref
        self.settings_button.setIcon(self.settings_icon)
        self.settings_button.setObjectName("settingsNavButton")
        self.settings_button.setToolTip("Open Settings")
        self.settings_button.clicked.connect(self.go_to_settings)

        self.volume_icon_button = QPushButton()
        self.volume_normal_icon = QIcon(ICON_VOLUME)
        self.volume_muted_icon = QIcon(ICON_VOLUME_MUTED)
        self.volume_icon_button.setIcon(self.volume_normal_icon) # Initial set later
        self.volume_icon_button.setObjectName("volumeIcon")
        self.volume_icon_button.setToolTip("Mute / Unmute Volume")
        self.volume_icon_button.setCheckable(True)
        self.volume_icon_button.clicked.connect(self.toggle_mute)

        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.valueChanged.connect(self.volume_slider_changed)

        self.restart_button_bar = QPushButton()
        self.restart_icon = QIcon(ICON_RESTART) # Store icon ref
        self.restart_button_bar.setIcon(self.restart_icon)
        self.restart_button_bar.setObjectName("restartNavButton")
        self.restart_button_bar.setToolTip("Restart Application")
        self.restart_button_bar.clicked.connect(self.restart_application)

        self.power_button = QPushButton()
        self.power_icon = QIcon(ICON_POWER) # Store icon ref
        self.power_button.setIcon(self.power_icon)
        self.power_button.setObjectName("powerNavButton")
        self.power_button.setToolTip("Exit Application")
        self.power_button.clicked.connect(self.close)

        # --- Add widgets to bottom bar layout ---
        self.bottom_bar_layout.addWidget(self.home_button_bar)
        self.bottom_bar_layout.addWidget(self.settings_button)
        self.bottom_bar_layout.addStretch(1) # Push status labels towards center
        self.bottom_bar_layout.addWidget(self.obd_status_label)
        self.bottom_bar_layout.addWidget(self.separator_label)
        self.bottom_bar_layout.addWidget(self.radio_status_label)
        self.bottom_bar_layout.addStretch(2) # More stretch towards center
        self.bottom_bar_layout.addWidget(self.volume_icon_button)
        self.bottom_bar_layout.addWidget(self.volume_slider)
        self.bottom_bar_layout.addStretch(2) # Push end buttons right
        self.bottom_bar_layout.addWidget(self.restart_button_bar)
        self.bottom_bar_layout.addWidget(self.power_button)

        # Add bottom bar widget to main layout
        self.main_layout.addWidget(self.bottom_bar_widget)
        # self.bottom_bar_widget.setFixedHeight(70) # Height set by scaling


        # --- Initialize Backend Managers ---
        self.obd_manager = OBDManager(
            port=self.settings_manager.get("obd_port"),
            baudrate=self.settings_manager.get("obd_baudrate")
        )
        self.radio_manager = RadioManager(
             radio_type=self.settings_manager.get("radio_type"),
             i2c_address=self.settings_manager.get("radio_i2c_address"),
             initial_freq=self.settings_manager.get("last_fm_station") # Use corrected get()
        )

        # --- Initialize Screens (Keep This - Pass self for navigation) ---
        self.home_screen = HomeScreen(parent=self)
        self.radio_screen = RadioScreen(self.radio_manager, parent=self)
        self.obd_screen = OBDScreen(parent=self)
        self.settings_screen = SettingsScreen(self.settings_manager, self)

        # --- Add Screens to Stack (Keep This) ---
        self.stacked_widget.addWidget(self.home_screen)
        self.stacked_widget.addWidget(self.radio_screen)
        self.stacked_widget.addWidget(self.obd_screen)
        self.stacked_widget.addWidget(self.settings_screen)

        # --- Connect Backend Signals to GUI Slots (Keep This) ---
        self.obd_manager.connection_status.connect(self.update_obd_status)
        self.obd_manager.data_updated.connect(self.obd_screen.update_data)
        self.radio_manager.radio_status.connect(self.update_radio_status)
        self.radio_manager.frequency_updated.connect(self.radio_screen.update_frequency)
        self.radio_manager.signal_strength.connect(self.radio_screen.update_signal_strength)

        # --- Initialize Volume/Mute States (Moved after widgets are created) ---
        initial_system_mute = self.audio_manager.get_mute_status()
        self.is_muted = initial_system_mute if initial_system_mute is not None else False
        self.last_volume_level = self.settings_manager.get("volume") or 50
        if not self.is_muted and self.last_volume_level == 0:
            self.last_volume_level = 50

        # Update volume button based on initial state
        initial_icon = self.volume_muted_icon if self.is_muted else self.volume_normal_icon
        self.volume_icon_button.setIcon(initial_icon)
        self.volume_icon_button.setChecked(self.is_muted)

        # Set initial slider value and sync system volume
        initial_slider_value = self.audio_manager.get_volume()
        if initial_slider_value is None:
            initial_slider_value = 0 if self.is_muted else self.last_volume_level
        self.volume_slider.setValue(initial_slider_value)
        if not self.is_muted:
             self.audio_manager.set_volume(initial_slider_value)
        else:
             self.audio_manager.set_mute(True)

        # --- Start Backend Threads (Keep This) ---
        self.obd_manager.start()
        if self.radio_manager.radio_type != "none":
            self.radio_manager.start()
        else:
            self.update_radio_status("Disabled")

        # Set initial screen
        self.stacked_widget.setCurrentWidget(self.home_screen)

        # --- Apply initial scaling and resize ---
        self._apply_scaling() # Apply scaling based on initial size
        self.resize(self._initial_width, self._initial_height) # Now resize the window

        # --- Apply Theme (Needs to happen AFTER scaling so QSS uses correct values) ---
        # We need the scale factor for the theme application now
        scale_factor = self.height() / self.BASE_RESOLUTION.height() if self.BASE_RESOLUTION.height() > 0 else 1.0
        apply_theme(QApplication.instance(), self.current_theme, scale_factor)


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


    # --- ADDED: resizeEvent handler ---
    def resizeEvent(self, event):
        """Override resizeEvent to apply scaling when window size changes."""
        super().resizeEvent(event) # Call base class implementation
        print(f"Window resized to: {event.size().width()}x{event.size().height()}")
        self._apply_scaling()

    # --- ADDED: Central scaling logic ---
    def _apply_scaling(self):
        """Applies scaling to UI elements based on current window height."""
        current_height = self.height()
        if self.BASE_RESOLUTION.height() <= 0 or current_height <= 0: # Prevent division by zero
             scale_factor = 1.0
        else:
             scale_factor = current_height / self.BASE_RESOLUTION.height()

        # --- Scale elements controlled directly ---
        scaled_icon_size = QSize(
            scale_value(self.base_icon_size.width(), scale_factor),
            scale_value(self.base_icon_size.height(), scale_factor)
        )
        scaled_button_size = QSize(
             scale_value(self.base_bottom_bar_button_size.width(), scale_factor),
             scale_value(self.base_bottom_bar_button_size.height(), scale_factor)
        )
        scaled_bottom_bar_height = scale_value(self.base_bottom_bar_height, scale_factor)
        scaled_slider_width = scale_value(self.base_volume_slider_width, scale_factor)
        scaled_spacing = scale_value(self.base_layout_spacing, scale_factor)
        scaled_margin = scale_value(self.base_layout_margin, scale_factor)
        scaled_main_margin = scale_value(self.base_main_margin, scale_factor)

        # Apply to bottom bar buttons
        self.home_button_bar.setIconSize(scaled_icon_size)
        self.home_button_bar.setFixedSize(scaled_button_size)
        self.settings_button.setIconSize(scaled_icon_size)
        self.settings_button.setFixedSize(scaled_button_size)
        self.volume_icon_button.setIconSize(scaled_icon_size)
        self.volume_icon_button.setFixedSize(scaled_button_size)
        self.restart_button_bar.setIconSize(scaled_icon_size)
        self.restart_button_bar.setFixedSize(scaled_button_size)
        self.power_button.setIconSize(scaled_icon_size)
        self.power_button.setFixedSize(scaled_button_size)

        # Apply to volume slider and bottom bar itself
        self.volume_slider.setFixedWidth(scaled_slider_width)
        self.bottom_bar_widget.setFixedHeight(scaled_bottom_bar_height)

        # Apply to layouts
        self.bottom_bar_layout.setContentsMargins(scaled_margin, scaled_margin, scaled_margin, scaled_margin)
        self.bottom_bar_layout.setSpacing(scaled_spacing)

        # Main layout margins/spacing (can affect space available for children)
        self.main_layout.setContentsMargins(0,0,0,0) # Usually main layout has no margins itself
        self.main_layout.setSpacing(scale_value(5, scale_factor)) # Small spacing between stack and bottom bar

        # --- Re-apply theme/stylesheet with new scale factor ---
        # This handles font sizes and other QSS-controlled properties
        apply_theme(QApplication.instance(), self.current_theme, scale_factor)

        # --- Notify Child Screens (Optional but recommended for complex children) ---
        # Children might need to adjust internal layouts/widgets not covered by QSS
        if hasattr(self.home_screen, 'update_scaling'):
            self.home_screen.update_scaling(scale_factor, scaled_main_margin)
        if hasattr(self.radio_screen, 'update_scaling'):
            self.radio_screen.update_scaling(scale_factor, scaled_main_margin)
        if hasattr(self.obd_screen, 'update_scaling'):
            self.obd_screen.update_scaling(scale_factor, scaled_main_margin)
        if hasattr(self.settings_screen, 'update_scaling'):
            self.settings_screen.update_scaling(scale_factor, scaled_main_margin)

    def switch_theme(self, theme_name):
        if theme_name != self.current_theme:
            print(f"Switching theme to: {theme_name}")
            self.current_theme = theme_name
            # --- MODIFIED: Apply theme using current scale factor ---
            scale_factor = self.height() / self.BASE_RESOLUTION.height() if self.BASE_RESOLUTION.height() > 0 else 1.0
            apply_theme(QApplication.instance(), self.current_theme, scale_factor)
            # ---
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
        # Save the last NON-MUTED volume level before closing
        # Use self.last_volume_level which is updated during interaction
        if self.last_volume_level > 0:
             print(f"Saving last non-muted volume: {self.last_volume_level}")
             self.settings_manager.set("volume", self.last_volume_level)
        # If user manually slid to 0 and it wasn't a mute action, save 0
        elif self.volume_slider.value() == 0 and not self.is_muted:
             print("Saving volume as 0 (manually set)")
             self.settings_manager.set("volume", 0)
        # Don't save volume if muted (last_volume_level already holds the value to restore)

        print("Close event triggered. Stopping background threads...")
        # ... (rest of closeEvent: stop threads, accept event) ...
        if hasattr(self, 'radio_manager') and self.radio_manager.isRunning(): self.radio_manager.stop(); self.radio_manager.wait(1500)
        if hasattr(self, 'obd_manager') and self.obd_manager.isRunning(): self.obd_manager.stop(); self.obd_manager.wait(1500)
        if hasattr(self, 'radio_manager') and self.radio_manager.radio_type != "none": self.settings_manager.set("last_fm_station", self.radio_manager.current_frequency)
        print("Threads stopped. Exiting.")
        event.accept()


    # --- toggle_mute to use AudioManager ---
    def toggle_mute(self):
        """Toggles volume mute state using AudioManager."""
        if self.is_muted:
            # --- Unmuting ---
            restore_level = self.last_volume_level if self.last_volume_level > 0 else 50
            # Update UI first
            self.volume_slider.setValue(restore_level) # Update slider visually
            self.volume_icon_button.setIcon(self.volume_normal_icon)
            self.volume_icon_button.setChecked(False)
            self.is_muted = False
            # Tell AudioManager to unmute the system
            print(f"UI Unmuted. Restoring level to {restore_level}. Telling system...")
            self.audio_manager.set_mute(False)
            # Setting mute to false often restores previous volume, but let's set explicitly
            self.audio_manager.set_volume(restore_level) # Ensure system matches slider

        else:
            # --- Muting ---
            current_volume = self.volume_slider.value()
            # Store the current level ONLY if it's not already 0
            if current_volume > 0:
                self.last_volume_level = current_volume

            # Update UI first
            self.volume_slider.setValue(0) # Update slider visually
            self.volume_icon_button.setIcon(self.volume_muted_icon)
            self.volume_icon_button.setChecked(True)
            self.is_muted = True
            # Tell AudioManager to mute the system
            print(f"UI Muted. Last level was {self.last_volume_level}. Telling system...")
            self.audio_manager.set_mute(True)
            # No need to call set_volume(0) as set_mute(True) handles it

    # --- volume_slider_changed to use AudioManager ---
    @pyqtSlot(int)
    def volume_slider_changed(self, value):
        """Handles manual slider changes, potentially unmuting, and sets system volume."""

        # --- Update AudioManager ---
        # Set the system volume regardless of mute state change here
        # If user drags slider while muted, set_volume will apply the new level
        # and might implicitly unmute depending on ALSA behavior, which is fine.
        self.audio_manager.set_volume(value)
        print(f"Slider changed to {value}. Set system volume.")

        # --- Update UI based on slider value ---
        if self.is_muted and value > 0:
            # If the slider is moved manually WHILE muted, unmute visually
            self.is_muted = False
            self.volume_icon_button.setIcon(self.volume_normal_icon)
            self.volume_icon_button.setChecked(False)
            print("Unmuted UI due to slider movement.")
            # Update last_volume_level to the new user-set value
            self.last_volume_level = value
            # Explicitly tell system it's not muted anymore (in case set_volume didn't)
            self.audio_manager.set_mute(False)
        elif not self.is_muted and value == 0:
            # If user slides TO 0 manually (not via mute button), update icon visually
            self.volume_icon_button.setIcon(self.volume_muted_icon)
            # Don't set self.is_muted = True here, as it wasn't a mute *action*
            # Don't set self.volume_icon_button.setChecked(True) either
            print("Slider moved to 0 manually. Updated icon.")
        elif not self.is_muted and value > 0:
            # If slider moved above 0 and wasn't muted, ensure normal icon is shown
            self.volume_icon_button.setIcon(self.volume_normal_icon)
            # Store this new level as the potential restore level
            self.last_volume_level = value
  
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
