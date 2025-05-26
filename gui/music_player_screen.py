# gui/music_player_screen.py

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QScrollArea,
    QFileDialog,
    QListWidget,
    QListWidgetItem,
    QStackedWidget,
    QMessageBox,
    QProgressBar,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot, pyqtSignal, QUrl
from PyQt6.QtGui import QPixmap
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
import os
import subprocess
import threading
import socket
import pygame  # Using pygame for audio playback instead of QtMultimedia

from .widgets.scrolling_label import ScrollingLabel


class PygameMediaPlayer:
    """A simple media player using pygame.mixer to replace QMediaPlayer."""

    def __init__(self):
        # Initialize pygame mixer with error handling
        try:
            pygame.mixer.init()
            self._mixer_available = True
        except pygame.error as e:
            print(f"Warning: Could not initialize audio mixer: {e}")
            print("Music playback will be disabled.")
            self._mixer_available = False

        self._position = 0
        self._duration = 0
        self._position_timer = None
        self._callbacks = {
            "position_changed": [],
            "duration_changed": [],
            "state_changed": [],
        }
        self._playing = False
        self._current_file = None

    def setSource(self, url):
        """Set the source file to play."""
        if not self._mixer_available:
            print("Audio mixer not available, cannot set source")
            return False

        if hasattr(url, "toLocalFile"):  # Handle QUrl objects
            file_path = url.toLocalFile()
        else:
            file_path = str(url)

        self._current_file = file_path

        # Stop any current playback
        self.stop()

        try:
            # Load the sound file
            pygame.mixer.music.load(file_path)

            # Get duration (this is a bit tricky with pygame)
            sound = pygame.mixer.Sound(file_path)
            duration_seconds = sound.get_length()
            self._duration = int(duration_seconds * 1000)  # Convert to ms

            # Notify duration change
            for callback in self._callbacks["duration_changed"]:
                callback(self._duration)

            return True
        except Exception as e:
            print(f"Error loading audio file: {e}")
            return False

    def play(self):
        """Start playback."""
        if not self._mixer_available:
            print("Audio mixer not available, cannot play")
            return False

        if self._current_file:
            try:
                pygame.mixer.music.play()
                self._playing = True

                # Start position tracking
                if self._position_timer is None:
                    self._position_timer = QTimer()
                    self._position_timer.timeout.connect(self._update_position)
                    self._position_timer.start(
                        50
                    )  # Update every 50ms for smoother tracking

                # Notify state change
                for callback in self._callbacks["state_changed"]:
                    callback(1)  # 1 = playing (similar to QMediaPlayer.PlayingState)

                return True
            except Exception as e:
                print(f"Error playing audio: {e}")
                return False
        return False

    def pause(self):
        """Pause playback."""
        if not self._mixer_available:
            return

        if self._playing:
            pygame.mixer.music.pause()
            self._playing = False

            # Notify state change
            for callback in self._callbacks["state_changed"]:
                callback(2)  # 2 = paused (similar to QMediaPlayer.PausedState)

    def stop(self):
        """Stop playback."""
        if self._mixer_available:
            pygame.mixer.music.stop()
        self._playing = False
        self._position = 0

        # Notify position change
        for callback in self._callbacks["position_changed"]:
            callback(0)

        # Notify state change
        for callback in self._callbacks["state_changed"]:
            callback(0)  # 0 = stopped (similar to QMediaPlayer.StoppedState)

    def setPosition(self, position):
        """Set the playback position in milliseconds."""
        if not self._mixer_available:
            return

        if self._current_file:
            position_seconds = position / 1000.0
            pygame.mixer.music.set_pos(position_seconds)
            self._position = position

            # Notify position change
            for callback in self._callbacks["position_changed"]:
                callback(position)

    def position(self):
        """Get the current playback position in milliseconds."""
        return self._position

    def duration(self):
        """Get the duration of the current media in milliseconds."""
        return self._duration

    def _update_position(self):
        """Update the current position based on pygame's playback."""
        if not self._mixer_available:
            return

        if self._playing and pygame.mixer.music.get_busy():
            # This is an approximation since pygame doesn't provide exact position
            elapsed_ms = pygame.mixer.music.get_pos()
            if elapsed_ms >= 0:
                self._position = elapsed_ms

                # Notify position change
                for callback in self._callbacks["position_changed"]:
                    callback(self._position)
        else:
            # Check if playback has ended
            if self._playing and not pygame.mixer.music.get_busy():
                self._playing = False
                self._position = 0

                # Notify state change
                for callback in self._callbacks["state_changed"]:
                    callback(0)  # 0 = stopped

    def positionChanged(self, callback):
        """Connect a callback to position changes."""
        self._callbacks["position_changed"].append(callback)

    def durationChanged(self, callback):
        """Connect a callback to duration changes."""
        self._callbacks["duration_changed"].append(callback)

    def stateChanged(self, callback):
        """Connect a callback to state changes."""
        self._callbacks["state_changed"].append(callback)

    def playbackState(self):
        """Return the current playback state."""
        if not self._mixer_available:
            return 0  # Stopped if mixer not available

        if self._playing:
            return 1  # Playing
        elif self._position > 0:
            return 2  # Paused
        else:
            return 0  # Stopped


class MusicPlayerScreen(QWidget):
    screen_title = "Music Player"

    # Define signals
    local_playback_started = pyqtSignal(dict)
    local_playback_status_changed = pyqtSignal(str)
    local_playback_position_changed = pyqtSignal(int, int)  # position, duration

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent

        # --- Store base sizes for scaling ---
        self.base_margin = 10
        self.base_spacing = 15
        self.base_button_size = 50
        self.base_album_art_size = 200

        # --- Create music directory ---
        # Use a folder within the project directory instead of ~/Music
        self.music_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "music/library"
        )
        if not os.path.exists(self.music_dir):
            os.makedirs(self.music_dir, exist_ok=True)
        print(f"Music library directory: {self.music_dir}")

        # --- Download status ---
        self.is_downloading = False

        # --- Network manager for album art ---
        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self.on_album_art_downloaded)

        # --- Track current song info ---
        self.current_title = ""
        self.current_artist = ""
        self.current_album = ""
        self.current_duration_ms = 0
        self.current_position_ms = 0
        self.current_lyrics = "No lyrics available"

        # --- Lyrics syncing variables ---
        self.lyrics_lines = []
        self.current_lyrics_line = 0
        self.lyrics_line_positions = []  # Estimated time positions for each line

        # --- Playlist tracking ---
        self.current_playlist_index = -1
        self.is_local_playback = False

        # --- Create default album art ---
        self.default_album_art = QPixmap(
            self.base_album_art_size, self.base_album_art_size
        )
        self.default_album_art.fill(Qt.GlobalColor.darkGray)

        # --- Create media player for local files ---
        self.media_player = PygameMediaPlayer()

        # --- Connect media player signals ---
        self.media_player.positionChanged(self.update_position)
        self.media_player.durationChanged(self.update_duration)

        # --- Create main layout ---
        self.main_layout = QVBoxLayout(self)

        # --- Create stacked widget for player and library views ---
        self.stacked_widget = QStackedWidget()
        self.main_layout.addWidget(self.stacked_widget)

        # --- Create player widget ---
        self.player_widget = QWidget()
        self.player_layout = QVBoxLayout(self.player_widget)

        # --- Track if we're in lyrics view mode ---
        self.lyrics_view_active = False

        # --- Create top section with album art and info ---
        self.top_section = QHBoxLayout()

        # --- Track info and controls section (LEFT SIDE) ---
        self.left_side_layout = QVBoxLayout()

        # --- Track info section ---
        self.track_info_layout = QVBoxLayout()

        # Album Label
        self.album_name_label = ScrollingLabel("(Album)")
        self.album_name_label.setObjectName("albumNameLabel")
        self.album_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.track_info_layout.addWidget(self.album_name_label)

        # Title Label
        self.track_title_label = ScrollingLabel()
        self.track_title_label.setObjectName("trackTitleLabel")
        self.track_title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.track_info_layout.addWidget(self.track_title_label)

        # Artist Label
        self.track_artist_label = ScrollingLabel()
        self.track_artist_label.setObjectName("trackArtistLabel")
        self.track_artist_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.track_info_layout.addWidget(self.track_artist_label)

        # Add track info to left side
        self.left_side_layout.addLayout(self.track_info_layout)

        # --- Playback Controls ---
        self.playback_layout = QHBoxLayout()
        self.btn_prev = QPushButton("<<")
        self.btn_play_pause = QPushButton("▶")
        self.btn_next = QPushButton(">>")
        self.btn_prev.setObjectName("mediaPrevButton")
        self.btn_play_pause.setObjectName("mediaPlayPauseButton")
        self.btn_next.setObjectName("mediaNextButton")

        self.playback_layout.addStretch(1)
        self.playback_layout.addWidget(self.btn_prev)
        self.playback_layout.addWidget(self.btn_play_pause)
        self.playback_layout.addWidget(self.btn_next)
        self.playback_layout.addStretch(1)

        # Add playback controls to left side
        self.left_side_layout.addLayout(self.playback_layout)

        # Add left side layout to top section
        self.top_section.addLayout(
            self.left_side_layout, 1
        )  # Give it stretch factor of 1

        # --- Album art section (RIGHT SIDE) ---
        self.album_art_layout = QVBoxLayout()
        self.album_art_label = QLabel()
        self.album_art_label.setPixmap(self.default_album_art)
        self.album_art_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.album_art_label.setObjectName("albumArtLabel")
        self.album_art_layout.addWidget(self.album_art_label)

        # --- Add album art to top section ---
        self.top_section.addLayout(self.album_art_layout)

        # --- Add top section to player layout ---
        self.player_layout.addLayout(self.top_section)

        # --- Time Slider (below top section, full width) ---
        self.time_slider_layout = QHBoxLayout()
        self.current_time_label = QLabel("00:00")
        self.current_time_label.setObjectName("currentTimeLabel")
        self.time_slider = QSlider(Qt.Orientation.Horizontal)
        self.time_slider.setObjectName("timeSlider")
        self.time_slider.setRange(0, 100)
        self.time_slider.sliderMoved.connect(self.seek_position)
        self.time_slider.sliderPressed.connect(self.slider_pressed)
        self.time_slider.sliderReleased.connect(self.slider_released)
        self.time_slider.valueChanged.connect(self.slider_value_changed)
        self.total_time_label = QLabel("00:00")
        self.total_time_label.setObjectName("totalTimeLabel")
        self.time_slider_layout.addWidget(self.current_time_label)
        self.time_slider_layout.addWidget(self.time_slider)
        self.time_slider_layout.addWidget(self.total_time_label)

        # Add time slider to player layout (full width)
        self.player_layout.addLayout(self.time_slider_layout)

        # --- Lyrics Section ---
        self.lyrics_scroll_area = QScrollArea()
        self.lyrics_scroll_area.setWidgetResizable(True)
        self.lyrics_scroll_area.setObjectName("lyricsScrollArea")

        self.lyrics_content = QLabel(self.current_lyrics)
        self.lyrics_content.setObjectName("lyricsContent")
        self.lyrics_content.setWordWrap(True)
        self.lyrics_content.setTextFormat(
            Qt.TextFormat.RichText
        )  # Enable HTML formatting
        self.lyrics_content.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter
        )

        self.lyrics_scroll_area.setWidget(self.lyrics_content)
        self.player_layout.addWidget(self.lyrics_scroll_area)

        # Initially hide the lyrics area until the user clicks the lyrics button
        self.lyrics_scroll_area.setVisible(False)

        # --- Button Layout ---
        self.button_layout = QVBoxLayout()  # Vertical to accommodate progress bar

        # Button row - all buttons in one horizontal line
        self.button_row = QHBoxLayout()

        # Lyrics Button
        self.lyrics_button = QPushButton("Show Lyrics")
        self.lyrics_button.setObjectName("lyricsButton")
        self.lyrics_button.clicked.connect(self.toggle_lyrics_view)
        self.lyrics_button.setFixedWidth(120)
        self.button_row.addWidget(self.lyrics_button)

        # Library Button
        self.library_button = QPushButton("Library")
        self.library_button.setObjectName("libraryButton")
        self.library_button.clicked.connect(self.show_library)
        self.library_button.setFixedWidth(120)
        self.button_row.addWidget(self.library_button)

        # Download Button
        self.download_button = QPushButton("Download")
        self.download_button.setObjectName("downloadButton")
        self.download_button.clicked.connect(self.download_current_song)
        self.download_button.setFixedWidth(120)
        self.button_row.addWidget(self.download_button)

        # Add stretch to keep buttons compact
        self.button_row.addStretch(1)

        # Add button row to main button layout
        self.button_layout.addLayout(self.button_row)

        # Download Progress Bar
        self.download_progress_layout = QHBoxLayout()
        self.download_progress_bar = QProgressBar()
        self.download_progress_bar.setObjectName("downloadProgressBar")
        self.download_progress_bar.setRange(0, 100)
        self.download_progress_bar.setValue(0)
        self.download_progress_bar.setTextVisible(True)
        self.download_progress_bar.setFormat("%p% - %v of %m")
        self.download_progress_bar.setVisible(False)  # Hide initially
        self.download_progress_layout.addWidget(self.download_progress_bar)

        # Add progress bar to main button layout
        self.button_layout.addLayout(self.download_progress_layout)

        # Add the complete button layout to player layout
        self.player_layout.addLayout(self.button_layout)

        # --- Create library widget ---
        self.library_widget = QWidget()
        self.library_layout = QVBoxLayout(self.library_widget)

        # --- Library header ---
        self.library_header = QHBoxLayout()
        self.library_title = QLabel("Music Library")
        self.library_title.setObjectName("libraryTitle")

        # Back button
        self.back_button = QPushButton("Back to Player")
        self.back_button.setObjectName("backButton")
        self.back_button.clicked.connect(self.show_player)

        # Developer mode button for selecting PC folder
        self.select_folder_button = QPushButton("Select PC Folder")
        self.select_folder_button.setObjectName("selectFolderButton")
        self.select_folder_button.clicked.connect(self.select_pc_folder)
        # Hide by default, will be shown if developer mode is enabled
        self.select_folder_button.setVisible(False)

        self.library_header.addWidget(self.library_title)
        self.library_header.addStretch(1)
        self.library_header.addWidget(self.select_folder_button)
        self.library_header.addWidget(self.back_button)
        self.library_layout.addLayout(self.library_header)

        # --- Library file list ---
        self.library_list = QListWidget()
        self.library_list.setObjectName("libraryList")
        self.library_list.itemDoubleClicked.connect(self.play_selected_file)
        self.library_layout.addWidget(self.library_list)

        # --- Add widgets to stacked widget ---
        self.stacked_widget.addWidget(self.player_widget)
        self.stacked_widget.addWidget(self.library_widget)

        # --- Connect control buttons ---
        self.btn_prev.clicked.connect(self.on_previous_clicked)
        self.btn_play_pause.clicked.connect(self.on_play_pause_clicked)
        self.btn_next.clicked.connect(self.on_next_clicked)

        # --- Timer for updating position ---
        self.position_timer = QTimer(self)
        self.position_timer.setInterval(100)  # Update every 100ms for smoother updates
        self.position_timer.timeout.connect(self.update_time_display)
        self.position_timer.start()

        # --- Initialize UI ---
        self.clear_media_info()
        self.lyrics_view_active = False  # Start in normal view
        self.lyrics_button.setText("Show Lyrics")
        self.lyrics_scroll_area.setVisible(False)
        self.show_player()

    def update_scaling(self, scale_factor, margin):
        """Updates UI element sizes based on the current scale factor."""
        # Scale margins and spacing
        scaled_spacing = int(self.base_spacing * scale_factor)
        scaled_button_size = int(self.base_button_size * scale_factor)
        scaled_album_art_size = int(self.base_album_art_size * scale_factor)

        # Apply scaling to layouts
        self.main_layout.setContentsMargins(margin, margin, margin, margin)
        self.main_layout.setSpacing(scaled_spacing)
        self.player_layout.setSpacing(scaled_spacing)
        self.library_layout.setSpacing(scaled_spacing)

        # Scale album art
        self.album_art_label.setFixedSize(scaled_album_art_size, scaled_album_art_size)

        # Scale buttons
        for btn in [self.btn_prev, self.btn_play_pause, self.btn_next]:
            btn.setFixedSize(scaled_button_size, scaled_button_size)

    def show_player(self):
        """Switch to the player view."""
        # Make sure we're in normal view mode when returning to player
        if self.lyrics_view_active:
            self.toggle_lyrics_view()
        self.stacked_widget.setCurrentWidget(self.player_widget)

    def show_library(self):
        """Switch to the library view and load music files."""
        # Check if developer mode is enabled
        if self.main_window and hasattr(self.main_window, "settings_manager"):
            developer_mode = self.main_window.settings_manager.get("developer_mode")
            self.select_folder_button.setVisible(developer_mode)

        self.load_library_files()
        self.stacked_widget.setCurrentWidget(self.library_widget)

    def select_pc_folder(self):
        """Select a folder from the PC to play music from (developer mode only)."""
        # Check if developer mode is enabled
        if not (
            self.main_window
            and hasattr(self.main_window, "settings_manager")
            and self.main_window.settings_manager.get("developer_mode")
        ):
            QMessageBox.warning(
                self,
                "Developer Mode Required",
                "This feature is only available in developer mode.",
            )
            return

        # Open folder selection dialog
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select Music Folder",
            os.path.expanduser("~"),
            QFileDialog.Option.ShowDirsOnly,
        )

        if folder_path:
            # Scan the selected folder for music files
            self.library_list.clear()
            self.scan_directory_for_music(folder_path)

            # Update the library title to show the selected folder
            folder_name = os.path.basename(folder_path)
            self.library_title.setText(f"Music Library - {folder_name}")

    def load_library_files(self):
        """Load music files from the music directory."""
        # Clear the current list
        self.library_list.clear()

        # Reset the library title
        self.library_title.setText("Music Library")

        try:
            if os.path.exists(self.music_dir):
                self.scan_directory_for_music(self.music_dir)

                # Check if we found any files
                if self.library_list.count() == 0:
                    item = QListWidgetItem("No music files found in library")
                    self.library_list.addItem(item)
            else:
                # If the music directory doesn't exist, create it and add a placeholder item
                os.makedirs(self.music_dir, exist_ok=True)
                item = QListWidgetItem("Music library is empty")
                self.library_list.addItem(item)
        except Exception as e:
            print(f"Error loading library files: {e}")
            item = QListWidgetItem(f"Error: {str(e)}")
            self.library_list.addItem(item)

    def scan_directory_for_music(self, directory):
        """Scan a directory for music files recursively."""
        music_extensions = [".mp3", ".wav", ".ogg", ".flac", ".m4a"]

        try:
            # Use _ for unused variables to avoid warnings
            for root, _, files in os.walk(directory):
                for file in files:
                    if any(file.lower().endswith(ext) for ext in music_extensions):
                        full_path = os.path.join(root, file)
                        display_name = os.path.basename(file)
                        item = QListWidgetItem(display_name)
                        item.setData(
                            Qt.ItemDataRole.UserRole, full_path
                        )  # Store the full path
                        self.library_list.addItem(item)
        except Exception as e:
            print(f"Error scanning directory: {e}")

    def play_selected_file(self, item):
        """Play the selected music file from the library."""
        file_path = item.data(Qt.ItemDataRole.UserRole)
        if file_path:
            # Store current playlist index
            self.current_playlist_index = self.library_list.row(item)

            # Set local playback flag
            self.is_local_playback = True

            # Stop any current playback
            self.media_player.stop()

            # Set the new source
            self.media_player.setSource(QUrl.fromLocalFile(file_path))

            # Start playback
            self.media_player.play()

            # Update UI
            self.btn_play_pause.setText("⏸")

            # Extract metadata from filename
            filename = os.path.basename(file_path)
            name_parts = os.path.splitext(filename)[0].split(" - ", 1)

            if len(name_parts) > 1:
                artist = name_parts[0]
                title = name_parts[1]
            else:
                artist = "Unknown Artist"
                title = name_parts[0]

            # Update current track info
            self.current_title = title
            self.current_artist = artist
            self.current_album = "Local File"

            # Update display
            self.track_title_label.setText(title)
            self.track_artist_label.setText(artist)
            self.album_name_label.setText("Local File")

            # Fetch album art and lyrics
            if self.main_window and hasattr(self.main_window, "audio_manager"):
                cover_url, lyrics = self.main_window.audio_manager.get_media_info(
                    title, artist
                )

                # Update lyrics
                self.current_lyrics = lyrics if lyrics else "No lyrics available"
                self.parse_lyrics(self.current_lyrics)
                self.update_lyrics_display()

                # Download album art
                if cover_url:
                    request = QNetworkRequest(QUrl(cover_url))
                    self.network_manager.get(request)
                else:
                    # Use default album art if no cover URL is available
                    self.album_art_label.setPixmap(self.default_album_art)

            # Emit signal for local playback
            track_info = {
                "Track": {
                    "Title": title,
                    "Artist": artist,
                    "Album": "Local File",
                    "Duration": self.media_player.duration(),
                },
                "Position": self.media_player.position(),
                "IsLocal": True,
                "FilePath": file_path,
            }
            self.local_playback_started.emit(track_info)
            self.local_playback_status_changed.emit("playing")

            # Switch back to player view
            self.show_player()

    def update_position(self, position):
        """Update the current position from the media player."""
        if not self.time_slider.isSliderDown():
            self.time_slider.setValue(position)
        self.current_position_ms = position
        self.update_time_display()

        # Emit signal for local playback position update
        if self.is_local_playback:
            self.local_playback_position_changed.emit(
                position, self.current_duration_ms
            )

    def update_duration(self, duration):
        """Update the total duration from the media player."""
        self.time_slider.setRange(0, duration)
        self.current_duration_ms = duration
        self.update_time_display()

        # Update track info with new duration if it's local playback
        if self.is_local_playback and self.current_title and self.current_artist:
            track_info = {
                "Track": {
                    "Title": self.current_title,
                    "Artist": self.current_artist,
                    "Album": self.current_album,
                    "Duration": duration,
                },
                "Position": self.current_position_ms,
                "IsLocal": True,
            }
            self.local_playback_started.emit(track_info)

    def slider_pressed(self):
        """Called when the slider is pressed."""
        # Store the current position to restore if seeking fails
        self._slider_drag_start_position = self.current_position_ms

    def seek_position(self, position):
        """Seek to the position when the slider is moved."""
        # This is called during slider movement
        self.current_time_label.setText(self.format_time(position))

        # Always update the current position for UI purposes
        self.current_position_ms = position

        # Real-time seeking during drag for local playback
        if self.is_local_playback:
            # Update the media player position in real-time
            self.media_player.setPosition(position)

            # Update lyrics highlighting if lyrics view is active
            if self.lyrics_view_active and self.lyrics_lines:
                self.highlight_current_lyrics_line()

    def slider_value_changed(self, _):
        """Called when the slider value changes."""
        # Only update if not being dragged (to avoid conflicts with seek_position)
        if not self.time_slider.isSliderDown():
            # Update lyrics highlighting if lyrics view is active
            if self.lyrics_view_active and self.lyrics_lines:
                self.highlight_current_lyrics_line()

    def slider_released(self):
        """Set the position when the slider is released."""
        position = self.time_slider.value()

        # Always update the current position for UI purposes
        self.current_position_ms = position

        if (
            self.main_window
            and self.main_window.bluetooth_manager
            and self.main_window.bluetooth_manager.media_player_path
        ):
            # For Bluetooth playback, we would need to implement seeking through D-Bus
            # This is not implemented in the current BluetoothManager
            print("Seeking in Bluetooth playback not implemented")
        else:
            # For local playback
            self.media_player.setPosition(position)

        # Update lyrics highlighting if lyrics view is active
        if self.lyrics_view_active and self.lyrics_lines:
            self.highlight_current_lyrics_line()

    def update_time_display(self):
        """Update the time display labels and sync lyrics if visible."""
        if not self.time_slider.isSliderDown():
            self.current_time_label.setText(self.format_time(self.current_position_ms))
        self.total_time_label.setText(self.format_time(self.current_duration_ms))

        # Update lyrics highlighting if lyrics view is active
        if self.lyrics_view_active and self.lyrics_lines:
            self.highlight_current_lyrics_line()

    def format_time(self, ms):
        """Format milliseconds as MM:SS."""
        seconds = ms // 1000
        minutes = seconds // 60
        seconds %= 60
        return f"{minutes:02d}:{seconds:02d}"

    def on_album_art_downloaded(self, reply):
        """Handle downloaded album art."""
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

    @pyqtSlot(dict)
    def update_media_info(self, properties):
        """Updates the media player display based on BT properties."""
        # Reset local playback flag when Bluetooth media is playing
        self.is_local_playback = False

        track_info = properties.get("Track", {})
        duration_ms = track_info.get("Duration", 0)
        position_ms = properties.get("Position", 0)
        title = track_info.get("Title", "---")
        artist = track_info.get("Artist", "---")
        album = track_info.get("Album", "")

        # Update track information
        self.track_title_label.setText(title)
        self.track_artist_label.setText(artist)
        self.album_name_label.setText(album if album else "(Album Unknown)")

        # Update time information
        self.current_duration_ms = duration_ms
        self.current_position_ms = position_ms
        self.time_slider.setRange(0, duration_ms)
        self.time_slider.setValue(position_ms)
        self.update_time_display()

        # Fetch album art and lyrics if title or artist changed
        if title != self.current_title or artist != self.current_artist:
            self.current_title = title
            self.current_artist = artist
            self.current_album = album

            # Only fetch if we have valid title and artist
            if title != "---" and artist != "---" and self.main_window:
                # Check if we have an audio_manager
                if hasattr(self.main_window, "audio_manager"):
                    cover_url, lyrics = self.main_window.audio_manager.get_media_info(
                        title, artist
                    )

                    # Update lyrics
                    self.current_lyrics = lyrics if lyrics else "No lyrics available"
                    self.parse_lyrics(self.current_lyrics)
                    self.update_lyrics_display()

                    # Download album art
                    if cover_url:
                        request = QNetworkRequest(QUrl(cover_url))
                        self.network_manager.get(request)
                    else:
                        # Use default album art if no cover URL is available
                        self.album_art_label.setPixmap(self.default_album_art)
                else:
                    # Use default album art if no audio_manager is available
                    self.album_art_label.setPixmap(self.default_album_art)
                    self.lyrics_content.setText("No lyrics available")

    @pyqtSlot(str)
    def update_playback_status(self, status):
        """Updates the play/pause button icon based on playback status."""
        if status == "playing":
            self.btn_play_pause.setText("⏸")
        elif status == "paused":
            self.btn_play_pause.setText("▶")
        else:  # stopped, etc.
            self.btn_play_pause.setText("▶")
            # Clear info ONLY if stopped and track info is already present
            if status == "stopped" and self.track_title_label.text() != "---":
                self.clear_media_info()

    def toggle_lyrics_view(self):
        """Toggle between normal view and lyrics view."""
        self.lyrics_view_active = not self.lyrics_view_active

        if self.lyrics_view_active:
            # Switch to lyrics view
            self.lyrics_button.setText("Hide Lyrics")

            # Hide all elements except title
            self.album_art_label.setVisible(False)
            self.album_name_label.setVisible(False)
            self.track_artist_label.setVisible(False)

            # Show lyrics and make it take up more space
            self.lyrics_scroll_area.setVisible(True)

            # Make lyrics scroll area fill the remaining space
            self.lyrics_scroll_area.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
            )
            # Remove any fixed height constraints
            self.lyrics_scroll_area.setMinimumHeight(0)
            self.lyrics_scroll_area.setMaximumHeight(16777215)  # QWIDGETSIZE_MAX

            # Move title to the button row
            # First, remove it from its current layout
            self.track_info_layout.removeWidget(self.track_title_label)
            # Add it to the button row at the beginning
            self.button_row.insertWidget(0, self.track_title_label)
            # Style it appropriately
            self.track_title_label.setAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            )
            self.track_title_label.setStyleSheet(
                "font-size: 14pt; font-weight: bold; margin-right: 20px;"
            )

            # Highlight current lyrics line and scroll to it
            if self.lyrics_lines:
                self.highlight_current_lyrics_line()
        else:
            # Switch back to normal view
            self.lyrics_button.setText("Show Lyrics")

            # Show all elements
            self.album_art_label.setVisible(True)
            self.album_name_label.setVisible(True)
            self.track_artist_label.setVisible(True)
            self.lyrics_scroll_area.setVisible(False)

            # Reset lyrics scroll area size policy
            self.lyrics_scroll_area.setSizePolicy(
                QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred
            )
            self.lyrics_scroll_area.setMinimumHeight(0)
            self.lyrics_scroll_area.setMaximumHeight(16777215)  # QWIDGETSIZE_MAX

            # Move title back to its original position
            # First, remove it from the button row
            self.button_row.removeWidget(self.track_title_label)
            # Add it back to the track info layout at its original position (index 1)
            self.track_info_layout.insertWidget(1, self.track_title_label)
            # Reset alignment and style
            self.track_title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.track_title_label.setStyleSheet("")

    def parse_lyrics(self, lyrics_text):
        """Parse lyrics into lines and estimate time positions."""
        # Split lyrics into lines, filtering out empty lines
        self.lyrics_lines = [
            line.strip() for line in lyrics_text.split("\n") if line.strip()
        ]

        # Reset current line
        self.current_lyrics_line = 0

        # Estimate time positions for each line (evenly distributed)
        if self.lyrics_lines and self.current_duration_ms > 0:
            # Distribute lines evenly across the song duration
            line_count = len(self.lyrics_lines)
            time_per_line = self.current_duration_ms / line_count

            self.lyrics_line_positions = []
            for i in range(line_count):
                # Start each line a bit earlier than its mathematical position
                # to account for singing starting before the exact time point
                position = int(i * time_per_line)
                self.lyrics_line_positions.append(position)
        else:
            self.lyrics_line_positions = []

    def highlight_current_lyrics_line(self):
        """Highlight the current line in the lyrics based on playback position."""
        if not self.lyrics_lines or not self.lyrics_line_positions:
            return

        # Find the current line based on playback position
        current_position = self.current_position_ms
        new_line = 0

        for i, position in enumerate(self.lyrics_line_positions):
            if current_position >= position:
                new_line = i

        # If the line has changed, update the display
        if new_line != self.current_lyrics_line or self.lyrics_view_active:
            self.current_lyrics_line = new_line
            self.update_lyrics_display()

            # Auto-scroll to keep the current line in the vertical middle
            if self.lyrics_view_active:
                # Get the scroll area viewport height
                viewport_height = self.lyrics_scroll_area.viewport().height()

                # Estimate line height (can be adjusted based on font size)
                line_height = 30  # Increased for better spacing

                # Calculate the position to scroll to (center the current line)
                # We want the current line to be in the middle of the viewport
                middle_offset = viewport_height // 2
                scroll_position = max(
                    0,
                    (self.current_lyrics_line * line_height)
                    - middle_offset
                    + (line_height // 2),
                )

                # Set the scroll position
                self.lyrics_scroll_area.verticalScrollBar().setValue(scroll_position)

    def update_lyrics_display(self):
        """Update the lyrics display with highlighted current line."""
        if not self.lyrics_lines:
            self.lyrics_content.setText("No lyrics available")
            return

        # Build HTML with the current line highlighted
        html = "<div style='text-align: center;'>"

        # Add some padding at the top to ensure scrolling works properly
        html += "<div style='height: 100px;'></div>"

        for i, line in enumerate(self.lyrics_lines):
            if i == self.current_lyrics_line:
                # Highlight the current line with blue color, bold text, and larger font
                html += f"<p style='color: #007bff; font-weight: bold; font-size: 120%; margin: 15px 0;'>{line}</p>"
            else:
                # Add more spacing between lines for better readability
                html += f"<p style='margin: 12px 0; color: #666666;'>{line}</p>"

        # Add padding at the bottom too
        html += "<div style='height: 100px;'></div>"
        html += "</div>"

        # Set the HTML content
        self.lyrics_content.setText(html)

    def clear_media_info(self):
        """Resets media player display to default state."""
        self.track_title_label.setText("---")
        self.track_artist_label.setText("---")
        self.album_name_label.setText("(No Media)")
        self.current_time_label.setText("00:00")
        self.total_time_label.setText("00:00")
        self.time_slider.setValue(0)
        self.album_art_label.setPixmap(self.default_album_art)
        self.btn_play_pause.setText("▶")
        self.current_title = ""
        self.current_artist = ""
        self.current_album = ""
        self.current_duration_ms = 0
        self.current_position_ms = 0
        self.current_lyrics = "No lyrics available"
        self.lyrics_lines = []
        self.lyrics_line_positions = []
        self.current_lyrics_line = 0
        self.lyrics_content.setText("No lyrics available")

        # Reset title alignment and style
        self.track_title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.track_title_label.setStyleSheet("")

        # Reset to normal view if in lyrics view
        if self.lyrics_view_active:
            self.toggle_lyrics_view()

    def on_play_pause_clicked(self):
        """Handle play/pause button click."""
        if (
            not self.is_local_playback
            and self.main_window
            and self.main_window.bluetooth_manager
        ):
            # Handle Bluetooth playback
            current_status = self.main_window.bluetooth_manager.playback_status
            if current_status == "playing":
                self.main_window.bluetooth_manager.send_pause()
            else:
                self.main_window.bluetooth_manager.send_play()
        else:
            # Handle local playback
            if self.media_player._playing:  # Check if playing
                self.media_player.pause()
                self.btn_play_pause.setText("▶")
                if self.is_local_playback:
                    self.local_playback_status_changed.emit("paused")
            else:
                self.media_player.play()
                self.btn_play_pause.setText("⏸")
                if self.is_local_playback:
                    self.local_playback_status_changed.emit("playing")

    def on_previous_clicked(self):
        """Handle previous button click."""
        if self.is_local_playback:
            # Handle local playback - navigate to previous track in playlist
            if self.current_playlist_index > 0:
                prev_index = self.current_playlist_index - 1
                prev_item = self.library_list.item(prev_index)
                if prev_item:
                    self.play_selected_file(prev_item)
        elif self.main_window and self.main_window.bluetooth_manager:
            self.main_window.bluetooth_manager.send_previous()

    def on_next_clicked(self):
        """Handle next button click."""
        if self.is_local_playback:
            # Handle local playback - navigate to next track in playlist
            if self.current_playlist_index < self.library_list.count() - 1:
                next_index = self.current_playlist_index + 1
                next_item = self.library_list.item(next_index)
                if next_item:
                    self.play_selected_file(next_item)
        elif self.main_window and self.main_window.bluetooth_manager:
            self.main_window.bluetooth_manager.send_next()

    def download_current_song(self):
        """Download the currently playing song."""
        if self.is_downloading:
            QMessageBox.information(
                self,
                "Download in Progress",
                "A download is already in progress. Please wait.",
            )
            return

        # Check if we have valid song info
        if (
            self.current_title == ""
            or self.current_artist == ""
            or self.current_title == "---"
            or self.current_artist == "---"
        ):
            QMessageBox.warning(
                self,
                "Cannot Download",
                "No song is currently playing or song information is incomplete.",
            )
            return

        # Check if yt-dlp is installed
        if not self._is_ytdlp_available():
            QMessageBox.critical(
                self,
                "Download Not Available",
                "The yt-dlp tool is not installed. Please install it to enable downloads:\n\n"
                "pip install yt-dlp",
            )
            return

        # Check if internet connection is available
        if not self._is_internet_available():
            QMessageBox.warning(
                self,
                "No Internet Connection",
                "Cannot download music. Please check your internet connection and try again.",
            )
            return

        # Reset and show progress bar
        self.download_progress_bar.setValue(0)
        self.download_progress_bar.setVisible(True)

        # Start download in a separate thread
        self.is_downloading = True
        download_thread = threading.Thread(target=self._download_song_thread)
        download_thread.daemon = True
        download_thread.start()

    def _is_ytdlp_available(self):
        """Check if yt-dlp is installed and available."""
        try:
            result = subprocess.run(
                ["yt-dlp", "--version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=2,
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def _is_internet_available(self):
        """Check if internet connection is available."""
        try:
            # Try to connect to Google's DNS server
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except OSError:
            return False

    def _download_song_thread(self):
        """Background thread for downloading songs."""
        try:
            # Show download status
            QTimer.singleShot(0, lambda: self.download_button.setText("Downloading..."))

            # Create search query
            query = f"{self.current_artist} - {self.current_title} audio"

            # Create safe filename
            safe_filename = f"{self.current_artist} - {self.current_title}"
            for char in ["/", "\\", ":", "*", "?", '"', "<", ">", "|"]:
                safe_filename = safe_filename.replace(char, "_")

            output_path = os.path.join(self.music_dir, f"{safe_filename}.%(ext)s")

            # Use yt-dlp to download the song with progress reporting
            cmd = [
                "yt-dlp",
                "--extract-audio",
                "--audio-format",
                "mp3",
                "--audio-quality",
                "0",  # Best quality
                "--output",
                output_path,
                "--no-playlist",
                "--default-search",
                "ytsearch",
                "--newline",  # Important for parsing progress
                "--progress",
                query,
            ]

            # Run the download command with real-time output processing
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
            )

            # Process output line by line to extract progress
            for line in iter(process.stdout.readline, ""):
                # Parse progress information
                if "[download]" in line and "%" in line:
                    try:
                        # Extract percentage
                        percent_str = line.split("%")[0].split()[-1]
                        percent = float(percent_str)
                        # Update progress bar in the main thread
                        QTimer.singleShot(0, lambda p=percent: self.update_progress(p))
                    except (ValueError, IndexError) as e:
                        print(f"Error parsing progress: {e}, line: {line}")

            # Wait for process to complete
            process.stdout.close()
            return_code = process.wait()

            # Check if download was successful
            if return_code == 0:
                # Update UI in the main thread
                self.download_complete(True)
            else:
                error_message = "Download failed"

                # Try to provide more specific error messages based on return code
                if return_code == 1:
                    error_message = "No suitable format found or content unavailable"
                elif return_code == 2:
                    error_message = "Network error occurred during download"
                elif return_code == 3:
                    error_message = "Copyright or terms of service violation detected"

                print(f"Download error: {error_message} (return code {return_code})")
                self.download_complete(False, error_message)

        except FileNotFoundError:
            print("yt-dlp command not found")
            self.download_complete(
                False, "Download tool not found. Please install yt-dlp."
            )
        except subprocess.TimeoutExpired:
            print("Download process timed out")
            self.download_complete(
                False, "Download timed out. Please check your internet connection."
            )
        except Exception as e:
            print(f"Download exception: {str(e)}")
            self.download_complete(False, f"An error occurred: {str(e)}")

    def update_progress(self, percent):
        """Update the progress bar (called from main thread)."""
        self.download_progress_bar.setValue(int(percent))

    def download_complete(self, success, error_message=None):
        """Called when download completes (from any thread)."""
        # Schedule UI update on the main thread
        QTimer.singleShot(
            0, lambda: self._update_ui_after_download(success, error_message)
        )

    def _update_ui_after_download(self, success, error_message=None):
        """Update UI after download (must be called on main thread)."""
        self.is_downloading = False
        self.download_button.setText("Download Song")

        # Set progress to 100% if successful, hide after a delay
        if success:
            self.download_progress_bar.setValue(100)
            QTimer.singleShot(
                3000, lambda: self.download_progress_bar.setVisible(False)
            )

            # Show success message with file location
            file_location = os.path.basename(self.music_dir)
            QMessageBox.information(
                self,
                "Download Complete",
                f"Successfully downloaded '{self.current_title}' by {self.current_artist}.\n\n"
                f"The file has been saved to the {file_location} folder.",
            )

            # Refresh the library if it's currently shown
            if self.stacked_widget.currentWidget() == self.library_widget:
                self.load_library_files()
        else:
            # Hide progress bar immediately on failure
            self.download_progress_bar.setVisible(False)

            # Show appropriate error message
            title = "Download Failed"
            message = (
                error_message
                if error_message
                else "Unknown error occurred during download"
            )

            # Add suggestion based on error type
            if (
                "network" in message.lower()
                or "connection" in message.lower()
                or "timeout" in message.lower()
            ):
                message += "\n\nPlease check your internet connection and try again."
            elif "not found" in message.lower() or "install" in message.lower():
                message += (
                    "\n\nPlease install the required tool with: pip install yt-dlp"
                )
            elif "copyright" in message.lower() or "terms" in message.lower():
                message += "\n\nThis content may be protected by copyright."

            QMessageBox.warning(self, title, message)
