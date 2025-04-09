# gui/main_window.py

import os
import sys

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QStackedWidget, QApplication, QLabel,
                             QMessageBox, QSlider, QSpacerItem, QSizePolicy) # Added QSpacerItem, QSizePolicy
from PyQt6.QtCore import pyqtSlot, Qt, QTimer, QDateTime, QSize, QMargins
from PyQt6.QtGui import QIcon, QPixmap, QShortcut, QKeySequence

from .styling import apply_theme, scale_value

# Import backend managers
from backend.audio_manager import AudioManager
from backend.bluetooth_manager import BluetoothManager
from backend.obd_manager import OBDManager
from backend.radio_manager import RadioManager
from backend.settings_manager import SettingsManager # Import if needed directly

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
# ICON_BT_CONNECTED removed - not using icon for now
# ---

class MainWindow(QMainWindow):
    BASE_RESOLUTION = QSize(1920, 1080)

    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.audio_manager = AudioManager()
        self.bluetooth_manager = BluetoothManager()

        # Flag for initial scaling
        self._has_scaled_correctly = False

        # --- Base sizes definition ---
        self.base_top_padding = 15 # Added base padding for the very top
        self.base_icon_size = QSize(42, 42) # Larger icons for bottom bar
        # self.base_header_icon_size = QSize(28, 28) # Still needed for calculation robustness
        self.base_bottom_bar_button_size = QSize(65, 65) # Larger buttons
        self.base_bottom_bar_height = 90 # Taller bottom bar
        self.base_volume_slider_width = 220 # Wider slider
        self.base_layout_spacing = 15 # More spacing between widgets generally
        self.base_header_spacing = 20 # More spacing between header items
        self.base_layout_margin = 8 # Bottom bar internal margin
        self.base_main_margin = 15 # Child screen margin

        # --- Load Icons (No BT icon needed now) ---
        self.home_icon = QIcon(ICON_HOME)
        self.settings_icon = QIcon(ICON_SETTINGS)
        self.volume_normal_icon = QIcon(ICON_VOLUME)
        self.volume_muted_icon = QIcon(ICON_VOLUME_MUTED)
        self.restart_icon = QIcon(ICON_RESTART)
        self.power_icon = QIcon(ICON_POWER)
        # ---

        # --- Volume/Mute variables ---
        self.is_muted = False
        self.last_volume_level = 50

        # --- Window setup ---
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setWindowTitle("RPi Car Infotainment") # Default title

        # --- Theme (Set variable, apply in _apply_scaling) ---
        self.current_theme = self.settings_manager.get("theme")

        # --- Central Widget & Main Layout ---
        self.central_widget = QWidget()
        self.central_widget.setObjectName("central_widget")
        self.main_layout = QVBoxLayout(self.central_widget) # Main vertical layout
        self.setCentralWidget(self.central_widget)

        # --- ADDED: Top Padding ---
        # We'll add the actual spacer item in _apply_scaling
        # For now, just structure the layout additions correctly
        # ---

        # --- PERSISTENT HEADER BAR ---
        self.header_layout = QHBoxLayout()
        # Spacing set by scaling
        self.header_title_label = QLabel("Home")
        self.header_title_label.setObjectName("headerTitle")
        self.header_layout.addWidget(self.header_title_label)
        header_spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.header_layout.addItem(header_spacer)
        self.header_bt_status_label = QLabel("") # Combined BT Status
        self.header_bt_status_label.setObjectName("headerBtStatus")
        self.header_bt_status_label.hide()
        self.header_layout.addWidget(self.header_bt_status_label)
        self.header_clock_label = QLabel("00:00")
        self.header_clock_label.setObjectName("headerClock")
        self.header_layout.addWidget(self.header_clock_label)
        self.header_clock_timer = QTimer(self)
        self.header_clock_timer.timeout.connect(self._update_header_clock)
        self.header_clock_timer.start(10000)
        self._update_header_clock()
        # Add header layout to the main layout (AFTER potential top spacer)
        self.main_layout.addLayout(self.header_layout, 0)

        # --- Stacked Widget for Screens ---
        self.stacked_widget = QStackedWidget()
        # Connect signal to update title when screen changes
        self.stacked_widget.currentChanged.connect(self.update_header_title)
        self.main_layout.addWidget(self.stacked_widget, 1) # Takes remaining vertical space (Stretch = 1)

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
        self.bluetooth_manager.battery_updated.connect(self.update_bluetooth_statusbar_battery)
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

        # Set initial screen & Title
        self.stacked_widget.setCurrentWidget(self.home_screen)
      
        # --- Keyboard Shortcut for Quitting ---
        self.quit_shortcut = QShortcut(QKeySequence("Ctrl+Q"), self)
        self.quit_shortcut.activated.connect(self.close)

        # Apply initial scaling based on BASE size only
        # We call it once here. resizeEvent will call it again, but the factor should be 1.0
        print("Applying initial scaling based on fixed BASE_RESOLUTION.")
        


    # --- Event Handlers ---
    def resizeEvent(self, event):
        """Override resizeEvent to apply scaling ONLY after fullscreen is settled."""
        super().resizeEvent(event)
        current_size = event.size()
        print(f"DEBUG: resizeEvent triggered with Size: {current_size}")
        # Check if the size matches our target base (allowing for small variations if necessary)
        is_target_size = abs(current_size.width() - self.BASE_RESOLUTION.width()) < 5 and \
                         abs(current_size.height() - self.BASE_RESOLUTION.height()) < 5

        if is_target_size and not self._has_scaled_correctly:
            print(f"Applying initial scaling for size: {current_size}")
            self._apply_scaling()
            self.update_header_title(self.stacked_widget.currentIndex()) # Set title now
            self._has_scaled_correctly = True
        elif self._has_scaled_correctly:
             # Optional: Re-apply scaling if size changes later?
             # print(f"Subsequent resize event: {current_size}")
             # self._apply_scaling()
             pass # Usually ignore in forced fullscreen
        else:
            print(f"Ignoring resize event (Size: {current_size}, Scaled Flag: {self._has_scaled_correctly})")

    # --- Scaling ---
    def _apply_scaling(self):
        """Applies scaling to UI elements based on the fixed BASE_RESOLUTION."""
        current_height = self.height() # Get current actual height
        if self.BASE_RESOLUTION.height() <= 0: scale_factor = 1.0
        else: scale_factor = current_height / self.BASE_RESOLUTION.height() # Factor relative to actual screen height
        print(f"DEBUG: _apply_scaling factor: {scale_factor:.3f} (Height: {current_height})")

        # Calculate scaled sizes using the NEW base sizes
        scaled_top_padding = scale_value(self.base_top_padding, scale_factor) # Added
        scaled_icon_size = QSize(scale_value(self.base_icon_size.width(), scale_factor), scale_value(self.base_icon_size.height(), scale_factor))
        # scaled_header_icon_size = QSize(...) # No longer needed for calculation if icon removed
        scaled_button_size = QSize(scale_value(self.base_bottom_bar_button_size.width(), scale_factor), scale_value(self.base_bottom_bar_button_size.height(), scale_factor))
        scaled_bottom_bar_height = scale_value(self.base_bottom_bar_height, scale_factor)
        scaled_slider_width = scale_value(self.base_volume_slider_width, scale_factor)
        scaled_spacing = scale_value(self.base_layout_spacing, scale_factor)
        scaled_header_spacing = scale_value(self.base_header_spacing, scale_factor)
        scaled_margin = scale_value(self.base_layout_margin, scale_factor)
        scaled_main_margin = scale_value(self.base_main_margin, scale_factor)

        # --- Apply sizes and layouts ---
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
        # Clear layout first to potentially re-order spacing? Simpler to adjust existing.
        self.main_layout.setContentsMargins(0, 0, 0, 0) # No margin for main layout itself
        # Set spacing between header, stack, bottom bar
        self.main_layout.setSpacing(scaled_spacing)
        # Set top margin for the entire content area
        self.central_widget.setStyleSheet(f"QWidget#central_widget {{ padding-top: {scaled_top_padding}px; }}")
        # Or add a spacer item (might be less reliable with theme changes)
        # if self.main_layout.itemAt(0) is not self.header_layout: # Add spacer only once
        #      self.main_layout.insertSpacing(0, scaled_top_padding)


        self.header_layout.setSpacing(scaled_header_spacing)
        self.bottom_bar_layout.setContentsMargins(scaled_margin, scaled_margin, scaled_margin, scaled_margin)
        self.bottom_bar_layout.setSpacing(scaled_spacing)

        # --- Re-apply theme/stylesheet ---
        apply_theme(QApplication.instance(), self.current_theme, scale_factor)

        # --- Update Header Bluetooth Status ---
        self.update_bluetooth_header_status() # Update text/visibility

        # --- Notify Child Screens ---
        for screen in self.all_screens:
             if hasattr(screen, 'update_scaling'):
                  screen.update_scaling(scale_factor, scaled_main_margin)



    # --- Header Update Slots ---
    def _update_header_clock(self):
        """Updates the clock label in the header."""
        current_time = QDateTime.currentDateTime()
        time_str = current_time.toString("HH:mm")
        self.header_clock_label.setText(time_str)

    @pyqtSlot(int)
    def update_header_title(self, index):
        """Updates the header title based on the current screen index."""
        current_widget = self.stacked_widget.widget(index)
        if current_widget:
            # Try to get a title attribute, fallback to class name or default
            title = getattr(current_widget, 'screen_title', type(current_widget).__name__)
            self.header_title_label.setText(title)
            print(f"DEBUG: Header title set to: {title}")
        else:
            self.header_title_label.setText("Infotainment") # Fallback


    # --- Combined Slot for Header BT Status Update ---
    @pyqtSlot()
    @pyqtSlot(bool)
    @pyqtSlot(object)
    def update_bluetooth_header_status(self, *args):
         """Updates the combined Bluetooth status text and visibility in the header."""
         # ... (Implementation remains the same - sets text and visibility of header_bt_status_label) ...
         if not self._has_scaled_correctly: return

         connected = self.bluetooth_manager.connected_device_path is not None
         device_name = self.bluetooth_manager.connected_device_name if connected else ""
         battery_level = self.bluetooth_manager.current_battery # Store battery level

         status_text = ""
         show_label = False

         if connected:
             show_label = True
             max_len = 25 # Max length for header display
             display_name = (device_name[:max_len] + '...') if len(device_name) > max_len else device_name
             status_text = display_name # Just show the name for now
             self.header_bt_status_label.setToolTip(device_name)
             # --- Temporarily removed battery display ---
             # if battery_level is not None and isinstance(battery_level, int):
             #      status_text += f" - {battery_level}%"
             # else:
             #      status_text += " - N/A" # Indicate if battery unavailable
             # ---

         print(f"DEBUG: Updating header BT status text: '{status_text}', Visible={show_label}")
         self.header_bt_status_label.setText(status_text)
         self.header_bt_status_label.setVisible(show_label)

    # --- Status Update Slots ---
    @pyqtSlot(bool, str)
    def update_bluetooth_statusbar(self, connected, device_name):
        """Updates the Bluetooth status name and separator in the BOTTOM status bar."""
        print(f"DEBUG: Updating status bar BT name, Connected={connected}, Name='{device_name}'")
        if connected:
             max_len = 20 # Max length for status bar display
             display_name = (device_name[:max_len] + '...') if len(device_name) > max_len else device_name
             self.bt_name_label.setText(f"BT: {display_name}")
             self.bt_name_label.setToolTip(device_name) # Show full name on hover
             # Show name and separator, battery visibility handled by its own slot
             self.bt_name_label.show()
             self.bt_separator_label.show()
        else:
             # Hide all BT elements in status bar on disconnect
             self.bt_name_label.hide()
             self.bt_battery_label.hide() # Hide battery too
             self.bt_separator_label.hide()
             # Clear media info on home screen
             if hasattr(self.home_screen, 'clear_media_info'):
                 self.home_screen.clear_media_info()

    @pyqtSlot(object) # Slot receives int or None
    def update_bluetooth_statusbar_battery(self, level):
        """Updates the Bluetooth battery percentage in the BOTTOM status bar."""
        print(f"DEBUG: Updating status bar BT battery, Level={level}")
        # Show battery only if level is valid AND the name label is visible (meaning device connected)
        show_battery = level is not None and isinstance(level, int) and self.bt_name_label.isVisible()

        if show_battery:
             battery_text = f"({level}%)"
             self.bt_battery_label.setText(battery_text)
             self.bt_battery_label.show()
        else:
             self.bt_battery_label.setText("") # Clear text
             self.bt_battery_label.hide()


    # --- Header Bluetooth Update Slots ---
    @pyqtSlot(bool, str)
    def update_bluetooth_header(self, connected, device_name=""):
        """DEPRECATED (Visibility handled by update_bluetooth_header_status). Kept for signal connection safety."""
        # This method is now effectively redundant because update_bluetooth_header_status
        # handles both the text AND visibility of the header_bt_status_label.
        # We keep it connected to connection_changed just in case, but it doesn't
        # need to do anything anymore regarding the icon.
        print(f"DEBUG: update_bluetooth_header called (now redundant), Connected={connected}")
        # --- REMOVE/COMMENT OUT ---
        # if not self._has_scaled_correctly: return
        # show_icon = connected and hasattr(self, 'bt_connected_icon') and not self.bt_connected_icon.isNull()
        # if scaled_size is None:
        #     scale_factor = self.height() / self.BASE_RESOLUTION.height() if self.BASE_RESOLUTION.height() > 0 else 1.0
        #     scaled_size = QSize(
        #         scale_value(self.base_header_icon_size.width(), scale_factor), # <--- Error originated here
        #         scale_value(self.base_header_icon_size.height(), scale_factor)
        #     )
        # print(f"DEBUG: Icon Target Size: {scaled_size}")
        # pixmap = self.bt_connected_icon.pixmap(scaled_size) if show_icon else QPixmap()
        # print(f"DEBUG: Header Pixmap isNull: {pixmap.isNull()}")
        # for screen in self.all_screens:
        #     if hasattr(screen, 'bt_icon_label'):
        #         if show_icon and not pixmap.isNull():
        #             screen.bt_icon_label.setPixmap(pixmap)
        #             screen.bt_icon_label.setFixedSize(scaled_size)
        #             screen.bt_icon_label.show()
        #         else:
        #             screen.bt_icon_label.hide()
        #             screen.bt_icon_label.clear()
        # --- END REMOVAL ---
        pass # Method does nothing now

                  

    @pyqtSlot(object)
    def update_bluetooth_header_battery(self, level):
        """Updates the Bluetooth battery text in ALL screen headers."""
        # No need to check _has_scaled_correctly anymore
        manager_connected = hasattr(self, 'bluetooth_manager') and self.bluetooth_manager.connected_device_path is not None
        print(f"DEBUG: Updating header BT battery, Level={level}, Manager Connected={manager_connected}")
        show_battery = level is not None and isinstance(level, int) and manager_connected
        battery_text = f"{level}%" if show_battery else ""
        for screen in self.all_screens:
            if hasattr(screen, 'bt_battery_label'):
                screen.bt_battery_label.setText(battery_text)
                screen.bt_battery_label.setVisible(show_battery)

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
