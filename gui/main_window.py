# gui/main_window.py

import base64
import os
import re
import sys
import subprocess

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QStackedWidget,
    QApplication,
    QLabel,
    QMessageBox,
    QSlider,
    QSpacerItem,
    QSizePolicy,
)  # Added QSpacerItem, QSizePolicy
from PyQt6.QtCore import pyqtSlot, Qt, QTimer, QDateTime, QSize, QBuffer, QIODevice
from PyQt6.QtGui import QIcon, QShortcut, QKeySequence

from .styling import apply_theme, scale_value

_SkipSetting = object()

# Import backend managers
from backend.audio_manager import AudioManager
from backend.bluetooth_manager import BluetoothManager
from backend.obd_manager import OBDManager
from backend.radio_manager import RadioManager
from backend.airplay_manager import AirPlayManager
from backend.wifi_manager import WiFiManager

# Import screens
from .home_screen import HomeScreen
from .radio_screen import RadioScreen
from .obd_screen import OBDScreen
from .setting_screen import SettingsScreen
from .music_player_screen import MusicPlayerScreen
from .airplay_screen import AirPlayScreen
from .logs_screen import LogsScreen

# Import network dialogs
from .network_dialogs import BluetoothDialog, WiFiDialog

try:
    from .html_renderer import HtmlView
except ImportError:  # pragma: no cover - fallback when WebEngine is missing
    HtmlView = None

# --- Icon definitions ---
ICON_PATH = "assets/icons/"
ICON_HOME = os.path.join(ICON_PATH, "home.png")
ICON_SETTINGS = os.path.join(ICON_PATH, "settings.png")
ICON_VOLUME = os.path.join(ICON_PATH, "volume.png")
ICON_VOLUME_MUTED = os.path.join(ICON_PATH, "volume_muted.png")
ICON_RESTART = os.path.join(ICON_PATH, "restart.png")
ICON_POWER = os.path.join(ICON_PATH, "power.png")
ICON_BLUETOOTH = os.path.join(ICON_PATH, "bluetooth.png")
ICON_WIFI = os.path.join(ICON_PATH, "wifi.png")
# ---


class MainWindow(QMainWindow):
    BASE_RESOLUTION = QSize(1024, 600)

    def __init__(self, settings_manager, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.audio_manager = AudioManager()
        self.bluetooth_manager = BluetoothManager()
        self.wifi_manager = WiFiManager()
        self.airplay_manager = AirPlayManager()
        

        # Flag for initial scaling
        self._has_scaled_correctly = False

        # --- Base sizes definition ---
        self.base_top_padding = 120  # Reduced padding for the very top for 1024x600
        self.base_icon_size = QSize(32, 32)  # Smaller icons for bottom bar for 1024x600
        # self.base_header_icon_size = QSize(22, 22) # Still needed for calculation robustness
        self.base_bottom_bar_button_size = QSize(50, 50)  # Smaller buttons for 1024x600
        self.base_bottom_bar_height = 70  # Shorter bottom bar for 1024x600
        self.base_volume_slider_width = 180  # Narrower slider for 1024x600
        self.base_layout_spacing = 10  # Less spacing between widgets for 1024x600
        self.base_header_spacing = 15  # Less spacing between header items for 1024x600
        self.base_layout_margin = 6  # Smaller bottom bar internal margin for 1024x600
        self.base_main_margin = 10  # Smaller child screen margin for 1024x600

        # --- Load Icons ---
        self.home_icon = QIcon(ICON_HOME)
        self.settings_icon = QIcon(ICON_SETTINGS)
        self.volume_normal_icon = QIcon(ICON_VOLUME)
        self.volume_muted_icon = QIcon(ICON_VOLUME_MUTED)
        self.restart_icon = QIcon(ICON_RESTART)
        self.power_icon = QIcon(ICON_POWER)
        self.bluetooth_icon = QIcon(ICON_BLUETOOTH)
        self.wifi_icon = QIcon(ICON_WIFI)
        # ---

        # --- Volume/Mute variables ---
        self.is_muted = False
        self.last_volume_level = 50

        # --- Window setup ---
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setWindowTitle("RPi Car Infotainment")  # Default title

        # --- Theme (Set variable, apply in _apply_scaling) ---
        self.current_theme = self.settings_manager.get("theme")

        requested_mode = (
            os.environ.get("INFOTAINMENT_UI_MODE")
            or self.settings_manager.get("ui_render_mode")
            or "native"
        )
        if isinstance(requested_mode, str):
            requested_mode = requested_mode.lower()
        else:
            requested_mode = "native"
        self.use_html_ui = requested_mode == "html" and HtmlView is not None
        self.html_view = None
        self._html_ready = False
        self.screen_registry = {}
        self.active_screen_id = "home"
        self.html_state = {
            "volume": {"level": 0, "muted": False},
            "bluetooth": {"connected": False, "device": None, "battery": None},
            "radio": {"status": "Disabled"},
            "obd": {"status": "Disabled"},
            "media": {
                "source": None,
                "title": None,
                "artist": None,
                "album": None,
                "position": 0,
                "duration": 0,
                "status": "stopped",
                "art": None,
            },
            "settings": {},
        }
        self.html_state["settings"] = self._collect_settings_summary()
        if requested_mode == "html" and HtmlView is None:
            print(
                "HTML UI requested but PyQt6-WebEngine is missing. Falling back to native widgets."
            )
            self.use_html_ui = False

        # --- Central Widget & Main Layout ---
        self.central_widget = QWidget()
        self.central_widget.setObjectName("central_widget")
        self.main_layout = QVBoxLayout(self.central_widget)  # Main vertical layout
        self.setCentralWidget(self.central_widget)

        # --- ADDED: Top Padding ---
        # We'll add the actual spacer item in _apply_scaling
        # For now, just structure the layout additions correctly
        # ---

        # 🔽 Azzeriamo margini e spazi per avere UI edge-to-edge
        self.central_widget.setContentsMargins(0, 0, 0, 0)
        self.central_widget.setStyleSheet("margin:0; padding:0; border:0;")

        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)


        # --- PERSISTENT HEADER BAR ---
        self.header_widget = QWidget()
        self.header_widget.setObjectName("persistentHeaderBar")
        self.header_layout = QHBoxLayout(self.header_widget)
        self.header_layout.setContentsMargins(0, 0, 0, 0)
        # Spacing set by scaling
        self.header_title_label = QLabel("Home")
        self.header_title_label.setObjectName("headerTitle")
        self.header_layout.addWidget(self.header_title_label)

        # Add first spacer to push quit button to middle
        header_spacer1 = QSpacerItem(
            40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        self.header_layout.addItem(header_spacer1)

        # Add quit button in the middle
        self.header_quit_button = QPushButton()
        self.header_quit_button.setIcon(self.power_icon)
        self.header_quit_button.setObjectName("appActionButton")
        self.header_quit_button.setToolTip("Exit Application")
        self.header_quit_button.clicked.connect(self.close)
        self.header_layout.addWidget(self.header_quit_button)

        # Add second spacer to push clock to right
        header_spacer2 = QSpacerItem(
            40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        self.header_layout.addItem(header_spacer2)
        # Combined BT Status
        self.header_bt_status_label = QLabel("")
        self.header_bt_status_label.setObjectName("headerBtStatus")
        self.header_bt_status_label.hide()
        self.header_layout.addWidget(self.header_bt_status_label)
        # Clock
        self.header_clock_label = QLabel("00:00")
        self.header_clock_label.setObjectName("headerClock")
        self.header_layout.addWidget(self.header_clock_label)
        self.header_clock_timer = QTimer(self)
        self.header_clock_timer.timeout.connect(self._update_header_clock)
        self.header_clock_timer.start(10000)
        self._update_header_clock()
        # Add header layout to the main layout (AFTER potential top spacer)
        self.main_layout.addWidget(self.header_widget, 0)

        # --- Stacked Widget for Screens ---
        self.stacked_widget = QStackedWidget()
        # Connect signal to update title when screen changes
        self.stacked_widget.currentChanged.connect(self.update_header_title)
        if self.use_html_ui:
            html_path = os.path.join(
                os.path.dirname(__file__),
                "html",
                "index.html",
            )
            self.html_view = HtmlView(html_path)
            self.html_view.event_received.connect(self.handle_html_event)
            self.html_view.view.loadFinished.connect(self._on_html_loaded)
            self.main_layout.addWidget(self.html_view, 1)
        else:
            self.main_layout.addWidget(
                self.stacked_widget, 1
            )  # Takes remaining vertical space (Stretch = 1)

        # --- Status Labels Setup (Bottom Bar) - REMOVED ---
        # Status labels removed to clean up bottom bar

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
        self.volume_slider.setObjectName("volumeSlider")
        self.volume_slider.setRange(0, 100)
        self.volume_slider.valueChanged.connect(self.volume_slider_changed)

        self.restart_button_bar = QPushButton()
        self.restart_button_bar.setIcon(self.restart_icon)
        self.restart_button_bar.setObjectName("appActionButton")
        self.restart_button_bar.setToolTip("Restart Application")
        self.restart_button_bar.clicked.connect(self.restart_application)

        self.power_button = QPushButton()
        self.power_button.setIcon(self.restart_icon)
        self.power_button.setObjectName("systemActionButton")
        self.power_button.setToolTip("Reboot Raspberry Pi")
        self.power_button.clicked.connect(self.reboot_system)

        # --- Network Control Buttons ---
        self.bluetooth_button = QPushButton()
        self.bluetooth_button.setIcon(self.bluetooth_icon)
        self.bluetooth_button.setObjectName("bluetoothNavButton")
        self.bluetooth_button.setToolTip("Bluetooth Settings")
        self.bluetooth_button.clicked.connect(self.open_bluetooth_dialog)

        self.wifi_button = QPushButton()
        self.wifi_button.setIcon(self.wifi_icon)
        self.wifi_button.setObjectName("wifiNavButton")
        self.wifi_button.setToolTip("WiFi Settings")
        self.wifi_button.clicked.connect(self.open_wifi_dialog)

        # --- Add widgets to bottom bar layout ---
        self.bottom_bar_layout.addWidget(self.home_button_bar)
        self.bottom_bar_layout.addWidget(self.settings_button)
        self.bottom_bar_layout.addStretch(1)
        # Status labels removed for cleaner bottom bar
        self.bottom_bar_layout.addWidget(self.volume_icon_button)
        self.bottom_bar_layout.addWidget(self.volume_slider)
        self.bottom_bar_layout.addWidget(self.bluetooth_button)
        self.bottom_bar_layout.addWidget(self.wifi_button)
        self.bottom_bar_layout.addStretch(1)
        self.bottom_bar_layout.addWidget(self.restart_button_bar)
        self.bottom_bar_layout.addWidget(self.power_button)

        # Add bottom bar widget to main layout
        self.main_layout.addWidget(self.bottom_bar_widget)  # Stretch factor 0

        if self.use_html_ui and self.header_widget is not None:
            self.header_widget.setVisible(False)
            self.bottom_bar_widget.setVisible(False)

        # --- Initialize Backend Managers ---
        self.obd_manager = OBDManager(
            port=self.settings_manager.get("obd_port"),
            baudrate=self.settings_manager.get("obd_baudrate"),
        )
        self.radio_manager = RadioManager(
            radio_type=self.settings_manager.get("radio_type"),
            i2c_address=self.settings_manager.get("radio_i2c_address"),
            initial_freq=self.settings_manager.get("last_fm_station"),
        )
        # BluetoothManager already instantiated

        # --- Initialize Screens ---
        self.home_screen = HomeScreen(parent=self)
        self.radio_screen = RadioScreen(self.radio_manager, parent=self)
        self.obd_screen = OBDScreen(parent=self)
        self.settings_screen = SettingsScreen(self.settings_manager, self)
        self.music_player_screen = MusicPlayerScreen(parent=self)
        self.airplay_screen = AirPlayScreen(self.airplay_manager, parent=self)
        self.logs_screen = LogsScreen(parent=self)
        self.all_screens = [
            self.home_screen,
            self.radio_screen,
            self.obd_screen,
            self.settings_screen,
            self.music_player_screen,
            self.airplay_screen,
            self.logs_screen
        ]

        # --- Add Screens to Stack ---
        for screen in self.all_screens:
            self._register_screen(screen)
            self.stacked_widget.addWidget(screen)

        # --- Connect Backend Signals ---
        self.obd_manager.connection_status.connect(self.update_obd_status)
        self.obd_manager.data_updated.connect(self.obd_screen.update_data)
        self.radio_manager.radio_status.connect(self.update_radio_status)
        self.radio_manager.frequency_updated.connect(self.radio_screen.update_frequency)
        self.radio_manager.signal_strength.connect(
            self.radio_screen.update_signal_strength
        )
        self.bluetooth_manager.connection_changed.connect(
            self.update_bluetooth_statusbar
        )
        self.bluetooth_manager.connection_changed.connect(
            self.update_bluetooth_header_status
        )
        self.bluetooth_manager.battery_updated.connect(
            self.update_bluetooth_header_status
        )
        self.bluetooth_manager.media_properties_changed.connect(
            self.home_screen.update_media_info
        )
        self.bluetooth_manager.playback_status_changed.connect(
            self.home_screen.update_playback_status
        )
        self.bluetooth_manager.media_properties_changed.connect(
            self._handle_media_properties_changed
        )
        self.bluetooth_manager.playback_status_changed.connect(
            self._handle_playback_status_changed
        )
        # Connect signals to music player screen
        self.bluetooth_manager.media_properties_changed.connect(
            self.music_player_screen.update_media_info
        )
        self.bluetooth_manager.playback_status_changed.connect(
            self.music_player_screen.update_playback_status
        )

        # Connect local playback signals from music player to home screen
        self.music_player_screen.local_playback_started.connect(
            self.home_screen.update_media_info
        )
        self.music_player_screen.local_playback_status_changed.connect(
            self.home_screen.update_playback_status
        )
        self.music_player_screen.local_playback_position_changed.connect(
            self.home_screen.update_position
        )

        self.music_player_screen.album_art_updated.connect(
            self.home_screen.update_album_art
        )
        self.music_player_screen.local_playback_started.connect(
            self._handle_local_media_started
        )
        self.music_player_screen.local_playback_status_changed.connect(
            self._handle_local_playback_status
        )
        self.music_player_screen.local_playback_position_changed.connect(
            self._handle_local_playback_position
        )
        self.music_player_screen.album_art_updated.connect(
            self._handle_local_album_art
        )

        # Connect AirPlay stream signals
        if hasattr(self.airplay_manager, 'show_stream_widget'):
            self.airplay_manager.show_stream_widget.connect(self.on_airplay_stream_widget)

        # --- Initialize Volume/Mute States ---
        initial_system_mute = self.audio_manager.get_mute_status()
        self.is_muted = (
            initial_system_mute if initial_system_mute is not None else False
        )
        self.last_volume_level = self.settings_manager.get("volume") or 50
        if not self.is_muted and self.last_volume_level == 0:
            self.last_volume_level = 50
        initial_icon = (
            self.volume_muted_icon if self.is_muted else self.volume_normal_icon
        )
        self.volume_icon_button.setIcon(initial_icon)
        self.volume_icon_button.setChecked(self.is_muted)
        initial_slider_value = self.audio_manager.get_volume()
        if initial_slider_value is None:
            initial_slider_value = 0 if self.is_muted else self.last_volume_level
        self.volume_slider.setValue(initial_slider_value)
        if not self.is_muted:
            self.audio_manager.set_volume(initial_slider_value)
        else:
            self.audio_manager.set_mute(True)
        self.html_state["volume"]["level"] = initial_slider_value
        self.html_state["volume"]["muted"] = self.is_muted

        # --- Start Backend Threads ---
        if self.settings_manager.get("obd_enabled"):
            print("Starting OBD Manager (enabled in settings)...")
            self.obd_manager.start()
        else:
            self.update_obd_status(False, "Disabled")  # Initial status update

        if (
            self.settings_manager.get("radio_enabled")
            and self.radio_manager.radio_type != "none"
        ):
            print("Starting Radio Manager (enabled in settings)...")
            self.radio_manager.start()
        else:
            radio_status = (
                "Disabled"
                if not self.settings_manager.get("radio_enabled")
                else "No HW"
            )
            self.update_radio_status(radio_status)  # Initial status update

        print("Starting Bluetooth Manager...")  # Always start BT manager
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
    def _register_screen(self, screen_widget):
        title = getattr(screen_widget, "screen_title", screen_widget.__class__.__name__)
        screen_id = getattr(screen_widget, "screen_id", None)
        if not screen_id:
            slug_source = title.lower()
            screen_id = re.sub(r"[^a-z0-9]+", "_", slug_source).strip("_")
        self.screen_registry[screen_id] = screen_widget
        setattr(screen_widget, "html_id", screen_id)
        return screen_id

    def _set_active_screen(self, screen_reference):
        if isinstance(screen_reference, QWidget):
            screen_id = getattr(screen_reference, "html_id", None)
            if screen_id is None:
                screen_id = self._register_screen(screen_reference)
        else:
            screen_id = str(screen_reference)
        if screen_id != self.active_screen_id:
            self.active_screen_id = screen_id
        self._html_send("navigation", {"screen": self.active_screen_id})

    def _navigate_by_id(self, screen_id):
        screen = self.screen_registry.get(screen_id)
        if screen is not None:
            self.navigate_to(screen)
        else:
            print(f"[HTML] Requested screen '{screen_id}' not found.")

    def _html_send(self, event_name, payload=None):
        if not (self.use_html_ui and self._html_ready and self.html_view):
            return
        self.html_view.send_event(event_name, payload or {})

    def _collect_settings_summary(self):
        cfg = dict(getattr(self.settings_manager, "settings", {}))
        resolution = cfg.get("window_resolution") or [1024, 600]
        resolution_label = (
            f"{resolution[0]}x{resolution[1]}" if isinstance(resolution, (list, tuple)) and len(resolution) == 2 else "Unknown"
        )
        scale_mode_map = {
            "auto": "Auto (Scale with Resolution)",
            "fixed_small": "Small UI (Fixed Style)",
            "fixed_medium": "Medium UI (Fixed Style)",
            "fixed_large": "Large UI (Fixed Style)",
        }
        radio_i2c = cfg.get("radio_i2c_address")
        if isinstance(radio_i2c, int):
            radio_i2c_label = hex(radio_i2c)
        elif radio_i2c:
            radio_i2c_label = str(radio_i2c)
        else:
            radio_i2c_label = ""
        volume_value = cfg.get("volume", 0)
        if hasattr(self, "volume_slider") and self.volume_slider:
            try:
                volume_value = self.volume_slider.value()
            except Exception:
                pass
        try:
            volume_value = int(volume_value)
        except (TypeError, ValueError):
            volume_value = 0
        theme_value = cfg.get("theme", self.current_theme) or "dark"
        radio_type_value = cfg.get("radio_type", "none")
        last_station = cfg.get("last_fm_station")
        if isinstance(last_station, (int, float)):
            last_station_value = f"{float(last_station):.1f}"
        elif last_station is not None:
            last_station_value = str(last_station)
        else:
            last_station_value = ""
        summary = {
            "theme": theme_value,
            "ui_render_mode": cfg.get("ui_render_mode", "native"),
            "ui_scale_mode": cfg.get("ui_scale_mode", "auto"),
            "window_resolution": resolution_label,
            "show_cursor": bool(cfg.get("show_cursor")),
            "position_bottom_right": bool(cfg.get("position_bottom_right")),
            "developer_mode": bool(cfg.get("developer_mode")),
            "volume": volume_value,
            "radio_enabled": bool(cfg.get("radio_enabled")),
            "radio_type": radio_type_value,
            "last_fm_station": last_station_value,
            "radio_i2c_address": radio_i2c_label,
            "obd_enabled": bool(cfg.get("obd_enabled")),
            "obd_port": cfg.get("obd_port") or "",
            "obd_baudrate": str(cfg.get("obd_baudrate")) if cfg.get("obd_baudrate") else "",
        }
        return summary

    def _update_settings_field(self, key, value):
        if "settings" not in self.html_state:
            self.html_state["settings"] = {}
        self.html_state["settings"][key] = value
        self._html_send("settings", {key: value})

    def refresh_html_settings(self):
        summary = self._collect_settings_summary()
        self.html_state["settings"] = summary
        self._html_send("settings", summary)

    def _on_html_loaded(self, ok):
        if not ok:
            print("[HTML] Failed to load infotainment index.html")
            return
        # DO NOT push state here. Wait for the 'ready' signal from the JS,
        # which fires after all partials have been loaded.
        print("[HTML] index.html loaded. Waiting for JS 'ready' signal...")

    def _push_html_init_state(self):
        if not self.use_html_ui or not self._html_ready:
            return

        # REFRESH settings right before sending to ensure UI gets current values
        self.html_state["settings"] = self._collect_settings_summary()
        
        # REFACTORED: The screen list is no longer sent. The frontend discovers it from the DOM.
        payload = {
            "active": self.active_screen_id,
            "theme": self.current_theme,
            "volume": self.html_state["volume"],
            "bluetooth": self.html_state["bluetooth"],
            "radio": self.html_state["radio"],
            "obd": self.html_state["obd"],
            "media": self.html_state["media"],
            "settings": self.html_state["settings"],
        }
        self._html_send("init", payload)
        self._update_html_clock()

    def _update_html_clock(self):
        if not self.use_html_ui or not self._html_ready:
            return
        self._html_send("clock", {"value": self.header_clock_label.text()})

    def _pixmap_to_data_url(self, pixmap):
        if pixmap is None or pixmap.isNull():
            return None
        buffer = QBuffer()
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        success = pixmap.save(buffer, "PNG")
        buffer.close()
        if not success:
            return None
        encoded = base64.b64encode(bytes(buffer.data()))
        return f"data:image/png;base64,{encoded.decode('ascii')}"

    def _update_media_state(self, payload):
        if not isinstance(payload, dict):
            return
        self.html_state["media"].update(payload)
        self._html_send("media", self.html_state["media"])

    def _handle_media_properties_changed(self, properties):
        if not isinstance(properties, dict):
            properties = {}
        track = properties.get("Track", {}) if isinstance(properties.get("Track"), dict) else {}
        title = track.get("Title") or track.get("title")
        artist = track.get("Artist") or track.get("artist")
        album = track.get("Album") or track.get("album")
        duration = track.get("Duration") or track.get("duration") or 0
        art = (
            track.get("artUrl")
            or track.get("ArtUrl")
            or track.get("Artwork")
            or track.get("artwork")
        )
        position = properties.get("Position") or 0
        payload = {
            "source": "bluetooth",
            "title": title,
            "artist": artist,
            "album": album,
            "duration": duration,
            "position": position,
        }
        if art:
            payload["art"] = art
        elif properties == {}:
            payload["art"] = None
            payload["title"] = None
            payload["artist"] = None
            payload["album"] = None
            payload["duration"] = 0
            payload["position"] = 0
        self._update_media_state(payload)

    def _handle_playback_status_changed(self, status):
        self._update_media_state({"status": status, "source": "bluetooth"})

    def _handle_local_media_started(self, track_info):
        if not isinstance(track_info, dict):
            return
        track = track_info.get("Track", {})
        payload = {
            "source": "local",
            "title": track.get("Title"),
            "artist": track.get("Artist"),
            "album": track.get("Album"),
            "duration": track.get("Duration") or track_info.get("Duration") or 0,
            "position": track_info.get("Position") or 0,
        }
        if track_info.get("IsLocal"):
            payload["source"] = "local"
        self._update_media_state(payload)

    def _handle_local_playback_status(self, status):
        self._update_media_state({"status": status, "source": "local"})

    def _handle_local_playback_position(self, position, duration):
        self._update_media_state(
            {"position": position, "duration": duration, "source": "local"}
        )

    def _handle_local_album_art(self, pixmap):
        data_url = self._pixmap_to_data_url(pixmap)
        self._update_media_state({"art": data_url, "source": "local"})

    def resizeEvent(self, event):
        """Override resizeEvent to apply scaling ONLY after fullscreen is settled."""
        super().resizeEvent(event)
        current_size = event.size()
        print(f"DEBUG: resizeEvent triggered with Size: {current_size}")
        # Check if the size matches our target base (allowing for small variations if necessary)
        is_target_size = (
            abs(current_size.width() - self.BASE_RESOLUTION.width()) < 5
            and abs(current_size.height() - self.BASE_RESOLUTION.height()) < 5
        )

        if is_target_size and not self._has_scaled_correctly:
            print(f"Applying initial scaling for size: {current_size}")
            self._apply_scaling()
            self.update_header_title(
                self.stacked_widget.currentIndex()
            )  # Set title now

    def handle_html_event(self, name, payload):
        """Route events emitted by the HTML UI layer."""
        handler_name = f"_handle_html_{name}"
        handler = getattr(self, handler_name, None)
        if callable(handler):
            handler(payload or {})
        else:
            print(f"[HTML] Unhandled event: {name} -> {payload}")

    def _handle_html_ready(self, payload):
        self._html_ready = True
        self._push_html_init_state()

    def _handle_html_navigate(self, payload):
        target = payload.get("screen", "home")
        self._navigate_by_id(target)

    def _handle_html_toggle_mute(self, payload):
        self.toggle_mute()

    def _handle_html_set_volume(self, payload):
        try:
            value = int(payload.get("value", 0))
        except (TypeError, ValueError):
            return
        value = max(0, min(100, value))
        self.volume_slider.setValue(value)

    def _handle_html_open_dialog(self, payload):
        target = (payload or {}).get("target")
        if target == "bluetooth":
            self.open_bluetooth_dialog()
        elif target == "wifi":
            self.open_wifi_dialog()

    def _handle_html_apply_settings(self, payload):
        if not isinstance(payload, dict):
            print("[HTML] apply_settings payload invalid:", payload)
            return

        updates = {}
        for key, raw_value in payload.items():
            normalized = self._coerce_html_setting(key, raw_value)
            # The helper returns a special marker when we should skip the key entirely
            if normalized is _SkipSetting:
                continue
            updates[key] = normalized

        if not updates:
            print("[HTML] apply_settings received no valid updates.")
            return

        # Track changes that warrant immediate UI updates
        theme_changed = (
            "theme" in updates
            and updates["theme"]
            and updates["theme"] != self.settings_manager.get("theme")
        )
        scale_mode_changed = "ui_scale_mode" in updates
        resolution_changed = "window_resolution" in updates

        # Persist to configuration (single save to avoid repeated disk writes)
        self.settings_manager.settings.update(updates)
        self.settings_manager.save_settings()

        # Apply runtime adjustments where appropriate
        if resolution_changed:
            resolution = updates.get("window_resolution")
            if (
                isinstance(resolution, (list, tuple))
                and len(resolution) == 2
                and all(isinstance(dim, int) and dim > 0 for dim in resolution)
            ):
                self.resize(resolution[0], resolution[1])

        if theme_changed and updates.get("theme"):
            self.current_theme = updates["theme"]

        if theme_changed or scale_mode_changed or resolution_changed:
            # Recompute scaling/theme to reflect the new settings immediately
            self._apply_scaling()

        # Refresh HTML snapshot so controls reflect sanitized values
        self.refresh_html_settings()

    def _coerce_html_setting(self, key, value):
        """Normalize incoming setting values from the HTML UI."""
        if key == "window_resolution":
            if isinstance(value, str):
                cleaned = value.lower().replace("×", "x")
                try:
                    width_str, height_str = [part.strip() for part in cleaned.split("x", 1)]
                    width = int(width_str)
                    height = int(height_str)
                except (ValueError, AttributeError):
                    return _SkipSetting
                return [width, height]
            if isinstance(value, (list, tuple)) and len(value) == 2:
                try:
                    width = int(value[0])
                    height = int(value[1])
                except (TypeError, ValueError):
                    return _SkipSetting
                return [width, height]
            return _SkipSetting

        if key in {"show_cursor", "position_bottom_right", "developer_mode", "radio_enabled", "obd_enabled"}:
            return bool(value)

        if key == "last_fm_station":
            text = str(value).strip()
            if not text:
                return None
            try:
                return float(text)
            except ValueError:
                print(f"[HTML] Invalid last_fm_station value '{value}', skipping.")
                return _SkipSetting

        if key == "radio_i2c_address":
            text = str(value).strip()
            if not text:
                return None
            try:
                if text.lower().startswith("0x"):
                    return int(text, 16)
                return int(text, 10)
            except ValueError:
                try:
                    return int(text, 16)
                except ValueError:
                    return text

        if key == "obd_port":
            text = str(value).strip()
            return text or None

        if key == "obd_baudrate":
            text = str(value).strip()
            if not text:
                return None
            try:
                return int(text)
            except ValueError:
                print(f"[HTML] Invalid obd_baudrate value '{value}', skipping.")
                return _SkipSetting

        if key in {"theme", "ui_render_mode", "ui_scale_mode", "radio_type"}:
            text = str(value).strip()
            return text or self.settings_manager.defaults.get(key)

        return value

    def _handle_html_system_action(self, payload):
        action = (payload or {}).get("action")
        if action == "restart_app":
            self.restart_application()
        elif action == "reboot":
            self.reboot_system()
        elif action == "quit":
            self.close()
        elif action == "refresh_state":
            self.refresh_html_settings()
            self._push_html_init_state()

    def _handle_html_media_control(self, payload):
        action = (payload or {}).get("action")
        if not action:
            return
        action = action.lower()
        if action == "play_pause":
            self.music_player_screen.on_play_pause_clicked()
        elif action == "next":
            self.music_player_screen.on_next_clicked()
        elif action == "previous":
            self.music_player_screen.on_previous_clicked()

    def _handle_html_download_current_song(self, payload):
        """HTML: richiesta di scaricare la canzone corrente."""
        if hasattr(self, "music_player_screen") and self.music_player_screen is not None:
            print("[HTML] Download current song requested from HTML UI")
            self.music_player_screen.download_current_song()
        else:
            print("[HTML] Download requested but music_player_screen is not available")

    def _handle_html_play_track(self, payload):
        """
        HTML: richiesta di riprodurre una traccia dalla Library.
        Si aspetta almeno 'filename' nel payload.
        """
        if not hasattr(self, "music_player_screen") or self.music_player_screen is None:
            print("[HTML] play_track: music_player_screen not available")
            return

        filename = (payload or {}).get("filename")
        if not filename:
            print("[HTML] play_track: no filename provided in payload")
            return

        # Usa la stessa cartella della MusicPlayerScreen
        music_dir = getattr(self.music_player_screen, "music_dir", None)
        if not music_dir:
            print("[HTML] play_track: music_dir is not set on MusicPlayerScreen")
            return

        file_path = os.path.join(music_dir, filename)
        if not os.path.exists(file_path):
            print(f"[HTML] play_track: file not found: {file_path}")
            return

        print(f"[HTML] play_track: playing {file_path}")
        # Attiva la schermata Music Player (anche lato HTML)
        self._set_active_screen(self.music_player_screen)
        # Chiedi al MusicPlayerScreen di riprodurre il file
        self.music_player_screen.play_file_from_path(file_path)


    # --- Scaling ---
    def _apply_scaling(self):
        """Applies scaling to UI elements based on the UI scale mode setting."""
        current_height = self.height()  # Get current actual height

        # Get the UI scale mode from settings
        ui_scale_mode = self.settings_manager.get("ui_scale_mode")

        # Define base sizes for different UI modes
        ui_mode_settings = {
            "fixed_small": {  # Optimized for 1024x600
                "scale_factor": 1.0,
                "top_padding": 120,
                "icon_size": QSize(32, 32),
                "button_size": QSize(50, 50),
                "bottom_bar_height": 70,
                "slider_width": 180,
                "spacing": 10,
                "header_spacing": 15,
                "margin": 6,
                "main_margin": 10,
            },
            "fixed_medium": {  # Optimized for 1280x720
                "scale_factor": 1.2,
                "top_padding": 150,
                "icon_size": QSize(38, 38),
                "button_size": QSize(60, 60),
                "bottom_bar_height": 80,
                "slider_width": 220,
                "spacing": 12,
                "header_spacing": 18,
                "margin": 8,
                "main_margin": 12,
            },
            "fixed_large": {  # Optimized for 1920x1080
                "scale_factor": 1.8,
                "top_padding": 220,
                "icon_size": QSize(42, 42),
                "button_size": QSize(65, 65),
                "bottom_bar_height": 90,
                "slider_width": 300,
                "spacing": 15,
                "header_spacing": 20,
                "margin": 10,
                "main_margin": 15,
            },
        }

        # Determine the scale factor and UI settings based on the UI scale mode
        if ui_scale_mode == "auto":
            # Auto mode: Calculate scale factor based on current resolution
            if self.BASE_RESOLUTION.height() <= 0:
                scale_factor = 1.0
            else:
                scale_factor = current_height / self.BASE_RESOLUTION.height()

            # Use the base sizes defined in the class
            scaled_top_padding = scale_value(self.base_top_padding, scale_factor)
            scaled_icon_size = QSize(
                scale_value(self.base_icon_size.width(), scale_factor),
                scale_value(self.base_icon_size.height(), scale_factor),
            )
            scaled_button_size = QSize(
                scale_value(self.base_bottom_bar_button_size.width(), scale_factor),
                scale_value(self.base_bottom_bar_button_size.height(), scale_factor),
            )
            scaled_bottom_bar_height = scale_value(
                self.base_bottom_bar_height, scale_factor
            )
            scaled_slider_width = scale_value(
                self.base_volume_slider_width, scale_factor
            )
            scaled_spacing = scale_value(self.base_layout_spacing, scale_factor)
            scaled_header_spacing = scale_value(self.base_header_spacing, scale_factor)
            scaled_margin = scale_value(self.base_layout_margin, scale_factor)
            scaled_main_margin = scale_value(self.base_main_margin, scale_factor)

            print(f"DEBUG: Using AUTO scaling mode. Scale factor: {scale_factor:.3f}")
        elif ui_scale_mode in ui_mode_settings:
            # Use predefined settings for the selected UI mode
            settings = ui_mode_settings[ui_scale_mode]
            scale_factor = settings["scale_factor"]
            scaled_top_padding = settings["top_padding"]
            scaled_icon_size = settings["icon_size"]
            scaled_button_size = settings["button_size"]
            scaled_bottom_bar_height = settings["bottom_bar_height"]
            scaled_slider_width = settings["slider_width"]
            scaled_spacing = settings["spacing"]
            scaled_header_spacing = settings["header_spacing"]
            scaled_margin = settings["margin"]
            scaled_main_margin = settings["main_margin"]

            print(
                f"DEBUG: Using {ui_scale_mode.upper().replace('_', ' ')} UI mode (fixed scale factor: {scale_factor:.3f})"
            )
        else:
            # Fallback to auto mode if the setting is invalid
            if self.BASE_RESOLUTION.height() <= 0:
                scale_factor = 1.0
            else:
                scale_factor = current_height / self.BASE_RESOLUTION.height()

            # Use the base sizes defined in the class
            scaled_top_padding = scale_value(self.base_top_padding, scale_factor)
            scaled_icon_size = QSize(
                scale_value(self.base_icon_size.width(), scale_factor),
                scale_value(self.base_icon_size.height(), scale_factor),
            )
            scaled_button_size = QSize(
                scale_value(self.base_bottom_bar_button_size.width(), scale_factor),
                scale_value(self.base_bottom_bar_button_size.height(), scale_factor),
            )
            scaled_bottom_bar_height = scale_value(
                self.base_bottom_bar_height, scale_factor
            )
            scaled_slider_width = scale_value(
                self.base_volume_slider_width, scale_factor
            )
            scaled_spacing = scale_value(self.base_layout_spacing, scale_factor)
            scaled_header_spacing = scale_value(self.base_header_spacing, scale_factor)
            scaled_margin = scale_value(self.base_layout_margin, scale_factor)
            scaled_main_margin = scale_value(self.base_main_margin, scale_factor)

            print(
                f"DEBUG: Invalid UI scale mode '{ui_scale_mode}'. Using auto scaling: {scale_factor:.3f}"
            )

        # Print the final scaling information
        print(
            f"DEBUG: _apply_scaling factor: {scale_factor:.3f} (Height: {current_height})"
        )

        # --- Apply sizes and layouts ---
        # Apply to bottom bar elements
        self.home_button_bar.setIconSize(scaled_icon_size)
        self.home_button_bar.setFixedSize(scaled_button_size)
        self.settings_button.setIconSize(scaled_icon_size)
        self.settings_button.setFixedSize(scaled_button_size)
        self.bluetooth_button.setIconSize(scaled_icon_size)
        self.bluetooth_button.setFixedSize(scaled_button_size)
        self.wifi_button.setIconSize(scaled_icon_size)
        self.wifi_button.setFixedSize(scaled_button_size)
        self.volume_icon_button.setIconSize(scaled_icon_size)
        self.volume_icon_button.setFixedSize(scaled_button_size)
        self.restart_button_bar.setIconSize(scaled_icon_size)
        self.restart_button_bar.setFixedSize(scaled_button_size)
        self.power_button.setIconSize(scaled_icon_size)
        self.power_button.setFixedSize(scaled_button_size)

        # Apply to header quit button
        self.header_quit_button.setIconSize(scaled_icon_size)
        self.header_quit_button.setFixedSize(scaled_button_size)
        self.volume_slider.setFixedWidth(scaled_slider_width)
        self.bottom_bar_widget.setFixedHeight(scaled_bottom_bar_height)

        # Apply to layouts
        self.main_layout.setSpacing(scaled_spacing)
        # Add top padding via stylesheet on central widget
        padding_style = (
            f"QWidget#central_widget {{ padding-top: {scaled_top_padding}px; }}"
        )
        # Apply the padding style to the central widget
        self.central_widget.setStyleSheet(padding_style)

        self.header_layout.setSpacing(scaled_header_spacing)
        self.bottom_bar_layout.setContentsMargins(
            scaled_margin, scaled_margin, scaled_margin, scaled_margin
        )
        self.bottom_bar_layout.setSpacing(scaled_spacing)

        # --- Re-apply theme/stylesheet ---
        apply_theme(QApplication.instance(), self.current_theme, scale_factor)

        # --- Force style update on specific buttons to ensure custom styles are applied ---
        # This helps prevent system default styles from being used at higher resolutions
        self.home_button_bar.style().unpolish(self.home_button_bar)
        self.home_button_bar.style().polish(self.home_button_bar)
        self.settings_button.style().unpolish(self.settings_button)
        self.settings_button.style().polish(self.settings_button)
        self.bluetooth_button.style().unpolish(self.bluetooth_button)
        self.bluetooth_button.style().polish(self.bluetooth_button)
        self.wifi_button.style().unpolish(self.wifi_button)
        self.wifi_button.style().polish(self.wifi_button)
        self.volume_icon_button.style().unpolish(self.volume_icon_button)
        self.volume_icon_button.style().polish(self.volume_icon_button)
        self.restart_button_bar.style().unpolish(self.restart_button_bar)
        self.restart_button_bar.style().polish(self.restart_button_bar)
        self.power_button.style().unpolish(self.power_button)
        self.power_button.style().polish(self.power_button)

        # --- Update Header Bluetooth Status ---
        self.update_bluetooth_header_status()  # Update text/visibility

        # --- Notify Child Screens ---
        for screen in self.all_screens:
            if hasattr(screen, "update_scaling"):
                screen.update_scaling(scale_factor, scaled_main_margin)

    # --- Header Update Slots ---
    def _update_header_clock(self):
        """Updates the clock label in the header."""
        current_time = QDateTime.currentDateTime()
        time_str = current_time.toString("HH:mm")
        self.header_clock_label.setText(time_str)
        self._update_html_clock()

    @pyqtSlot(int)
    def update_header_title(self, index):
        """Updates the header title based on the current screen index."""
        current_widget = self.stacked_widget.widget(index)
        if current_widget:
            # Try to get a title attribute, fallback to class name or default
            title = getattr(
                current_widget, "screen_title", type(current_widget).__name__
            )
            self.header_title_label.setText(title)
            print(f"DEBUG: Header title set to: {title}")
            self._set_active_screen(current_widget)
        else:
            self.header_title_label.setText("Infotainment")  # Fallback

    # --- Combined Slot for Header BT Status Update ---
    @pyqtSlot()
    @pyqtSlot(bool)
    @pyqtSlot(object)
    def update_bluetooth_header_status(self, *args):
        """Updates the combined Bluetooth status text (Name + Battery) in the header."""
        connected = self.bluetooth_manager.connected_device_path is not None
        device_name = self.bluetooth_manager.connected_device_name if connected else ""
        # Get the latest battery level from the manager's state
        battery_level = self.bluetooth_manager.current_battery
        html_payload = {
            "connected": bool(connected),
            "device": device_name or None,
            "battery": battery_level if isinstance(battery_level, int) else None,
        }
        self.html_state["bluetooth"] = html_payload
        self._html_send("bluetooth_status", html_payload)

        if not self._has_scaled_correctly:
            return

        status_text = ""
        show_label = False

        if connected:
            show_label = True
            max_len = 25  # Max length for header display name part
            display_name = (
                (device_name[:max_len] + "...")
                if len(device_name) > max_len
                else device_name
            )
            status_text = display_name
            self.header_bt_status_label.setToolTip(
                device_name
            )  # Tooltip shows full name

            # --- RESTORED: Append battery level if available ---
            if battery_level is not None and isinstance(battery_level, int):
                # Ensure level is within expected 0-100 range
                battery_level = max(0, min(100, battery_level))
                status_text += f" - {battery_level}%"
            # Optionally indicate if battery unknown explicitly?
            else:
                status_text += " - Batt: N/A"

        print(
            f"DEBUG: Updating header BT status text: '{status_text}', Visible={show_label}"
        )
        self.header_bt_status_label.setText(status_text)
        self.header_bt_status_label.setVisible(show_label)

    # --- Status Update Slots ---
    @pyqtSlot(bool, str)
    def update_bluetooth_statusbar(self, connected, device_name):
        """Updates the Bluetooth status - now only updates header and home screen."""
        print(
            f"DEBUG: Updating BT status, Connected={connected}, Name='{device_name}'"
        )
        # Bottom bar status labels were removed, so we only update header and home screen
        if connected:
            print(f"Bluetooth device connected: {device_name}")
            # Header status is updated by update_bluetooth_header_status
            # Home screen media info is updated by the media player signals, not here
        else:
            print("Bluetooth device disconnected")
            # Clear home screen media info when device disconnects
            if hasattr(self.home_screen, "clear_media_info"):
                self.home_screen.clear_media_info()

    # --- OBD Status Update (Bottom bar labels removed, but OBD screen still needs updates) ---
    @pyqtSlot(bool, str)
    def update_obd_status(self, connected, message):
        if not self.settings_manager.get("obd_enabled"):
            status_text = "Disabled"
        else:
            status_text = message
        html_payload = {"connected": bool(connected), "status": status_text}
        self.html_state["obd"] = html_payload
        self._html_send("obd_status", html_payload)
        # Bottom bar status label removed, but still update OBD screen
        if hasattr(self.obd_screen, "update_connection_status"):
            self.obd_screen.update_connection_status(status_text)

    @pyqtSlot(str)
    def update_radio_status(self, status):
        if not self.settings_manager.get("radio_enabled"):
            status_text = "Disabled"
        else:
            radio_type = self.settings_manager.get("radio_type")
            status_text = "No HW" if radio_type == "none" else status
        # Bottom bar status label removed, but still update radio screen if needed
        if hasattr(self.radio_screen, "update_status_display"):
            self.radio_screen.update_status_display(status_text)
        self.html_state["radio"] = {"status": status_text}
        self._html_send("radio_status", self.html_state["radio"])

    def switch_theme(self, theme_name):
        """Switches theme and re-applies scaling/styling."""
        if theme_name != self.current_theme:
            print(f"Switching theme to: {theme_name}")
            self.current_theme = theme_name
            # Re-apply scaling which now includes re-applying the theme with the correct factor
            self._apply_scaling()
            self.settings_manager.set("theme", theme_name)
            self.refresh_html_settings()

    def update_obd_config(self):
        """Restarts OBD Manager with new connection settings."""
        # Only restart if OBD is currently enabled
        if self.settings_manager.get("obd_enabled"):
            print("OBD connection configuration updated. Restarting OBD Manager...")
            if hasattr(self, "obd_manager") and self.obd_manager.isRunning():
                self.obd_manager.stop()
                self.obd_manager.wait()
            # Recreate and start
            self.obd_manager = OBDManager(
                port=self.settings_manager.get("obd_port"),
                baudrate=self.settings_manager.get("obd_baudrate"),
            )
            self.obd_manager.connection_status.connect(self.update_obd_status)
            self.obd_manager.data_updated.connect(self.obd_screen.update_data)
            self.obd_manager.start()
        else:
            print("OBD connection settings saved, but OBD manager remains disabled.")

    def update_radio_config(self):
        """Restarts Radio Manager with new type/address settings."""
        # Only restart if Radio is currently enabled
        if self.settings_manager.get("radio_enabled"):
            print("Radio configuration updated. Restarting Radio Manager...")
            if hasattr(self, "radio_manager") and self.radio_manager.isRunning():
                last_freq = self.radio_manager.current_frequency
                self.radio_manager.stop()
                self.radio_manager.wait()
            else:
                last_freq = self.settings_manager.get(
                    "last_fm_station"
                )  # Use saved if not running

            # Recreate
            self.radio_manager = RadioManager(
                radio_type=self.settings_manager.get("radio_type"),
                i2c_address=self.settings_manager.get("radio_i2c_address"),
                initial_freq=last_freq,
            )
            # Reconnect signals
            self.radio_manager.radio_status.connect(self.update_radio_status)
            self.radio_manager.frequency_updated.connect(
                self.radio_screen.update_frequency
            )
            self.radio_manager.signal_strength.connect(
                self.radio_screen.update_signal_strength
            )
            # Start only if type is valid
            if self.radio_manager.radio_type != "none":
                self.radio_manager.start()
            else:
                self.update_radio_status("No HW")  # Update status if type is none
        else:
            print(
                "Radio connection settings saved, but Radio manager remains disabled."
            )

    # --- Methods to Toggle Managers ---
    def toggle_obd_manager(self, enable):
        """Starts or stops the OBD manager based on the enable flag."""
        if enable:
            if not hasattr(self, "obd_manager") or not self.obd_manager.isRunning():
                print("Enabling and starting OBD Manager...")
                # Ensure manager exists or recreate if needed
                if not hasattr(self, "obd_manager"):
                    self.obd_manager = OBDManager(
                        port=self.settings_manager.get("obd_port"),
                        baudrate=self.settings_manager.get("obd_baudrate"),
                    )
                    self.obd_manager.connection_status.connect(self.update_obd_status)
                    self.obd_manager.data_updated.connect(self.obd_screen.update_data)
                # Start the thread
                self.obd_manager.start()
                # Initial status will be emitted by the manager
            else:
                print("OBD Manager already running.")
        else:  # Disable
            if hasattr(self, "obd_manager") and self.obd_manager.isRunning():
                print("Disabling and stopping OBD Manager...")
                self.obd_manager.stop()
                self.obd_manager.wait(1000)  # Wait briefly
                # Update status immediately
                self.update_obd_status(False, "Disabled")
            else:
                print("OBD Manager already stopped or not initialized.")
                self.update_obd_status(False, "Disabled")  # Ensure status is correct

    def toggle_radio_manager(self, enable):
        """Starts or stops the Radio manager based on the enable flag."""
        radio_type = self.settings_manager.get("radio_type")
        if enable and radio_type != "none":
            if not hasattr(self, "radio_manager") or not self.radio_manager.isRunning():
                print("Enabling and starting Radio Manager...")
                if not hasattr(self, "radio_manager"):
                    self.radio_manager = RadioManager(
                        radio_type=radio_type,
                        i2c_address=self.settings_manager.get("radio_i2c_address"),
                        initial_freq=self.settings_manager.get("last_fm_station"),
                    )
                    self.radio_manager.radio_status.connect(self.update_radio_status)
                    self.radio_manager.frequency_updated.connect(
                        self.radio_screen.update_frequency
                    )
                    self.radio_manager.signal_strength.connect(
                        self.radio_screen.update_signal_strength
                    )
                self.radio_manager.start()
            else:
                print("Radio Manager already running.")
        else:  # Disable or radio_type is "none"
            if hasattr(self, "radio_manager") and self.radio_manager.isRunning():
                print("Disabling and stopping Radio Manager...")
                self.radio_manager.stop()
                self.radio_manager.wait(1000)
                self.update_radio_status("Disabled")  # Update status
            else:
                status = "Disabled" if not enable else "No HW"
                print(
                    f"Radio Manager already stopped or hardware type is '{radio_type}'."
                )
                self.update_radio_status(
                    status
                )  # Ensure status reflects disabled or no hw

    def restart_application(self):
        """Gracefully stops threads and restarts the current Python application."""
        print("Attempting to restart application...")
        confirm = QMessageBox.warning(
            self,
            "Restart Confirmation",
            "Are you sure you want to restart the application?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if confirm == QMessageBox.StandardButton.Yes:
            try:
                # Cleanly stop threads before restarting
                print("Stopping background threads before restart...")
                if hasattr(self, "radio_manager") and self.radio_manager.isRunning():
                    self.radio_manager.stop()
                    self.radio_manager.wait(1500)  # Wait max 1.5s
                if hasattr(self, "obd_manager") and self.obd_manager.isRunning():
                    self.obd_manager.stop()
                    self.obd_manager.wait(1500)  # Wait max 1.5s
                if hasattr(self, "airplay_manager"):
                    self.airplay_manager.cleanup()
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
                QMessageBox.critical(
                    self, "Restart Error", f"Could not restart application:\n{e}"
                )
                # Fallback: Just exit if restart fails critically
                QApplication.quit()
        else:
            print("Restart cancelled by user.")

    def reboot_system(self):
        """Gracefully stops threads and reboots the Raspberry Pi."""
        print("Attempting to reboot system...")
        
        confirm = QMessageBox.warning(
            self,
            "Reboot Confirmation",
            "Are you sure you want to reboot the Raspberry Pi?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if confirm == QMessageBox.StandardButton.Yes:
            try:
                print("Stopping background threads before reboot...")
                if hasattr(self, "radio_manager") and self.radio_manager.isRunning():
                    self.radio_manager.stop()
                    self.radio_manager.wait(1500)
                if hasattr(self, "obd_manager") and self.obd_manager.isRunning():
                    self.obd_manager.stop()
                    self.obd_manager.wait(1500)
                if hasattr(self, "bluetooth_manager") and self.bluetooth_manager.isRunning():
                    self.bluetooth_manager.stop()
                    self.bluetooth_manager.wait(1500)
                if hasattr(self, "airplay_manager"):
                    self.airplay_manager.cleanup()
                print("Threads stopped.")

                if hasattr(self, "radio_manager") and self.radio_manager.radio_type != "none":
                    self.settings_manager.set(
                        "last_fm_station", self.radio_manager.current_frequency
                    )
                if self.last_volume_level > 0:
                    self.settings_manager.set("volume", self.last_volume_level)
                elif self.volume_slider.value() == 0 and not self.is_muted:
                    self.settings_manager.set("volume", 0)

                print("Settings saved. Initiating system reboot...")
                sys.stdout.flush()
                sys.stderr.flush()

                # Try using systemctl first (standard on RPi OS)
                try:
                    result = subprocess.run(["sudo", "systemctl", "reboot"], capture_output=True, text=True)
                    if result.returncode != 0:
                        print(f"systemctl reboot failed: {result.stderr}. Trying direct reboot...")
                        # Fallback to direct reboot command
                        result = subprocess.run(["sudo", "reboot"], capture_output=True, text=True)
                        if result.returncode != 0:
                            raise RuntimeError(f"Reboot failed: {result.stderr}")
                except Exception as e:
                     raise RuntimeError(f"Failed to execute reboot command: {e}")

            except Exception as e:
                print(f"Error attempting to reboot system: {e}")
                QMessageBox.critical(
                    self, "Reboot Error", f"Could not reboot system:\n{e}\n\nClosing application instead."
                )
                self.close() # Fallback to close app if reboot fails
        else:
            print("Reboot cancelled by user.")

    def shutdown_system(self):
        """Gracefully stops threads and shuts down the Raspberry Pi."""
        print("Attempting to shutdown system...")
        confirm = QMessageBox.warning(
            self,
            "Shutdown Confirmation",
            "Are you sure you want to shutdown the Raspberry Pi?\n\nThis will power off the system completely.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if confirm == QMessageBox.StandardButton.Yes:
            try:
                # Cleanly stop threads before shutdown
                print("Stopping background threads before shutdown...")
                if hasattr(self, "radio_manager") and self.radio_manager.isRunning():
                    self.radio_manager.stop()
                    self.radio_manager.wait(1500)  # Wait max 1.5s
                if hasattr(self, "obd_manager") and self.obd_manager.isRunning():
                    self.obd_manager.stop()
                    self.obd_manager.wait(1500)  # Wait max 1.5s
                if hasattr(self, "bluetooth_manager") and self.bluetooth_manager.isRunning():
                    self.bluetooth_manager.stop()
                    self.bluetooth_manager.wait(1500)
                if hasattr(self, "airplay_manager"):
                    self.airplay_manager.cleanup()
                print("Threads stopped.")

                # Save settings
                if hasattr(self, "radio_manager") and self.radio_manager.radio_type != "none":
                    self.settings_manager.set(
                        "last_fm_station", self.radio_manager.current_frequency
                    )

                # Save volume settings
                if self.last_volume_level > 0:
                    print(f"Saving last non-muted volume: {self.last_volume_level}")
                    self.settings_manager.set("volume", self.last_volume_level)
                elif self.volume_slider.value() == 0 and not self.is_muted:
                    print("Saving volume as 0 (manually set)")
                    self.settings_manager.set("volume", 0)

                print("Settings saved. Initiating system shutdown...")

                # Flush outputs
                sys.stdout.flush()
                sys.stderr.flush()

                # Execute system shutdown command
                subprocess.run(["sudo", "shutdown", "-h", "now"], check=False)

            except Exception as e:
                print(f"Error attempting to shutdown system: {e}")
                QMessageBox.critical(
                    self, "Shutdown Error", f"Could not shutdown system:\n{e}\n\nClosing application instead."
                )
                # Fallback: Just close the application if shutdown fails
                self.close()
        else:
            print("Shutdown cancelled by user.")

    def closeEvent(self, event):
        """Handles window close events (triggered by Alt+F4, Ctrl+Q, Power button)."""
        # ... (Save volume settings logic) ...
        if self.last_volume_level > 0:  # Save last non-muted
            print(f"Saving last non-muted volume: {self.last_volume_level}")
            self.settings_manager.set("volume", self.last_volume_level)
        elif (
            self.volume_slider.value() == 0 and not self.is_muted
        ):  # Save 0 if manually set
            print("Saving volume as 0 (manually set)")
            self.settings_manager.set("volume", 0)

        print("Close event triggered. Stopping background threads...")

        # Chiama il nuovo metodo di pulizia per l'AudioManager
        if hasattr(self, "audio_manager"):
            self.audio_manager.cleanup()


        if hasattr(self, "airplay_manager"):
            print("Stopping AirPlay Manager...")
            self.airplay_manager.cleanup()
            print("AirPlay Manager stopped.")

            
        # Stop threads gracefully
        if hasattr(self, "radio_manager") and self.radio_manager.isRunning():
            self.radio_manager.stop()
            self.radio_manager.wait(1500)
        if hasattr(self, "obd_manager") and self.obd_manager.isRunning():
            self.obd_manager.stop()
            self.obd_manager.wait(1500)
        if hasattr(self, "bluetooth_manager") and self.bluetooth_manager.isRunning():
            print("Stopping Bluetooth Manager...")
            self.bluetooth_manager.stop()
            self.bluetooth_manager.wait(1500)
            print("Bluetooth Manager stopped.")
        if hasattr(self, "airplay_manager"):
            print("Stopping AirPlay Manager...")
            self.airplay_manager.cleanup()
            print("AirPlay Manager stopped.")
        # Save other settings
        if hasattr(self, "radio_manager") and self.radio_manager.radio_type != "none":
            self.settings_manager.set(
                "last_fm_station", self.radio_manager.current_frequency
            )
        print("Threads stopped. Exiting.")
        event.accept()  # Accept the close event

    # --- toggle_mute to use AudioManager ---
    def toggle_mute(self):
        """Toggles volume mute state using AudioManager."""
        if self.is_muted:
            # --- Unmuting ---
            restore_level = self.last_volume_level if self.last_volume_level > 0 else 50
            # Update UI first
            self.volume_slider.setValue(restore_level)  # Update slider visually
            self.volume_icon_button.setIcon(self.volume_normal_icon)
            self.volume_icon_button.setChecked(False)
            self.is_muted = False
            # Tell AudioManager to unmute the system
            print(f"UI Unmuted. Restoring level to {restore_level}. Telling system...")
            self.audio_manager.set_mute(False)
            # Setting mute to false often restores previous volume, but let's set explicitly
            self.audio_manager.set_volume(restore_level)  # Ensure system matches slider

        else:
            # --- Muting ---
            current_volume = self.volume_slider.value()
            # Store the current level ONLY if it's not already 0
            if current_volume > 0:
                self.last_volume_level = current_volume

            # Update UI first
            self.volume_slider.setValue(0)  # Update slider visually
            self.volume_icon_button.setIcon(self.volume_muted_icon)
            self.volume_icon_button.setChecked(True)
            self.is_muted = True
            # Tell AudioManager to mute the system
            print(
                f"UI Muted. Last level was {self.last_volume_level}. Telling system..."
            )
            self.audio_manager.set_mute(True)
            # No need to call set_volume(0) as set_mute(True) handles it
        slider_value = self.volume_slider.value()
        self.html_state["volume"]["level"] = slider_value
        self.html_state["volume"]["muted"] = self.is_muted
        self._html_send("volume", self.html_state["volume"])
        self._update_settings_field("volume", slider_value)

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
        self.html_state["volume"]["level"] = value
        self.html_state["volume"]["muted"] = self.is_muted or value == 0
        self._html_send("volume", self.html_state["volume"])
        self._update_settings_field("volume", value)

    def go_to_home(self):
        """Navigates to the home screen."""
        print("Home button clicked, navigating...")
        self.navigate_to(self.home_screen)

    def go_to_settings(self):
        """Navigates to the settings screen."""
        print("Settings button clicked, navigating...")
        self.navigate_to(self.settings_screen)

    def go_to_music_player(self):
        """Navigates to the music player screen."""
        print("Music player button clicked, navigating...")
        self.navigate_to(self.music_player_screen)

    # --- Add a helper method for navigation if desired ---
    def navigate_to(self, screen_widget):
        """Sets the current screen in the stacked widget."""
        index = self.stacked_widget.indexOf(screen_widget)
        if index != -1:
            self.stacked_widget.setCurrentWidget(screen_widget)
        else:
            print(f"Error: Cannot navigate to {screen_widget}. Not found in stack.")
        self._set_active_screen(screen_widget)

    # --- AirPlay Stream Management ---
    @pyqtSlot(bool)
    def on_airplay_stream_widget(self, show):
        """Handle AirPlay stream widget show/hide from the stream manager."""
        if show:
            # Create stream widget if it doesn't exist
            if not hasattr(self, 'airplay_stream_widget') or not self.airplay_stream_widget:
                self.airplay_stream_widget = self._create_airplay_stream_widget()

            if self.airplay_stream_widget:
                self.airplay_stream_widget.show_widget()
                print("AirPlay stream widget shown")
        else:
            # Hide stream widget
            if hasattr(self, 'airplay_stream_widget') and self.airplay_stream_widget:
                self.airplay_stream_widget.hide_widget()

            print("AirPlay stream widget hidden")

    def _create_airplay_stream_widget(self):
        """Create the AirPlay stream widget."""
        from .airplay_stream_widget import AirPlayStreamWidget

        widget = AirPlayStreamWidget(self)

        # Connect signals
        widget.stop_airplay.connect(self.stop_airplay_streaming)

        return widget

    @pyqtSlot()
    def stop_airplay_streaming(self):
        """Stop AirPlay streaming completely."""
        if self.airplay_manager:
            self.airplay_manager.stop_airplay()

        print("AirPlay streaming stopped by user")

    # --- Network Dialog Methods ---
    @pyqtSlot()
    def open_bluetooth_dialog(self):
        """Open the Bluetooth settings dialog."""
        try:
            dialog = BluetoothDialog(self.bluetooth_manager, self)
            dialog.exec()
        except Exception as e:
            print(f"Error opening Bluetooth dialog: {e}")

    @pyqtSlot()
    def open_wifi_dialog(self):
        """Open the WiFi settings dialog."""
        try:
            dialog = WiFiDialog(self.wifi_manager, self)
            dialog.exec()
        except Exception as e:
            print(f"Error opening WiFi dialog: {e}")
