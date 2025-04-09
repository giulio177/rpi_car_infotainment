# gui/main_window.py

import os
import sys

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QStackedWidget, QApplication, QLabel,
                             QMessageBox, QSlider)
from PyQt6.QtCore import pyqtSlot, Qt, QTimer, QDateTime, QSize, QMargins
from PyQt6.QtGui import QIcon, QPixmap, QShortcut, QKeySequence

from .styling import apply_theme, scale_value

# Import backend managers
from backend.audio_manager import AudioManager
from backend.bluetooth_manager import BluetoothManager
from backend.obd_manager import OBDManager
from backend.radio_manager import RadioManager
from backend.settings_manager import SettingsManager

# Import screens
from .home_screen import HomeScreen
from .radio_screen import RadioScreen
from .obd_screen import OBDScreen
from .setting_screen import SettingsScreen

# --- Icon definitions ---
ICON_PATH = "assets/icons/"
ICON_HOME = os.path.join(ICON_PATH, "home.png")
ICON_SETTINGS = os.path.join(ICON_PATH, "settings.png")
ICON_VOLUME = os.path.join(ICON_PATH, "volume.png")
ICON_VOLUME_MUTED = os.path.join(ICON_PATH, "volume_muted.png")
ICON_RESTART = os.path.join(ICON_PATH, "restart.png")
ICON_POWER = os.path.join(ICON_PATH, "power.png")
ICON_BT_CONNECTED = os.path.join(ICON_PATH, "bluetooth_connected.png")
# ---

class MainWindow(QMainWindow):
    BASE_RESOLUTION = QSize(1920, 1080)

    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.audio_manager = AudioManager()
        self.bluetooth_manager = BluetoothManager()

        # --- Flag to prevent scaling before fullscreen is settled ---
        self._has_scaled_correctly = False # Renamed for clarity

        # --- Base sizes definition ---
        self.base_icon_size = QSize(38, 38)
        self.base_header_icon_size = QSize(28, 28) # Base size for 1080p
        self.base_bottom_bar_button_size = QSize(55, 55)
        self.base_bottom_bar_height = 80
        self.base_volume_slider_width = 180
        self.base_layout_spacing = 12
        self.base_layout_margin = 6
        self.base_main_margin = 12

        # --- Load Icons ---
        self.home_icon = QIcon(ICON_HOME)
        self.settings_icon = QIcon(ICON_SETTINGS)
        self.volume_normal_icon = QIcon(ICON_VOLUME)
        self.volume_muted_icon = QIcon(ICON_VOLUME_MUTED)
        self.restart_icon = QIcon(ICON_RESTART)
        self.power_icon = QIcon(ICON_POWER)
        self.bt_connected_icon = QIcon(ICON_BT_CONNECTED)
        # --- ADDED: Explicit check for BT icon ---
        if self.bt_connected_icon.isNull():
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print(f"CRITICAL WARNING: Bluetooth icon failed to load from: {ICON_BT_CONNECTED}")
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        # ---

        # --- Volume/Mute variables ---
        self.is_muted = False
        self.last_volume_level = 50

        # --- Window setup ---
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setWindowTitle("RPi Car Infotainment")

        # --- Theme (Set variable, apply in _apply_scaling) ---
        self.current_theme = self.settings_manager.get("theme")

        # --- Central Widget Area ---
        self.central_widget = QWidget()
        self.central_widget.setObjectName("central_widget")
        self.main_layout = QVBoxLayout(self.central_widget)
        self.setCentralWidget(self.central_widget)

        # --- Stacked Widget for Screens ---
        self.stacked_widget = QStackedWidget()
        self.main_layout.addWidget(self.stacked_widget, 1)

        # --- Status Labels Setup (Bottom Bar) ---
        self.obd_status_label = QLabel("OBD: Disconnected")
        self.obd_status_label.setObjectName("statusBarObdLabel")
        self.radio_status_label = QLabel("Radio: Idle")
        self.radio_status_label.setObjectName("statusBarRadioLabel")
        self.separator_label = QLabel("|")
        self.separator_label.setObjectName("statusBarSeparator")
        self.bt_name_label = QLabel("BT: -")
        self.bt_name_label.setObjectName("statusBarBtNameLabel")
        self.bt_battery_label = QLabel("")
        self.bt_battery_label.setObjectName("statusBarBtBatteryLabel")
        self.bt_separator_label = QLabel("|")
        self.bt_separator_label.setObjectName("statusBarSeparator")
        self.bt_name_label.hide()
        self.bt_battery_label.hide()
        self.bt_separator_label.hide()

        # --- PERSISTENT BOTTOM BAR ---
        self.bottom_bar_widget = QWidget()
        self.bottom_bar_widget.setObjectName("persistentBottomBar")
        self.bottom_bar_layout = QHBoxLayout(self.bottom_bar_widget)

        # --- Create bottom bar buttons ---
        self.home_button_bar = QPushButton()
        self.home_button_bar.setIcon(self.home_icon)
        self.home_button_bar.setObjectName("homeNavButton")
        self.home_button_bar.setToolTip("Go to Home Screen")
        self.home_button_bar.clicked.connect(self.go_to_home)

        self.settings_button = QPushButton()
        self.settings_button.setIcon(self.settings_icon)
        self.settings_button.setObjectName("settingsNavButton")
        self.settings_button.setToolTip("Open Settings")
        self.settings_button.clicked.connect(self.go_to_settings)

        self.volume_icon_button = QPushButton()
        self.volume_icon_button.setObjectName("volumeIcon")
        self.volume_icon_button.setToolTip("Mute / Unmute Volume")
        self.volume_icon_button.setCheckable(True)
        self.volume_icon_button.clicked.connect(self.toggle_mute)

        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.valueChanged.connect(self.volume_slider_changed)

        self.restart_button_bar = QPushButton()
        self.restart_button_bar.setIcon(self.restart_icon)
        self.restart_button_bar.setObjectName("restartNavButton")
        self.restart_button_bar.setToolTip("Restart Application")
        self.restart_button_bar.clicked.connect(self.restart_application)

        self.power_button = QPushButton()
        self.power_button.setIcon(self.power_icon)
        self.power_button.setObjectName("powerNavButton")
        self.power_button.setToolTip("Exit Application (Ctrl+Q)")
        self.power_button.clicked.connect(self.close)

        # --- Add widgets to bottom bar layout ---
        self.bottom_bar_layout.addWidget(self.home_button_bar)
        self.bottom_bar_layout.addWidget(self.settings_button)
        self.bottom_bar_layout.addStretch(1)
        self.bottom_bar_layout.addWidget(self.obd_status_label)
        self.bottom_bar_layout.addWidget(self.separator_label)
        self.bottom_bar_layout.addWidget(self.radio_status_label)
        self.bottom_bar_layout.addWidget(self.bt_separator_label)
        self.bottom_bar_layout.addWidget(self.bt_name_label)
        self.bottom_bar_layout.addWidget(self.bt_battery_label)
        self.bottom_bar_layout.addStretch(2)
        self.bottom_bar_layout.addWidget(self.volume_icon_button)
        self.bottom_bar_layout.addWidget(self.volume_slider)
        self.bottom_bar_layout.addStretch(2)
        self.bottom_bar_layout.addWidget(self.restart_button_bar)
        self.bottom_bar_layout.addWidget(self.power_button)

        # Add bottom bar widget to main layout
        self.main_layout.addWidget(self.bottom_bar_widget) # Stretch factor 0

        # --- Initialize Backend Managers ---
        self.obd_manager = OBDManager(
            port=self.settings_manager.get("obd_port"),
            baudrate=self.settings_manager.get("obd_baudrate")
        )
        self.radio_manager = RadioManager(
             radio_type=self.settings_manager.get("radio_type"),
             i2c_address=self.settings_manager.get("radio_i2c_address"),
             initial_freq=self.settings_manager.get("last_fm_station")
        )
        # BluetoothManager already instantiated

        # --- Initialize Screens ---
        self.home_screen = HomeScreen(parent=self)
        self.radio_screen = RadioScreen(self.radio_manager, parent=self)
        self.obd_screen = OBDScreen(parent=self)
        self.settings_screen = SettingsScreen(self.settings_manager, self)
        self.all_screens = [self.home_screen, self.radio_screen, self.obd_screen, self.settings_screen]

        # --- Add Screens to Stack ---
        for screen in self.all_screens:
            self.stacked_widget.addWidget(screen)

        # --- Connect Backend Signals ---
        self.obd_manager.connection_status.connect(self.update_obd_status)
        self.obd_manager.data_updated.connect(self.obd_screen.update_data)
        self.radio_manager.radio_status.connect(self.update_radio_status)
        self.radio_manager.frequency_updated.connect(self.radio_screen.update_frequency)
        self.radio_manager.signal_strength.connect(self.radio_screen.update_signal_strength)
        self.bluetooth_manager.connection_changed.connect(self.update_bluetooth_statusbar)
        self.bluetooth_manager.battery_updated.connect(self.update_bluetooth_header_battery)
        self.bluetooth_manager.connection_changed.connect(self.update_bluetooth_header)
        self.bluetooth_manager.battery_updated.connect(self.update_bluetooth_header_battery)
        self.bluetooth_manager.media_properties_changed.connect(self.home_screen.update_media_info)
        self.bluetooth_manager.playback_status_changed.connect(self.home_screen.update_playback_status)

        # --- Initialize Volume/Mute States ---
        initial_system_mute = self.audio_manager.get_mute_status()
        self.is_muted = initial_system_mute if initial_system_mute is not None else False
        self.last_volume_level = self.settings_manager.get("volume") or 50
        if not self.is_muted and self.last_volume_level == 0: self.last_volume_level = 50
        initial_icon = self.volume_muted_icon if self.is_muted else self.volume_normal_icon
        self.volume_icon_button.setIcon(initial_icon)
        self.volume_icon_button.setChecked(self.is_muted)
        initial_slider_value = self.audio_manager.get_volume()
        if initial_slider_value is None: initial_slider_value = 0 if self.is_muted else self.last_volume_level
        self.volume_slider.setValue(initial_slider_value)
        if not self.is_muted: self.audio_manager.set_volume(initial_slider_value)
        else: self.audio_manager.set_mute(True)

        # --- Start Backend Threads ---
        self.obd_manager.start()
        if self.radio_manager.radio_type != "none": self.radio_manager.start()
        self.bluetooth_manager.start()

        # Set initial screen
        self.stacked_widget.setCurrentWidget(self.home_screen)

        # --- Keyboard Shortcut for Quitting ---
        self.quit_shortcut = QShortcut(QKeySequence("Ctrl+Q"), self)
        self.quit_shortcut.activated.connect(self.close)

        # Initial scaling/theme applied by first resizeEvent *with correct size*


    # --- MODIFIED: resizeEvent ---
    def resizeEvent(self, event):
        """Override resizeEvent to apply scaling ONLY after fullscreen is settled."""
        super().resizeEvent(event)
        current_size = event.size()
        print(f"DEBUG: resizeEvent triggered with Size: {current_size}")

        # Check if we have a reasonable size (likely fullscreen) AND haven't scaled yet
        # Use a threshold slightly smaller than target to account for minor variations
        is_fullscreen_approx = current_size.width() > 1000 and current_size.height() > 500

        if is_fullscreen_approx and not self._has_scaled_correctly:
            print(f"Applying initial scaling for size: {current_size}")
            self._apply_scaling()
            self._has_scaled_correctly = True # Mark that initial scaling is done
        elif self._has_scaled_correctly:
            # Handle subsequent resizes if needed (e.g., if manually resized later, though unlikely in kiosk mode)
            # This might be where the resize back to 767x415 was happening if something triggered it
            # For now, only rescale if size significantly changes AFTER initial scaling
            # print(f"Subsequent resize event: {current_size}")
            # self._apply_scaling() # Uncomment this line if you WANT rescaling on later size changes
            pass
        else:
            # Ignore resize events with small initial sizes before fullscreen
            print(f"Ignoring resize event (Size: {current_size}, Scaled Flag: {self._has_scaled_correctly})")


    # REMOVED showEvent - Relying on resizeEvent check


    def _apply_scaling(self):
        """Applies scaling to UI elements based on current window height vs BASE_RESOLUTION."""
        current_height = self.height()
        if self.BASE_RESOLUTION.height() <= 0 or current_height <= 0: scale_factor = 1.0
        else: scale_factor = current_height / self.BASE_RESOLUTION.height()
        print(f"DEBUG: _apply_scaling factor: {scale_factor:.3f} (Height: {current_height})")

        # Calculate scaled sizes
        scaled_icon_size = QSize(scale_value(self.base_icon_size.width(), scale_factor), scale_value(self.base_icon_size.height(), scale_factor))
        scaled_header_icon_size = QSize(scale_value(self.base_header_icon_size.width(), scale_factor), scale_value(self.base_header_icon_size.height(), scale_factor))
        scaled_button_size = QSize(scale_value(self.base_bottom_bar_button_size.width(), scale_factor), scale_value(self.base_bottom_bar_button_size.height(), scale_factor))
        scaled_bottom_bar_height = scale_value(self.base_bottom_bar_height, scale_factor)
        scaled_slider_width = scale_value(self.base_volume_slider_width, scale_factor)
        scaled_spacing = scale_value(self.base_layout_spacing, scale_factor)
        scaled_margin = scale_value(self.base_layout_margin, scale_factor)
        scaled_main_margin = scale_value(self.base_main_margin, scale_factor)

        # Apply to bottom bar elements
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
        self.volume_slider.setFixedWidth(scaled_slider_width)
        self.bottom_bar_widget.setFixedHeight(scaled_bottom_bar_height)

        # Apply to layouts
        self.bottom_bar_layout.setContentsMargins(scaled_margin, scaled_margin, scaled_margin, scaled_margin)
        self.bottom_bar_layout.setSpacing(scaled_spacing)
        self.main_layout.setContentsMargins(0,0,0,0)
        self.main_layout.setSpacing(scale_value(5, scale_factor))

        # Re-apply theme/stylesheet
        apply_theme(QApplication.instance(), self.current_theme, scale_factor)

        # Update Header Icons (Force update with potentially new size)
        self.update_bluetooth_header(self.bluetooth_manager.connected_device_path is not None, "")
        self.update_bluetooth_header_battery(self.bluetooth_manager.current_battery)

        # Notify Child Screens
        for screen in self.all_screens:
             if hasattr(screen, 'update_scaling'):
                  screen.update_scaling(scale_factor, scaled_main_margin)


    # --- Status Update Slots ---
    @pyqtSlot(bool, str)
    def update_bluetooth_statusbar(self, connected, device_name):
        # ... (Implementation remains the same) ...
        if connected:
             max_len = 20
             display_name = (device_name[:max_len] + '...') if len(device_name) > max_len else device_name
             self.bt_name_label.setText(f"BT: {display_name}")
             self.bt_name_label.setToolTip(device_name)
             self.bt_name_label.show()
             self.bt_separator_label.show()
        else:
             self.bt_name_label.hide()
             self.bt_separator_label.hide()
             if hasattr(self.home_screen, 'clear_media_info'):
                 self.home_screen.clear_media_info()

    @pyqtSlot(object)
    def update_bluetooth_header_battery(self, level):
        # ... (Implementation remains the same) ...
         if level is not None and isinstance(level, int) and self.bt_name_label.isVisible():
             self.bt_battery_label.setText(f"({level}%)")
             self.bt_battery_label.show()
         else:
             self.bt_battery_label.hide()


    # --- Header Bluetooth Update Slots ---
    @pyqtSlot(bool, str)
    def update_bluetooth_header(self, connected, device_name=""):
        """Updates the Bluetooth icon visibility in ALL screen headers."""
        # Only proceed if scaling has been done (widget sizes are valid)
        if not self._has_scaled_correctly: return

        print(f"DEBUG: Updating header BT icon, Connected={connected}")
        show_icon = connected and not self.bt_connected_icon.isNull() # Check icon loaded ok

        # Calculate scaled size dynamically
        scale_factor = self.height() / self.BASE_RESOLUTION.height() if self.BASE_RESOLUTION.height() > 0 else 1.0
        scaled_size = QSize(
            scale_value(self.base_header_icon_size.width(), scale_factor),
            scale_value(self.base_header_icon_size.height(), scale_factor)
        )
        print(f"DEBUG: Icon Scaled Size: {scaled_size}") # Debug

        pixmap = self.bt_connected_icon.pixmap(scaled_size) if show_icon else QPixmap()
        print(f"DEBUG: Pixmap isNull: {pixmap.isNull()}") # Debug

        for screen in self.all_screens:
            if hasattr(screen, 'bt_icon_label'):
                if show_icon:
                    screen.bt_icon_label.setPixmap(pixmap)
                    screen.bt_icon_label.setFixedSize(scaled_size) # Crucial: Set fixed size
                    print(f"DEBUG: Showing BT icon on {type(screen).__name__}") # Debug
                    screen.bt_icon_label.show()
                else:
                    print(f"DEBUG: Hiding BT icon on {type(screen).__name__}") # Debug
                    screen.bt_icon_label.hide()
                    screen.bt_icon_label.clear()


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
        """Switches theme and re-applies scaling/styling."""
        if theme_name != self.current_theme:
            print(f"Switching theme to: {theme_name}")
            self.current_theme = theme_name
            # Re-apply scaling which now includes re-applying the theme with the correct factor
            self._apply_scaling()
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
        """Handles window close events (triggered by Alt+F4, Ctrl+Q, Power button)."""
        # ... (Save volume settings logic) ...
        if self.last_volume_level > 0: # Save last non-muted
             print(f"Saving last non-muted volume: {self.last_volume_level}")
             self.settings_manager.set("volume", self.last_volume_level)
        elif self.volume_slider.value() == 0 and not self.is_muted: # Save 0 if manually set
             print("Saving volume as 0 (manually set)")
             self.settings_manager.set("volume", 0)

        print("Close event triggered. Stopping background threads...")
        # Stop threads gracefully
        if hasattr(self, 'radio_manager') and self.radio_manager.isRunning(): self.radio_manager.stop(); self.radio_manager.wait(1500)
        if hasattr(self, 'obd_manager') and self.obd_manager.isRunning(): self.obd_manager.stop(); self.obd_manager.wait(1500)
        if hasattr(self, 'bluetooth_manager') and self.bluetooth_manager.isRunning():
            print("Stopping Bluetooth Manager...")
            self.bluetooth_manager.stop()
            self.bluetooth_manager.wait(1500)
            print("Bluetooth Manager stopped.")
        # Save other settings
        if hasattr(self, 'radio_manager') and self.radio_manager.radio_type != "none": self.settings_manager.set("last_fm_station", self.radio_manager.current_frequency)
        print("Threads stopped. Exiting.")
        event.accept() # Accept the close event


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
