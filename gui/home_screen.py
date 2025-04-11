# gui/home_screen.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QPushButton, QLabel, QSpacerItem, QSizePolicy)
from PyQt6.QtCore import QTimer, QDateTime, Qt, QSize, pyqtSlot
from PyQt6.QtGui import QPixmap, QIcon

# --- Import scale_value helper ---
try:
    from .styling import scale_value
except ImportError:
    # Fallback if styling.py doesn't have it or import fails
    def scale_value(base, factor): return max(1, int(base * factor))

# --- Import ScrollingLabel ---
try:
    from .widgets.scrolling_label import ScrollingLabel
except ImportError:
    print("WARNING: ScrollingLabel not found. Falling back to standard QLabel.")
    ScrollingLabel = QLabel # Fallback


class HomeScreen(QWidget):
    # --- ADDED: Screen Title ---
    screen_title = "Home"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent

        # --- Store base sizes for scaling ---
        self.base_margin = 10
        self.base_top_section_spacing = 15
        self.base_grid_spacing = 8
        self.base_media_spacing = 10 # Vertical spacing in media player
        self.base_media_playback_button_spacing = 5

        # --- Main Layout (Vertical) ---
        self.main_layout = QVBoxLayout(self)
        # Margins/Spacing set by update_scaling

        # --- Top Section Layout (Horizontal: Grid, Media Player) ---
        self.top_section_layout = QHBoxLayout() # Store reference
        # Spacing set by update_scaling

        # --- 1. Grid Layout for Main Buttons ---
        self.grid_widget = QWidget()
        self.grid_widget.setObjectName("grid_widget")
        self.grid_layout = QGridLayout(self.grid_widget) # Store reference
        # Spacing set by update_scaling

        buttons_data = [
            ("Telephone", "phone-icon.png"),
            ("Android Auto", "android-auto-icon.png"),
            ("OBD", "obd-icon.png"),
            ("Mirroring", "mirroring-icon.png"),
            ("Rear Camera", "camera-icon.png"),
            ("Music", "music-icon.png"),
            ("Radio", "radio-icon.png"),
            ("Equalizer", "eq-icon.png"),
            ("Settings", "settings-icon.png")
        ]

        target_cols = 5
        num_buttons = len(buttons_data)
        num_rows = (num_buttons + target_cols - 1) // target_cols

        btn_index = 0
        for r in range(num_rows):
            for c in range(target_cols):
                if btn_index < num_buttons:
                    name, icon_path = buttons_data[btn_index]
                    button = QPushButton(name)
                    button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                    button.setObjectName(f"homeBtn{name.replace(' ', '')}")
                    button.clicked.connect(lambda checked, b=name: self.on_home_button_clicked(b))
                    self.grid_layout.addWidget(button, r, c)
                    btn_index += 1

        # Vertical spacer to push buttons up within the grid area
        grid_vertical_spacer = QSpacerItem(20, 1, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.grid_layout.addItem(grid_vertical_spacer, num_rows, 0, 1, target_cols)
        self.grid_widget.setLayout(self.grid_layout) # Set layout on grid container


        # --- 2. Media Player Section ---
        self.media_widget = QWidget()
        self.media_widget.setObjectName("media_widget")
        self.media_layout = QVBoxLayout(self.media_widget) # Store reference
        # Spacing set by update_scaling
        # Removed AlignTop - Let stretch factor handle vertical distribution

        # Album Label (Scrolling, square via QSS, takes most vertical space)
        self.album_art_label = ScrollingLabel("(Album)")
        self.album_art_label.setObjectName("albumArtLabel")
        self.album_art_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Give it a larger stretch factor (e.g., 4 or 5)
        self.media_layout.addWidget(self.album_art_label, 9, Qt.AlignmentFlag.AlignHCenter)

        # Title Label (Scrolling, less vertical space)
        self.track_title_label = ScrollingLabel()
        self.track_title_label.setObjectName("trackTitleLabel")
        self.track_title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.media_layout.addWidget(self.track_title_label, 0) # Smaller stretch factor (e.g., 1)

        # Artist Label (Scrolling, less vertical space)
        self.track_artist_label = ScrollingLabel()
        self.track_artist_label.setObjectName("trackArtistLabel")
        self.track_artist_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.media_layout.addWidget(self.track_artist_label, 0) # Smaller stretch factor (e.g., 1)

        # Time Label (Standard, minimal vertical space)
        self.track_time_label = QLabel("--:-- / --:--")
        self.track_time_label.setObjectName("trackTimeLabel")
        self.track_time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.media_layout.addWidget(self.track_time_label, 0) # Smallest stretch factor (0)

        # --- Playback Controls (Default vertical space) ---
        self.playback_layout = QHBoxLayout() # Store reference
        # Spacing set by update_scaling
        self.btn_prev = QPushButton("<<")
        self.btn_play_pause = QPushButton("▶") # Text updated by update_playback_status
        self.btn_next = QPushButton(">>")
        self.btn_prev.setObjectName("mediaPrevButton")
        self.btn_play_pause.setObjectName("mediaPlayPauseButton")
        self.btn_next.setObjectName("mediaNextButton")

        self.playback_layout.addStretch(1)
        self.playback_layout.addWidget(self.btn_prev)
        self.playback_layout.addWidget(self.btn_play_pause)
        self.playback_layout.addWidget(self.btn_next)
        self.playback_layout.addStretch(1)
        self.media_layout.addLayout(self.playback_layout) # Added with default stretch 0

        # --- Stretch at the end ---
        # This pushes all the above widgets upwards in the media_layout
        self.media_layout.addStretch(1)

      

        # Connect control buttons
        self.btn_prev.clicked.connect(self.on_previous_clicked)
        self.btn_play_pause.clicked.connect(self.on_play_pause_clicked)
        self.btn_next.clicked.connect(self.on_next_clicked)

        # Removed extra stretch at the end
        self.media_widget.setLayout(self.media_layout) # Set layout on media container


        # --- Add Grid and Media Player to Top Section with Stretch Factors ---
        # Grid gets 2/3, Media Player gets 1/3 of horizontal space
        self.top_section_layout.addWidget(self.grid_widget, 2) # Stretch factor 2
        self.top_section_layout.addWidget(self.media_widget, 1) # Stretch factor 1

        # --- Add Top Section to Main Layout (Stretch=1, takes remaining vertical space) ---
        self.main_layout.addLayout(self.top_section_layout, 1) # IMPORTANT: Stretch factor 1


        # --- Initial state ---
        self.clear_media_info()


    def update_scaling(self, scale_factor, scaled_main_margin):
        """Applies scaling to internal layouts."""
        scaled_top_section_spacing = scale_value(self.base_top_section_spacing, scale_factor)
        scaled_grid_spacing = scale_value(self.base_grid_spacing, scale_factor)
        scaled_media_spacing = scale_value(self.base_media_spacing, scale_factor)
        scaled_playback_spacing = scale_value(self.base_media_playback_button_spacing, scale_factor)

        # Apply to layouts
        self.main_layout.setContentsMargins(scaled_main_margin, scaled_main_margin, scaled_main_margin, scaled_main_margin)
        self.main_layout.setSpacing(scaled_main_margin) # Or a separate base spacing value

        self.top_section_layout.setSpacing(scaled_top_section_spacing)
        self.grid_layout.setSpacing(scaled_grid_spacing)
        self.media_layout.setSpacing(scaled_media_spacing)
        self.playback_layout.setSpacing(scaled_playback_spacing)


    @pyqtSlot(dict)
    def update_media_info(self, properties):
        """Updates the media player display based on BT properties."""
        # print("HomeScreen received media properties:", properties) # DEBUG
        track_info = properties.get('Track', {})
        duration_ms = track_info.get('Duration', 0)
        position_ms = properties.get('Position', 0)
        title = track_info.get('Title', "---")
        artist = track_info.get('Artist', "---")
        album = track_info.get('Album', "")

        # Update scrolling labels
        self.track_title_label.setText(title)
        self.track_artist_label.setText(artist)
        self.album_art_label.setText(album if album else "(Album Unknown)")

        # Update time label
        pos_sec = position_ms // 1000
        dur_sec = duration_ms // 1000
        pos_str = f"{pos_sec // 60:02d}:{pos_sec % 60:02d}"
        dur_str = f"{dur_sec // 60:02d}:{dur_sec % 60:02d}" if dur_sec > 0 else "--:--"
        self.track_time_label.setText(f"{pos_str} / {dur_str}")


    @pyqtSlot(str)
    def update_playback_status(self, status):
        """Updates the play/pause button icon based on playback status."""
        print(f"HomeScreen received playback status: {status}")
        if status == "playing":
            self.btn_play_pause.setText("⏸")
        elif status == "paused":
            self.btn_play_pause.setText("▶")
        else: # stopped, etc.
            self.btn_play_pause.setText("▶")
            # Clear info ONLY if stopped and track info is already present
            if status == "stopped" and self.track_title_label.text() != "---":
                 self.clear_media_info()


    def clear_media_info(self):
        """Resets media player display to default state."""
        self.track_title_label.setText("---")
        self.track_artist_label.setText("---")
        self.track_time_label.setText("--:-- / --:--")
        self.album_art_label.setText("(No Media)")
        self.btn_play_pause.setText("▶")


    # --- Click Handlers ---
    def on_play_pause_clicked(self):
        print("Play/Pause button clicked")
        if self.main_window and self.main_window.bluetooth_manager:
            current_status = self.main_window.bluetooth_manager.playback_status
            if current_status == "playing":
                self.main_window.bluetooth_manager.send_pause()
            else:
                self.main_window.bluetooth_manager.send_play()
        else: print("Error: Cannot send command - BluetoothManager not available.")

    def on_next_clicked(self):
        print("Next button clicked")
        if self.main_window and self.main_window.bluetooth_manager:
            self.main_window.bluetooth_manager.send_next()
        else: print("Error: Cannot send command - BluetoothManager not available.")

    def on_previous_clicked(self):
        print("Previous button clicked")
        if self.main_window and self.main_window.bluetooth_manager:
            self.main_window.bluetooth_manager.send_previous()
        else: print("Error: Cannot send command - BluetoothManager not available.")

    # --- Navigation and Clock ---
    def on_home_button_clicked(self, button_name):
        """Handle clicks on the main grid buttons and navigate."""
        print(f"Home button clicked: {button_name}")
        if self.main_window is not None and hasattr(self.main_window, 'navigate_to'):
            if button_name == "OBD" and hasattr(self.main_window, 'obd_screen'):
                self.main_window.navigate_to(self.main_window.obd_screen)
            elif button_name == "Radio" and hasattr(self.main_window, 'radio_screen'):
                self.main_window.navigate_to(self.main_window.radio_screen)
            elif button_name == "Settings" and hasattr(self.main_window, 'settings_screen'):
                self.main_window.navigate_to(self.main_window.settings_screen)
            # ... other navigation cases ...
            else:
                 print(f"No navigation action defined for: {button_name}")
        else:
            print("Error: Could not navigate. Main window reference is invalid or missing 'navigate_to' method.")
