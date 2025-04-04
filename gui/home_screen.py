# gui/home_screen.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QPushButton, QLabel, QSpacerItem, QSizePolicy,
                             QSlider) # Keep QSlider if used elsewhere, maybe not needed here
from PyQt6.QtCore import QTimer, QDateTime, Qt, QSize, pyqtSlot
from PyQt6.QtGui import QPixmap, QIcon

# --- Import scale_value helper ---
# Assuming it's accessible, e.g. defined in styling or a utils module
# If styling.py is in the same directory:
# from .styling import scale_value
# If scale_value is defined elsewhere, adjust import path:
from .styling import scale_value


class HomeScreen(QWidget):
    def __init__(self, parent=None): # parent is likely MainWindow now
        super().__init__(parent)
        self.main_window = parent

        # --- Store base sizes for scaling ---
        self.base_margin = 10 # Corresponds to main_margin in MainWindow
        self.base_header_spacing = 10
        self.base_top_section_spacing = 15
        self.base_grid_spacing = 8
        self.base_media_spacing = 10
        self.base_media_playback_button_spacing = 5 # Spacing for prev/play/next

        # --- Main Layout ---
        self.main_layout = QVBoxLayout(self)
        # Margins/Spacing set by update_scaling

        # --- Header Layout ---
        self.header_layout = QHBoxLayout() # Store reference
        # Spacing set by update_scaling
        self.header_title_label = QLabel("Home")
        self.header_title_label.setObjectName("headerTitle") # Styled by QSS
        self.header_layout.addWidget(self.header_title_label)
        spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.header_layout.addItem(spacer)
        self.clock_label = QLabel("00:00")
        self.clock_label.setObjectName("headerClock") # Styled by QSS
        self.header_layout.addWidget(self.clock_label)
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(10000)
        self._update_clock()
        self.main_layout.addLayout(self.header_layout)
        # --- End Header ---

        # --- Top Section Layout (Grid + Media Player) ---
        self.top_section_layout = QHBoxLayout() # Store reference
        # Spacing set by update_scaling

        # --- 1. Grid Layout for Main Buttons ---
        self.grid_widget = QWidget()
        self.grid_widget.setObjectName("grid_widget") # ID for potential styling
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
                    # Size policy allows button to fill grid cell
                    button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                    button.setObjectName(f"homeBtn{name.replace(' ', '')}")
                    button.clicked.connect(lambda checked, b=name: self.on_home_button_clicked(b))
                    self.grid_layout.addWidget(button, r, c)
                    btn_index += 1

        # Vertical spacer to push buttons up
        vertical_spacer = QSpacerItem(20, 1, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.grid_layout.addItem(vertical_spacer, num_rows, 0, 1, target_cols)


        # --- 2. Media Player Section ---
        self.media_widget = QWidget()
        self.media_widget.setObjectName("media_widget") # ID for potential styling
        self.media_layout = QVBoxLayout(self.media_widget) # Store reference
        # Spacing set by update_scaling
        self.media_layout.setAlignment(Qt.AlignmentFlag.AlignTop) # Keep content aligned top

        self.album_art_label = QLabel("Album Art") # Placeholder text
        self.album_art_label.setObjectName("albumArtLabel") # Use ID for styling in QSS
        # Remove fixed/min/max sizes - control via QSS (e.g., min-width, min-height) or leave to layout
        # self.album_art_label.setMinimumSize(150, 150) # REMOVE
        # self.album_art_label.setMaximumSize(200, 200) # REMOVE
        # self.album_art_label.setStyleSheet(...) # REMOVE - Style via QSS and objectName
        self.album_art_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.media_layout.addWidget(self.album_art_label, 0, Qt.AlignmentFlag.AlignHCenter) # Stretch factor 0

        self.track_title_label = QLabel("Track Title")
        self.track_title_label.setObjectName("trackTitleLabel")
        # self.track_title_label.setStyleSheet(...) # REMOVE - Style via QSS
        self.track_artist_label = QLabel("Artist Name")
        self.track_artist_label.setObjectName("trackArtistLabel")
        self.track_time_label = QLabel("00:00 / 00:00")
        self.track_time_label.setObjectName("trackTimeLabel")

        self.media_layout.addWidget(self.track_title_label)
        self.media_layout.addWidget(self.track_artist_label)
        self.media_layout.addWidget(self.track_time_label)

        # Playback Controls
        self.playback_layout = QHBoxLayout() # Store reference
        # Spacing set by update_scaling
        self.btn_prev = QPushButton("<<")
        self.btn_play_pause = QPushButton("▶")
        self.btn_next = QPushButton(">>")
        # Add specific object names if unique styling is needed
        self.btn_prev.setObjectName("mediaPrevButton")
        self.btn_play_pause.setObjectName("mediaPlayPauseButton")
        self.btn_next.setObjectName("mediaNextButton")

        self.playback_layout.addStretch(1)
        self.playback_layout.addWidget(self.btn_prev)
        self.playback_layout.addWidget(self.btn_play_pause)
        self.playback_layout.addWidget(self.btn_next)
        self.playback_layout.addStretch(1)
        self.media_layout.addLayout(self.playback_layout)

        self.media_layout.addStretch(1) # Pushes media content upwards

        # --- Add widgets to top_section_layout ---
        self.top_section_layout.addWidget(self.grid_widget, 1) # Grid takes expanding space
        self.top_section_layout.addStretch(1)                   # Spacer
        self.top_section_layout.addWidget(self.media_widget)    # Media player takes preferred size

        # --- Add Top Section to Main Layout ---
        self.main_layout.addLayout(self.top_section_layout, 1) # Stretch factor 1 for vertical space


    # --- ADDED: Slot to update media player info ---
    @pyqtSlot(dict)
    def update_media_info(self, properties):
        """Updates the media player display based on BT properties."""
        print("HomeScreen received media properties:", properties)
        track_info = properties.get('Track', {})
        duration_ms = track_info.get('Duration', 0) # Default to Python int 0
        position_ms = properties.get('Position', 0) # Default to Python int 0

        title = track_info.get('Title', "Unknown Title") # Default to Python str
        artist = track_info.get('Artist', "Unknown Artist") # Default to Python str
        album = track_info.get('Album', "Unknown Album") # Default to Python str

        self.track_title_label.setText(title)
        self.track_artist_label.setText(artist)
        self.album_art_label.setText(f"{album}\n(Art N/A)") # Update placeholder text, art not usually available

        # Format time display (mm:ss / mm:ss)
        pos_sec = position_ms // 1000
        dur_sec = duration_ms // 1000
        pos_str = f"{pos_sec // 60:02d}:{pos_sec % 60:02d}"
        dur_str = f"{dur_sec // 60:02d}:{dur_sec % 60:02d}" if dur_sec > 0 else "??:??"
        self.track_time_label.setText(f"{pos_str} / {dur_str}")

    # --- ADDED: Slot to update playback status ---
    @pyqtSlot(str)
    def update_playback_status(self, status):
        """Updates the play/pause button icon based on playback status."""
        print(f"HomeScreen received playback status: {status}")
        if status == "playing":
            self.btn_play_pause.setText("⏸") # Use pause symbol
            # Or use an icon: self.btn_play_pause.setIcon(QIcon("path/to/pause_icon.png"))
        elif status == "paused":
            self.btn_play_pause.setText("▶") # Use play symbol
            # Or use an icon: self.btn_play_pause.setIcon(QIcon("path/to/play_icon.png"))
        else: # stopped, forward-seek, reverse-seek etc.
            self.btn_play_pause.setText("▶") # Default to play symbol
            if status == "stopped":
                 self.clear_media_info() # Clear info if stopped

    # --- ADDED: Helper to clear media info ---
    def clear_media_info(self):
        """Resets media player display to default state."""
        self.track_title_label.setText("---")
        self.track_artist_label.setText("---")
        self.track_time_label.setText("00:00 / 00:00")
        self.album_art_label.setText("Album Art") # Reset placeholder
        self.btn_play_pause.setText("▶") # Default to play symbol
  
    def update_scaling(self, scale_factor, scaled_main_margin):
        """Applies scaling to internal layouts."""
        scaled_header_spacing = scale_value(self.base_header_spacing, scale_factor)
        scaled_top_section_spacing = scale_value(self.base_top_section_spacing, scale_factor)
        scaled_grid_spacing = scale_value(self.base_grid_spacing, scale_factor)
        scaled_media_spacing = scale_value(self.base_media_spacing, scale_factor)
        scaled_playback_spacing = scale_value(self.base_media_playback_button_spacing, scale_factor)


        # Apply to layouts
        self.main_layout.setContentsMargins(scaled_main_margin, scaled_main_margin, scaled_main_margin, scaled_main_margin)
        self.main_layout.setSpacing(scaled_main_margin) # Or a separate base spacing value

        self.header_layout.setSpacing(scaled_header_spacing)
        self.top_section_layout.setSpacing(scaled_top_section_spacing)
        self.grid_layout.setSpacing(scaled_grid_spacing)
        self.media_layout.setSpacing(scaled_media_spacing)
        self.playback_layout.setSpacing(scaled_playback_spacing)

        # You would scale specific internal widgets here IF needed and not handled by QSS
        # Example (if album art needed explicit scaling):
        # base_art_size = 150
        # scaled_size = scale_value(base_art_size, scale_factor)
        # self.album_art_label.setFixedSize(scaled_size, scaled_size)

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


    def _update_clock(self):
        """Updates the clock label with the current time."""
        current_time = QDateTime.currentDateTime()
        time_str = current_time.toString("HH:mm")
        self.clock_label.setText(time_str)
