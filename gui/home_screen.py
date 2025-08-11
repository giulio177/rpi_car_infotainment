# gui/home_screen.py

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QPushButton,
    QLabel,
    QSpacerItem,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSlot, QUrl
from PyQt6.QtGui import QPixmap
from .symbol_manager import symbol_manager
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

# --- Import scale_value helper ---
try:
    from .styling import scale_value
except ImportError:
    # Fallback if styling.py doesn't have it or import fails
    def scale_value(base, factor):
        return max(1, int(base * factor))


# --- Import ScrollingLabel ---
try:
    from .widgets.scrolling_label import ScrollingLabel
except ImportError:
    print("WARNING: ScrollingLabel not found. Falling back to standard QLabel.")
    ScrollingLabel = QLabel  # Fallback


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
        self.base_media_spacing = 15  # Vertical spacing in media player
        self.base_media_playback_button_spacing = 5

        # --- Network manager for album art ---
        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self.on_album_art_downloaded)

        # --- Current track info ---
        self.current_title = ""
        self.current_artist = ""
        self.default_album_art = QPixmap("assets/default_album_art.png")
        if self.default_album_art.isNull():
            # Create a default album art if the file doesn't exist
            self.default_album_art = QPixmap(100, 100)
            self.default_album_art.fill(Qt.GlobalColor.darkGray)

        # --- Main Layout (Vertical) ---
        self.main_layout = QVBoxLayout(self)
        # Margins/Spacing set by update_scaling

        # --- Top Section Layout (Horizontal: Grid, Media Player) ---
        self.top_section_layout = QHBoxLayout()  # Store reference
        # Spacing set by update_scaling

        # --- 1. Grid Layout for Main Buttons ---
        self.grid_widget = QWidget()
        self.grid_widget.setObjectName("grid_widget")
        self.grid_layout = QGridLayout(self.grid_widget)  # Store reference
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
            ("Settings", "settings-icon.png"),
            ("Logs", "logs-icon.png"),
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
                    button.setSizePolicy(
                        QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
                    )
                    button.setObjectName(f"homeBtn{name.replace(' ', '')}")
                    button.clicked.connect(
                        lambda checked, b=name: self.on_home_button_clicked(b)
                    )
                    self.grid_layout.addWidget(button, r, c)
                    btn_index += 1

        # Vertical spacer to push buttons up within the grid area
        grid_vertical_spacer = QSpacerItem(
            20, 1, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        )
        self.grid_layout.addItem(grid_vertical_spacer, num_rows, 0, 1, target_cols)
        self.grid_widget.setLayout(self.grid_layout)  # Set layout on grid container

        # --- 2. Media Player Section ---
        self.media_widget = QWidget()
        self.media_widget.setObjectName("media_widget")
        self.media_widget.setCursor(
            Qt.CursorShape.PointingHandCursor
        )  # Show hand cursor to indicate clickable
        self.media_widget.mousePressEvent = (
            self.on_media_widget_clicked
        )  # Make the widget clickable
        self.media_layout = QVBoxLayout(self.media_widget)  # Store reference
        # Spacing set by update_scaling
        # Removed AlignTop - Let stretch factor handle vertical distribution

        # Album Art Label (QLabel for displaying album artwork)
        self.album_art_label = QLabel()
        self.album_art_label.setObjectName("albumArtLabel")
        self.album_art_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.album_art_label.setMinimumSize(100, 100)  # Minimum size for album art
        self.album_art_label.setMaximumSize(200, 200)  # Maximum size for album art
        self.album_art_label.setScaledContents(True)  # Scale the image to fit the label
        self.album_art_label.setPixmap(self.default_album_art)
        # Give it a larger stretch factor (e.g., 4 or 5)
        self.media_layout.addWidget(
            self.album_art_label, 0, Qt.AlignmentFlag.AlignHCenter
        )

        # Album Label (Scrolling text for album name)
        self.album_name_label = ScrollingLabel("(Album)")
        self.album_name_label.setObjectName("albumNameLabel")
        self.album_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.media_layout.addWidget(self.album_name_label, 0)

        # Title Label (Scrolling, less vertical space)
        self.track_title_label = ScrollingLabel()
        self.track_title_label.setObjectName("trackTitleLabel")
        self.track_title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.media_layout.addWidget(
            self.track_title_label, 0
        )  # Smaller stretch factor (e.g., 1)

        # Artist Label (Scrolling, less vertical space)
        self.track_artist_label = ScrollingLabel()
        self.track_artist_label.setObjectName("trackArtistLabel")
        self.track_artist_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.media_layout.addWidget(
            self.track_artist_label, 0
        )  # Smaller stretch factor (e.g., 1)

        # Time Label (Standard, minimal vertical space)
        self.track_time_label = QLabel("--:-- / --:--")
        self.track_time_label.setObjectName("trackTimeLabel")
        self.track_time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.media_layout.addWidget(
            self.track_time_label, 0
        )  # Smallest stretch factor (0)

        # --- Playback Controls (Default vertical space) ---
        self.playback_layout = QHBoxLayout()  # Store reference
        # Spacing set by update_scaling
        self.btn_prev = QPushButton()
        self.btn_play_pause = QPushButton()  # Symbol updated by update_playback_status
        self.btn_next = QPushButton()
        self.btn_prev.setObjectName("mediaPrevButton")
        self.btn_play_pause.setObjectName("mediaPlayPauseButton")
        self.btn_next.setObjectName("mediaNextButton")

        # Setup symbols using centralized symbol manager
        symbol_manager.setup_button_symbol(self.btn_prev, "previous")
        symbol_manager.setup_button_symbol(self.btn_play_pause, "play")
        symbol_manager.setup_button_symbol(self.btn_next, "next")

        self.playback_layout.addStretch(1)
        self.playback_layout.addWidget(self.btn_prev)
        self.playback_layout.addWidget(self.btn_play_pause)
        self.playback_layout.addWidget(self.btn_next)
        self.playback_layout.addStretch(1)
        self.media_layout.addLayout(
            self.playback_layout
        )  # Added with default stretch 0

        # --- Test Button for Album Art (Only for development) ---
        self.test_layout = QHBoxLayout()
        self.test_button = QPushButton("Test Album Art")
        self.test_button.setObjectName("testButton")
        self.test_button.clicked.connect(self.test_album_art)
        self.test_layout.addWidget(self.test_button)
        self.media_layout.addLayout(self.test_layout)

        # Hide test button by default, will be shown if developer mode is enabled
        self.test_button.setVisible(False)
        # Check if developer mode is enabled
        if self.main_window and hasattr(self.main_window, "settings_manager"):
            developer_mode = self.main_window.settings_manager.get("developer_mode")
            self.test_button.setVisible(developer_mode)

        # --- Stretch at the end ---
        # This pushes all the above widgets upwards in the media_layout
        self.media_layout.addStretch(1)

        # Connect control buttons
        self.btn_prev.clicked.connect(self.on_previous_clicked)
        self.btn_play_pause.clicked.connect(self.on_play_pause_clicked)
        self.btn_next.clicked.connect(self.on_next_clicked)

        # Removed extra stretch at the end
        self.media_widget.setLayout(self.media_layout)  # Set layout on media container

        # --- Add Grid and Media Player to Top Section with Stretch Factors ---
        # Grid gets 2/3, Media Player gets 1/3 of horizontal space
        self.top_section_layout.addWidget(self.grid_widget, 2)  # Stretch factor 2
        self.top_section_layout.addWidget(self.media_widget, 1)  # Stretch factor 1

        # --- Add Top Section to Main Layout (Stretch=1, takes remaining vertical space) ---
        self.main_layout.addLayout(
            self.top_section_layout, 1
        )  # IMPORTANT: Stretch factor 1

        # --- Initial state ---
        self.clear_media_info()

    def update_scaling(self, scale_factor, scaled_main_margin):
        """Applies scaling to internal layouts."""
        scaled_top_section_spacing = scale_value(
            self.base_top_section_spacing, scale_factor
        )
        scaled_grid_spacing = scale_value(self.base_grid_spacing, scale_factor)
        scaled_media_spacing = scale_value(self.base_media_spacing, scale_factor)
        scaled_playback_spacing = scale_value(
            self.base_media_playback_button_spacing, scale_factor
        )

        # Apply to layouts
        self.main_layout.setContentsMargins(
            scaled_main_margin,
            scaled_main_margin,
            scaled_main_margin,
            scaled_main_margin,
        )
        self.main_layout.setSpacing(
            scaled_main_margin
        )  # Or a separate base spacing value

        self.top_section_layout.setSpacing(scaled_top_section_spacing)
        self.grid_layout.setSpacing(scaled_grid_spacing)
        self.media_layout.setSpacing(scaled_media_spacing)
        self.playback_layout.setSpacing(scaled_playback_spacing)

        # Check if developer mode is enabled and update test button visibility
        if self.main_window and hasattr(self.main_window, "settings_manager"):
            developer_mode = self.main_window.settings_manager.get("developer_mode")
            self.test_button.setVisible(developer_mode)

    @pyqtSlot(dict)
    def update_media_info(self, properties):
        """Updates the media player display based on BT properties."""
        # print("HomeScreen received media properties:", properties) # DEBUG
        track_info = properties.get("Track", {})
        duration_ms = track_info.get("Duration", 0)
        position_ms = properties.get("Position", 0)
        title = track_info.get("Title", "---")
        artist = track_info.get("Artist", "---")
        album = track_info.get("Album", "")

        # Update scrolling labels
        self.track_title_label.setText(title)
        self.track_artist_label.setText(artist)
        self.album_name_label.setText(album if album else "(Album Unknown)")

        # Update time label
        duration_ms = track_info.get("Duration", 0)
        position_ms = properties.get("Position", 0)
        pos_sec = position_ms // 1000
        dur_sec = duration_ms // 1000
        pos_str = f"{pos_sec // 60:02d}:{pos_sec % 60:02d}"
        dur_str = f"{dur_sec // 60:02d}:{dur_sec % 60:02d}" if dur_sec > 0 else "--:--"
        self.track_time_label.setText(f"{pos_str} / {dur_str}")

        # Fetch album art if title or artist changed
        if title != self.current_title or artist != self.current_artist:
            self.current_title = title
            self.current_artist = artist
            self.album_art_label.setPixmap(self.default_album_art)

    @pyqtSlot(str)
    def update_playback_status(self, status):
        """Updates the play/pause button icon based on playback status."""
        print(f"HomeScreen received playback status: {status}")
        if status == "playing":
            symbol_manager.update_button_symbol(self.btn_play_pause, "pause")
        elif status == "paused":
            symbol_manager.update_button_symbol(self.btn_play_pause, "play")
        else:  # stopped, etc.
            symbol_manager.update_button_symbol(self.btn_play_pause, "play")
            # Clear info ONLY if stopped and track info is already present
            if status == "stopped" and self.track_title_label.text() != "---":
                self.clear_media_info()

    
    @pyqtSlot(QPixmap)
    def update_album_art(self, pixmap):
        """
        Questo slot riceve la copertina dell'album direttamente da un'altra schermata (es. MusicPlayerScreen).
        """
        print("[HomeScreen] Ricevuto segnale per aggiornare la copertina.")
        if not pixmap.isNull():
            # Ridimensiona il pixmap per adattarlo alla label della HomeScreen
            # Usiamo self.album_art_label.size() per ottenere le dimensioni attuali,
            # che potrebbero essere state modificate dallo scaling.
            scaled_pixmap = pixmap.scaled(
                self.album_art_label.size(), 
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.album_art_label.setPixmap(scaled_pixmap)
        else:
            self.album_art_label.setPixmap(self.default_album_art)

    @pyqtSlot(int, int)
    def update_position(self, _position, _duration):
        """Updates the position for local playback."""
        # This method is used only for local playback
        # We don't have a time slider in the home screen, but we could update other UI elements if needed
        # Using _ prefix for unused parameters to avoid warnings
        pass

    def clear_media_info(self):
        """Resets media player display to default state."""
        self.track_title_label.setText("---")
        self.track_artist_label.setText("---")
        self.track_time_label.setText("--:-- / --:--")
        self.album_name_label.setText("(No Media)")
        self.album_art_label.setPixmap(self.default_album_art)
        self.btn_play_pause.setText("▶")
        self.current_title = ""
        self.current_artist = ""

    def on_album_art_downloaded(self, reply):
        """Handle downloaded album art"""
        if reply.error() == QNetworkReply.NetworkError.NoError:
            data = reply.readAll()
            pixmap = QPixmap()
            pixmap.loadFromData(data)
            if not pixmap.isNull():
                # Scale the pixmap to fit the label while maintaining aspect ratio
                scaled_pixmap = pixmap.scaled(
                    self.album_art_label.width(),
                    self.album_art_label.height(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.album_art_label.setPixmap(scaled_pixmap)
            else:
                self.album_art_label.setPixmap(self.default_album_art)
        else:
            print(f"Error downloading album art: {reply.errorString()}")
            self.album_art_label.setPixmap(self.default_album_art)
        reply.deleteLater()

    # --- Click Handlers ---
    def on_play_pause_clicked(self):
        print("Play/Pause button clicked")
        # Check if we have a music player screen with local playback
        if (
            self.main_window
            and hasattr(self.main_window, "music_player_screen")
            and self.main_window.music_player_screen.is_local_playback
        ):
            # Forward the command to the music player screen
            self.main_window.music_player_screen.on_play_pause_clicked()
        # Otherwise use Bluetooth
        elif self.main_window and self.main_window.bluetooth_manager:
            current_status = self.main_window.bluetooth_manager.playback_status
            if current_status == "playing":
                self.main_window.bluetooth_manager.send_pause()
            else:
                self.main_window.bluetooth_manager.send_play()
        else:
            print("Error: Cannot send command - No playback system available.")

    def on_next_clicked(self):
        print("Next button clicked")
        # Check if we have a music player screen with local playback
        if (
            self.main_window
            and hasattr(self.main_window, "music_player_screen")
            and self.main_window.music_player_screen.is_local_playback
        ):
            # Forward the command to the music player screen
            self.main_window.music_player_screen.on_next_clicked()
        # Otherwise use Bluetooth
        elif self.main_window and self.main_window.bluetooth_manager:
            self.main_window.bluetooth_manager.send_next()
        else:
            print("Error: Cannot send command - No playback system available.")

    def on_previous_clicked(self):
        print("Previous button clicked")
        # Check if we have a music player screen with local playback
        if (
            self.main_window
            and hasattr(self.main_window, "music_player_screen")
            and self.main_window.music_player_screen.is_local_playback
        ):
            # Forward the command to the music player screen
            self.main_window.music_player_screen.on_previous_clicked()
        # Otherwise use Bluetooth
        elif self.main_window and self.main_window.bluetooth_manager:
            self.main_window.bluetooth_manager.send_previous()
        else:
            print("Error: Cannot send command - No playback system available.")

    # --- Test Album Art ---
    def test_album_art(self):
        """Test function to simulate a song being played and display album art."""
        print("Testing album art functionality...")

        # Create a sample track with known artist and title
        # You can change these to test different songs
        test_songs = [
            {
                "title": "Bohemian Rhapsody",
                "artist": "Queen",
                "album": "A Night at the Opera",
            },
            {"title": "Billie Jean", "artist": "Michael Jackson", "album": "Thriller"},
            {
                "title": "Hotel California",
                "artist": "Eagles",
                "album": "Hotel California",
            },
            {
                "title": "Sweet Child O' Mine",
                "artist": "Guns N' Roses",
                "album": "Appetite for Destruction",
            },
            {"title": "Imagine", "artist": "John Lennon", "album": "Imagine"},
        ]

        import random

        test_song = random.choice(test_songs)

        # Create a mock media properties dictionary
        mock_properties = {
            "Track": {
                "Title": test_song["title"],
                "Artist": test_song["artist"],
                "Album": test_song["album"],
                "Duration": 240000,  # 4 minutes in milliseconds
            },
            "Position": 30000,  # 30 seconds in milliseconds
        }

        # Update the media info with the mock properties
        self.update_media_info(mock_properties)

        # Update the playback status to "playing"
        self.update_playback_status("playing")

        print(
            f"Test song: {test_song['title']} by {test_song['artist']} from {test_song['album']}"
        )

    # --- Navigation and Clock ---
    def on_home_button_clicked(self, button_name):
        """Handle clicks on the main grid buttons and navigate."""
        print(f"Home button clicked: {button_name}")

        if self.main_window is not None and hasattr(self.main_window, "navigate_to"):
            if button_name == "OBD" and hasattr(self.main_window, "obd_screen"):
                self.main_window.navigate_to(self.main_window.obd_screen)

            elif button_name == "Radio" and hasattr(self.main_window, "radio_screen"):
                self.main_window.navigate_to(self.main_window.radio_screen)

            elif button_name == "Settings" and hasattr(self.main_window, "settings_screen"):
                self.main_window.navigate_to(self.main_window.settings_screen)

            elif button_name == "Music" and hasattr(self.main_window, "music_player_screen"):
                self.main_window.navigate_to(self.main_window.music_player_screen)
                
            elif button_name == "Mirroring" and hasattr(self.main_window, "airplay_screen"):
                self.main_window.navigate_to(self.main_window.airplay_screen)
            
            elif button_name == "Logs" and hasattr(self.main_window, "logs_screen"):
                self.main_window.navigate_to(self.main_window.logs_screen)
            # ... other navigation cases ...
            else:
                print(f"No navigation action defined for: {button_name}")
        else:
            print(
                "Error: Could not navigate. Main window reference is invalid or missing 'navigate_to' method."
            )

    def on_media_widget_clicked(self, _event):
        """Handle clicks on the media player widget to open the expanded music player."""
        print("Media widget clicked, opening expanded music player")
        if self.main_window is not None and hasattr(
            self.main_window, "go_to_music_player"
        ):
            self.main_window.go_to_music_player()
        else:
            print(
                "Error: Could not navigate to music player. Main window reference is invalid or missing method."
            )
