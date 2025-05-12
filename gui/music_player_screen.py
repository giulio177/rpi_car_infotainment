# gui/music_player_screen.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QPushButton, QSlider, QScrollArea, QFileDialog,
                            QListWidget, QListWidgetItem, QStackedWidget, QMessageBox)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot, pyqtSignal, QUrl
from PyQt6.QtGui import QPixmap
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
import os
import subprocess
import threading
import time

from .widgets.scrolling_label import ScrollingLabel

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
        self.music_dir = os.path.expanduser("~/Music")
        if not os.path.exists(self.music_dir):
            os.makedirs(self.music_dir)

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

        # --- Playlist tracking ---
        self.current_playlist_index = -1
        self.is_local_playback = False

        # --- Create default album art ---
        self.default_album_art = QPixmap(self.base_album_art_size, self.base_album_art_size)
        self.default_album_art.fill(Qt.GlobalColor.darkGray)

        # --- Create media player for local files ---
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)

        # --- Connect media player signals ---
        self.media_player.positionChanged.connect(self.update_position)
        self.media_player.durationChanged.connect(self.update_duration)

        # --- Create main layout ---
        self.main_layout = QVBoxLayout(self)

        # --- Create stacked widget for player and library views ---
        self.stacked_widget = QStackedWidget()
        self.main_layout.addWidget(self.stacked_widget)

        # --- Create player widget ---
        self.player_widget = QWidget()
        self.player_layout = QVBoxLayout(self.player_widget)

        # --- Create top section with album art and info ---
        self.top_section = QHBoxLayout()

        # --- Album art section ---
        self.album_art_layout = QVBoxLayout()
        self.album_art_label = QLabel()
        self.album_art_label.setPixmap(self.default_album_art)
        self.album_art_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.album_art_label.setObjectName("albumArtLabel")
        self.album_art_layout.addWidget(self.album_art_label)

        # --- Add album art to top section ---
        self.top_section.addLayout(self.album_art_layout)

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

        # Time Slider
        self.time_slider_layout = QHBoxLayout()
        self.current_time_label = QLabel("00:00")
        self.current_time_label.setObjectName("currentTimeLabel")
        self.time_slider = QSlider(Qt.Orientation.Horizontal)
        self.time_slider.setObjectName("timeSlider")
        self.time_slider.setRange(0, 100)
        self.time_slider.sliderMoved.connect(self.seek_position)
        self.time_slider.sliderReleased.connect(self.slider_released)
        self.total_time_label = QLabel("00:00")
        self.total_time_label.setObjectName("totalTimeLabel")
        self.time_slider_layout.addWidget(self.current_time_label)
        self.time_slider_layout.addWidget(self.time_slider)
        self.time_slider_layout.addWidget(self.total_time_label)
        self.track_info_layout.addLayout(self.time_slider_layout)

        # --- Add track info to top section ---
        self.top_section.addLayout(self.track_info_layout)

        # --- Add top section to player layout ---
        self.player_layout.addLayout(self.top_section)

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

        # --- Add playback controls to player layout ---
        self.player_layout.addLayout(self.playback_layout)

        # --- Lyrics Section ---
        self.lyrics_label = QLabel("Lyrics")
        self.lyrics_label.setObjectName("lyricsLabel")
        self.lyrics_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.player_layout.addWidget(self.lyrics_label)

        self.lyrics_scroll_area = QScrollArea()
        self.lyrics_scroll_area.setWidgetResizable(True)
        self.lyrics_scroll_area.setObjectName("lyricsScrollArea")

        self.lyrics_content = QLabel(self.current_lyrics)
        self.lyrics_content.setObjectName("lyricsContent")
        self.lyrics_content.setWordWrap(True)
        self.lyrics_content.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        self.lyrics_scroll_area.setWidget(self.lyrics_content)
        self.player_layout.addWidget(self.lyrics_scroll_area)

        # --- Button Layout ---
        self.button_layout = QHBoxLayout()

        # Library Button
        self.library_button = QPushButton("Library")
        self.library_button.setObjectName("libraryButton")
        self.library_button.clicked.connect(self.show_library)
        self.button_layout.addWidget(self.library_button)

        # Download Button
        self.download_button = QPushButton("Download Song")
        self.download_button.setObjectName("downloadButton")
        self.download_button.clicked.connect(self.download_current_song)
        self.button_layout.addWidget(self.download_button)

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
        self.position_timer.setInterval(1000)  # Update every second
        self.position_timer.timeout.connect(self.update_time_display)
        self.position_timer.start()

        # --- Initialize UI ---
        self.clear_media_info()
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
        self.stacked_widget.setCurrentWidget(self.player_widget)

    def show_library(self):
        """Switch to the library view and load music files."""
        # Check if developer mode is enabled
        if self.main_window and hasattr(self.main_window, 'settings_manager'):
            developer_mode = self.main_window.settings_manager.get("developer_mode")
            self.select_folder_button.setVisible(developer_mode)

        self.load_library_files()
        self.stacked_widget.setCurrentWidget(self.library_widget)

    def select_pc_folder(self):
        """Select a folder from the PC to play music from (developer mode only)."""
        # Check if developer mode is enabled
        if not (self.main_window and hasattr(self.main_window, 'settings_manager') and
                self.main_window.settings_manager.get("developer_mode")):
            QMessageBox.warning(self, "Developer Mode Required",
                               "This feature is only available in developer mode.")
            return

        # Open folder selection dialog
        folder_path = QFileDialog.getExistingDirectory(self, "Select Music Folder",
                                                      os.path.expanduser("~"),
                                                      QFileDialog.Option.ShowDirsOnly)

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
        music_extensions = ['.mp3', '.wav', '.ogg', '.flac', '.m4a']

        try:
            # Use _ for unused variables to avoid warnings
            for root, _, files in os.walk(directory):
                for file in files:
                    if any(file.lower().endswith(ext) for ext in music_extensions):
                        full_path = os.path.join(root, file)
                        display_name = os.path.basename(file)
                        item = QListWidgetItem(display_name)
                        item.setData(Qt.ItemDataRole.UserRole, full_path)  # Store the full path
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
            name_parts = os.path.splitext(filename)[0].split(' - ', 1)

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
            if self.main_window and hasattr(self.main_window, 'audio_manager'):
                cover_url, lyrics = self.main_window.audio_manager.get_media_info(title, artist)

                # Update lyrics
                self.current_lyrics = lyrics if lyrics else "No lyrics available"
                self.lyrics_content.setText(self.current_lyrics)

                # Download album art
                if cover_url:
                    request = QNetworkRequest(QUrl(cover_url))
                    self.network_manager.get(request)
                else:
                    # Use default album art if no cover URL is available
                    self.album_art_label.setPixmap(self.default_album_art)

            # Emit signal for local playback
            track_info = {
                'Track': {
                    'Title': title,
                    'Artist': artist,
                    'Album': 'Local File',
                    'Duration': self.media_player.duration()
                },
                'Position': self.media_player.position(),
                'IsLocal': True,
                'FilePath': file_path
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
            self.local_playback_position_changed.emit(position, self.current_duration_ms)

    def update_duration(self, duration):
        """Update the total duration from the media player."""
        self.time_slider.setRange(0, duration)
        self.current_duration_ms = duration
        self.update_time_display()

        # Update track info with new duration if it's local playback
        if self.is_local_playback and self.current_title and self.current_artist:
            track_info = {
                'Track': {
                    'Title': self.current_title,
                    'Artist': self.current_artist,
                    'Album': self.current_album,
                    'Duration': duration
                },
                'Position': self.current_position_ms,
                'IsLocal': True
            }
            self.local_playback_started.emit(track_info)

    def seek_position(self, position):
        """Seek to the position when the slider is moved."""
        # This is called during slider movement
        self.current_time_label.setText(self.format_time(position))

    def slider_released(self):
        """Set the position when the slider is released."""
        position = self.time_slider.value()
        if self.main_window and self.main_window.bluetooth_manager and self.main_window.bluetooth_manager.media_player_path:
            # For Bluetooth playback, we would need to implement seeking through D-Bus
            # This is not implemented in the current BluetoothManager
            print("Seeking in Bluetooth playback not implemented")
        else:
            # For local playback
            self.media_player.setPosition(position)

    def update_time_display(self):
        """Update the time display labels."""
        if not self.time_slider.isSliderDown():
            self.current_time_label.setText(self.format_time(self.current_position_ms))
        self.total_time_label.setText(self.format_time(self.current_duration_ms))

    def format_time(self, ms):
        """Format milliseconds as MM:SS."""
        seconds = ms // 1000
        minutes = seconds // 60
        seconds %= 60
        return f"{minutes:02d}:{seconds:02d}"

    def on_album_art_downloaded(self, reply):
        """Handle downloaded album art."""
        if reply.error():
            print(f"Error downloading album art: {reply.errorString()}")
            self.album_art_label.setPixmap(self.default_album_art)
            return

        # Read the image data
        img_data = reply.readAll()
        pixmap = QPixmap()
        pixmap.loadFromData(img_data)

        # Scale the pixmap to fit the label
        scaled_pixmap = pixmap.scaled(
            self.album_art_label.width(),
            self.album_art_label.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        # Set the pixmap
        self.album_art_label.setPixmap(scaled_pixmap)

    @pyqtSlot(dict)
    def update_media_info(self, properties):
        """Updates the media player display based on BT properties."""
        # Reset local playback flag when Bluetooth media is playing
        self.is_local_playback = False

        track_info = properties.get('Track', {})
        duration_ms = track_info.get('Duration', 0)
        position_ms = properties.get('Position', 0)
        title = track_info.get('Title', "---")
        artist = track_info.get('Artist', "---")
        album = track_info.get('Album', "")

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
                if hasattr(self.main_window, 'audio_manager'):
                    cover_url, lyrics = self.main_window.audio_manager.get_media_info(title, artist)

                    # Update lyrics
                    self.current_lyrics = lyrics if lyrics else "No lyrics available"
                    self.lyrics_content.setText(self.current_lyrics)

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
        self.lyrics_content.setText("No lyrics available")

    def on_play_pause_clicked(self):
        """Handle play/pause button click."""
        if not self.is_local_playback and self.main_window and self.main_window.bluetooth_manager:
            # Handle Bluetooth playback
            current_status = self.main_window.bluetooth_manager.playback_status
            if current_status == "playing":
                self.main_window.bluetooth_manager.send_pause()
            else:
                self.main_window.bluetooth_manager.send_play()
        else:
            # Handle local playback
            if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
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
            QMessageBox.information(self, "Download in Progress", "A download is already in progress. Please wait.")
            return

        # Check if we have valid song info
        if self.current_title == "" or self.current_artist == "" or self.current_title == "---" or self.current_artist == "---":
            QMessageBox.warning(self, "Cannot Download", "No song is currently playing or song information is incomplete.")
            return

        # Start download in a separate thread
        self.is_downloading = True
        download_thread = threading.Thread(target=self._download_song_thread)
        download_thread.daemon = True
        download_thread.start()

    def _download_song_thread(self):
        """Background thread for downloading songs."""
        try:
            # Show download status
            self.download_button.setText("Downloading...")

            # Create search query
            query = f"{self.current_artist} - {self.current_title} audio"

            # Create safe filename
            safe_filename = f"{self.current_artist} - {self.current_title}"
            for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']:
                safe_filename = safe_filename.replace(char, '_')

            output_path = os.path.join(self.music_dir, f"{safe_filename}.%(ext)s")

            # Use yt-dlp to download the song
            cmd = [
                "yt-dlp",
                "--extract-audio",
                "--audio-format", "mp3",
                "--audio-quality", "0",  # Best quality
                "--output", output_path,
                "--no-playlist",
                "--default-search", "ytsearch",
                "--quiet",
                query
            ]

            # Run the download command
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            _, stderr = process.communicate()  # Use _ for unused stdout

            # Check if download was successful
            if process.returncode == 0:
                # Update UI in the main thread
                self.download_complete(True)
            else:
                print(f"Download error: {stderr.decode()}")
                self.download_complete(False, stderr.decode())

        except Exception as e:
            print(f"Download exception: {str(e)}")
            self.download_complete(False, str(e))

    def download_complete(self, success, error_message=None):
        """Called when download completes (from any thread)."""
        # Schedule UI update on the main thread
        QTimer.singleShot(0, lambda: self._update_ui_after_download(success, error_message))

    def _update_ui_after_download(self, success, error_message=None):
        """Update UI after download (must be called on main thread)."""
        self.is_downloading = False
        self.download_button.setText("Download Song")

        if success:
            QMessageBox.information(self, "Download Complete",
                                   f"Successfully downloaded '{self.current_title}' by {self.current_artist}.")
            # Refresh the library if it's currently shown
            if self.stacked_widget.currentWidget() == self.library_widget:
                self.load_library_files()
        else:
            QMessageBox.warning(self, "Download Failed",
                               f"Failed to download the song: {error_message if error_message else 'Unknown error'}")
