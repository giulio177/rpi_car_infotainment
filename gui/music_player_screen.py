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
    QTabWidget,  # Import QTabWidget
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot, pyqtSignal, QUrl
from PyQt6.QtGui import QPixmap
from .symbol_manager import symbol_manager
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
import os
import subprocess
import threading
import socket
import pygame  # Using pygame for audio playback instead of QtMultimedia
import collections  # Import collections for deque
import json  # Import json for history
import datetime  # Import datetime for timestamps

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
            "song_finished": [],
        }
        self._playing = False
        self._current_file = None
        self._seek_offset = 0

    def songFinished(self, callback):
        """Connect a callback to the song finished event."""
        self._callbacks["song_finished"].append(callback)

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

        self._seek_offset = 0

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
                # Se la canzone è in pausa (posizione > 0 e non sta suonando),
                # usa unpause() per riprendere.
                if self._position > 0 and not self._playing:
                    pygame.mixer.music.unpause()
                else:
                    # Altrimenti, avviala dall'inizio.
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
        self._seek_offset = 0

        # Notify position change
        for callback in self._callbacks["position_changed"]:
            callback(0)

        # Notify state change
        for callback in self._callbacks["state_changed"]:
            callback(0)  # 0 = stopped (similar to QMediaPlayer.StoppedState)

    def setPosition(self, position):
        """
        Sets the playback position robustly, handling both playing and paused states.
        This method stops and restarts playback from the new position to ensure accuracy.
        """
        if not self._mixer_available or not self._current_file:
            return

        # Memorizza lo stato di riproduzione attuale (se era in play o in pausa)
        was_playing = self._playing

        # Ferma la musica per garantire un "seek" pulito.
        # Questo resetta il timer interno di pygame.mixer.music.get_pos().
        pygame.mixer.music.stop()

        # Imposta immediatamente la nostra variabile di posizione interna
        self._position = position
        self._seek_offset = position
        position_seconds = position / 1000.0

        # Riavvia la riproduzione dal nuovo punto usando il parametro 'start'.
        # Questo comando funziona anche se intendiamo mettere in pausa subito dopo.
        pygame.mixer.music.play(start=position_seconds)

        # Se prima la musica NON era in riproduzione, mettila in pausa immediatamente.
        # Questo gestisce il caso di spostamento dello slider mentre la musica è ferma.
        if not was_playing:
            pygame.mixer.music.pause()

        # Ripristina lo stato di 'playing' a quello che era prima della chiamata
        self._playing = was_playing

        # Notifica a chi è in ascolto che la posizione è cambiata
        for callback in self._callbacks["position_changed"]:
            callback(self._position)

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
                # La posizione assoluta è l'offset + il tempo trascorso
                self._position = self._seek_offset + elapsed_ms
                
                # Notifica la nuova posizione CORRETTA
                for callback in self._callbacks["position_changed"]:
                    callback(self._position)
        else:
            # Check if playback has ended
            # Controlla se la canzone è finita NATURALMENTE
            if self._playing and not pygame.mixer.music.get_busy():
                print("[PygameMediaPlayer] La canzone è terminata.")
                self._playing = False
                self._position = 0
                self._seek_offset = 0

                # Emetti il nostro nuovo segnale PRIMA di fare altro
                for callback in self._callbacks["song_finished"]:
                    callback()

                # Poi, notifica il cambio di stato generico
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
    album_art_updated = pyqtSignal(QPixmap)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent

        # --- Store base sizes for scaling ---
        self.base_margin = 10
        self.base_spacing = 15
        self.base_button_size = 50
        self.base_album_art_size = 200

        # --- Download Management ---
        self.download_queue = collections.deque()
        self.download_history = []
        self.current_download = None  # Holds info on the active download
        self.history_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "download_history.json"
        )

        # --- Create music & data directories ---
        self.music_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "music/library"
        )
        data_dir = os.path.dirname(self.history_file)
        
        if not os.path.exists(self.music_dir):
            os.makedirs(self.music_dir, exist_ok=True)
        if not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
        print(f"Music library directory: {self.music_dir}")

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
        self.default_album_art = QPixmap("assets/default_album_art.png")
        if self.default_album_art.isNull():
            # Create a default album art if the file doesn't exist
            self.default_album_art = QPixmap(100, 100)
            self.default_album_art.fill(Qt.GlobalColor.lightGray)

        # --- Create media player for local files ---
        self.media_player = PygameMediaPlayer()

        # --- Connect media player signals ---
        self.media_player.positionChanged(self.update_position)
        self.media_player.durationChanged(self.update_duration)
        self.media_player.songFinished(self.play_next_song)

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

        # --- Create main content section ---
        self.main_content = QHBoxLayout()

        # --- Left navigation buttons (LEFTMOST) ---
        self.left_nav_layout = QVBoxLayout()
        self.left_nav_layout.setSpacing(5)

        # Lyrics Button (vertical stack)
        self.lyrics_button = QPushButton("Show Lyrics")
        self.lyrics_button.setObjectName("lyricsButton")
        self.lyrics_button.clicked.connect(self.toggle_lyrics_view)
        self.lyrics_button.setFixedSize(100, 40)
        self.left_nav_layout.addWidget(self.lyrics_button)

        # Library Button (vertical stack)
        self.library_button = QPushButton("Library")
        self.library_button.setObjectName("libraryButton")
        self.library_button.clicked.connect(self.show_library)
        self.library_button.setFixedSize(100, 40)
        self.left_nav_layout.addWidget(self.library_button)

        # Add stretch to push buttons to top
        self.left_nav_layout.addStretch(1)

        # Add left nav to main content
        self.main_content.addLayout(self.left_nav_layout)

        # Add some spacing between nav buttons and content
        self.main_content.addSpacing(10)

        # --- Center content section ---
        self.center_section = QHBoxLayout()

        # --- Track info and controls section (LEFT SIDE OF CENTER) ---
        self.left_side_layout = QVBoxLayout()
        self.left_side_layout.setSpacing(3)  # Reduced from 8 to 3

        # --- Track info section ---
        self.track_info_layout = QVBoxLayout()
        self.track_info_layout.setSpacing(2)  # Reduced from 5 to 2

        # Album Label
        self.album_name_label = ScrollingLabel("(Album)")
        self.album_name_label.setObjectName("albumNameLabel")
        self.album_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.track_info_layout.addWidget(self.album_name_label)

        # Title section with download button
        self.title_section = QHBoxLayout()
        self.title_section.setSpacing(5)  # Reduced from 8 to 5

        # Add stretch to center the title and download button
        self.title_section.addStretch(1)

        # Title Label
        self.track_title_label = ScrollingLabel()
        self.track_title_label.setObjectName("trackTitleLabel")
        self.track_title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_section.addWidget(self.track_title_label)

        # Download Button (bigger, next to title)
        self.download_button = QPushButton()
        self.download_button.setObjectName("downloadButton")
        self.download_button.clicked.connect(self.download_current_song)
        self.download_button.setFixedSize(40, 40)  # Bigger square button
        symbol_manager.setup_button_symbol(self.download_button, "download")
        self.title_section.addWidget(self.download_button)

        # Add stretch to center the title and download button
        self.title_section.addStretch(1)

        self.track_info_layout.addLayout(self.title_section)

        # Artist Label
        self.track_artist_label = ScrollingLabel()
        self.track_artist_label.setObjectName("trackArtistLabel")
        self.track_artist_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.track_info_layout.addWidget(self.track_artist_label)

        # Add track info to left side
        self.left_side_layout.addLayout(self.track_info_layout)

        # --- Playback Controls (centered to align with track info) ---
        self.playback_layout = QHBoxLayout()
        self.btn_prev = QPushButton()
        self.btn_play_pause = QPushButton()
        self.btn_next = QPushButton()
        self.btn_prev.setObjectName("mediaPrevButton")
        self.btn_play_pause.setObjectName("mediaPlayPauseButton")
        self.btn_next.setObjectName("mediaNextButton")

        # Setup symbols using centralized symbol manager
        symbol_manager.setup_button_symbol(self.btn_prev, "previous")
        symbol_manager.setup_button_symbol(self.btn_play_pause, "play")
        symbol_manager.setup_button_symbol(self.btn_next, "next")

        # Center the media controls
        self.playback_layout.addStretch(1)
        self.playback_layout.addWidget(self.btn_prev)
        self.playback_layout.addWidget(self.btn_play_pause)
        self.playback_layout.addWidget(self.btn_next)
        self.playback_layout.addStretch(1)

        # Add playback controls to left side
        self.left_side_layout.addLayout(self.playback_layout)

        # Add left side layout to center section
        self.center_section.addLayout(self.left_side_layout, 1)

        # --- Album art section (RIGHT SIDE OF CENTER) ---
        self.album_art_layout = QVBoxLayout()
        self.album_art_label = QLabel()
        self.album_art_label.setPixmap(self.default_album_art)
        self.album_art_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.album_art_label.setObjectName("albumArtLabel")
        self.album_art_layout.addWidget(self.album_art_label)

        # Add album art to center section
        self.center_section.addLayout(self.album_art_layout)

        # Add center section to main content
        self.main_content.addLayout(self.center_section)

        # --- Add main content to player layout ---
        self.player_layout.addLayout(self.main_content)

        # Add reduced spacing between playback controls and time slider
        self.player_layout.addSpacing(5)  # Reduced from default spacing

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

        # Add reduced spacing between time slider and lyrics
        self.player_layout.addSpacing(5)  # Reduced from default spacing

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

        # Add reduced spacing between lyrics and bottom buttons
        self.player_layout.addSpacing(5)  # Reduced from default spacing

        # --- Button Layout (progress bar) ---
        self.button_layout = QVBoxLayout()  # Vertical to accommodate progress bar
        self.button_layout.setSpacing(5)  # Reduced spacing between button row and progress bar

        # Download Progress Bar
        self.download_progress_layout = QHBoxLayout()
        self.download_progress_bar = QProgressBar()
        self.download_progress_bar.setObjectName("downloadProgressBar")
        self.download_progress_bar.setRange(0, 100)
        self.download_progress_bar.setValue(0)
        self.download_progress_bar.setTextVisible(True)
        self.download_progress_bar.setFormat("Downloading... %p%") # Explicitly set format
        self.download_progress_bar.setVisible(False)  # Hide initially
        self.download_progress_layout.addWidget(self.download_progress_bar)

        # Add progress bar to main button layout
        self.button_layout.addLayout(self.download_progress_layout)

        # Add the complete button layout to player layout
        self.player_layout.addLayout(self.button_layout)

        # --- Create library widget (with Tabs) ---
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
        
        # --- Create Tab Widget ---
        self.library_tab_widget = QTabWidget()
        # Apply system theme to the tab widget itself if possible, though often automatic.
        # You can add custom stylesheet here if needed:
        # self.library_tab_widget.setStyleSheet("QTabWidget::pane { border: 1px solid grey; }") 
        self.library_layout.addWidget(self.library_tab_widget)

        # --- Library Tab ---
        self.library_files_widget = QWidget()
        self.library_files_layout = QVBoxLayout(self.library_files_widget)
        self.library_list = QListWidget()
        self.library_list.setObjectName("libraryList")
        self.library_list.itemClicked.connect(self.play_selected_file)
        self.library_files_layout.addWidget(self.library_list)
        self.library_files_widget.setLayout(self.library_files_layout)
        self.library_tab_widget.addTab(self.library_files_widget, "My Library")

        # --- Downloads Tab ---
        self.downloads_widget = QWidget()
        self.downloads_layout = QVBoxLayout(self.downloads_widget)
        # Apply system theme to the tab content.
        # The default behavior of QWidgets/QListWidgets should align with the system.

        # Queue Section
        self.queue_label = QLabel("Download Queue")
        self.queue_label.setObjectName("downloadQueueLabel")
        self.download_queue_list = QListWidget()
        self.download_queue_list.setObjectName("downloadQueueList")

        # History Section
        self.history_label = QLabel("Download History")
        self.history_label.setObjectName("downloadHistoryLabel")
        self.download_history_list = QListWidget()
        self.download_history_list.setObjectName("downloadHistoryList")

        self.downloads_layout.addWidget(self.queue_label)
        self.downloads_layout.addWidget(self.download_queue_list)
        self.downloads_layout.addWidget(self.history_label)
        self.downloads_layout.addWidget(self.download_history_list, 1)  # Give history more stretch

        self.downloads_widget.setLayout(self.downloads_layout)
        self.library_tab_widget.addTab(self.downloads_widget, "Downloads")

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

        # Connetti il segnale dell'AudioManager a uno slot in questa classe.
        if self.main_window and hasattr(self.main_window, "audio_manager"):
            self.main_window.audio_manager.metadata_ready.connect(self.on_metadata_received)
            
        # Load download history
        self._load_download_history()
        # Initial update of queue UI
        self._update_queue_list_ui()

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
        self.main_content.setSpacing(scaled_spacing)
        self.center_section.setSpacing(scaled_spacing)
        self.left_nav_layout.setSpacing(scaled_spacing)

        # Scale album art
        self.album_art_label.setFixedSize(scaled_album_art_size, scaled_album_art_size)

        # Scale media control buttons
        for btn in [self.btn_prev, self.btn_play_pause, self.btn_next]:
            btn.setFixedSize(scaled_button_size, scaled_button_size)

        # Scale navigation buttons (rectangular, stacked vertically)
        nav_button_width = int(100 * scale_factor)
        nav_button_height = int(40 * scale_factor)
        for btn in [self.lyrics_button, self.library_button]:
            btn.setFixedSize(nav_button_width, nav_button_height)

        # Scale download button (bigger square)
        download_button_size = int(40 * scale_factor)
        self.download_button.setFixedSize(download_button_size, download_button_size)

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

    @pyqtSlot()
    def play_next_song(self):
        """
        Chiamato automaticamente quando una canzone finisce.
        Riproduce la traccia successiva nella libreria, tornando alla prima se è l'ultima.
        """
        print("[MusicPlayerScreen] Canzone finita, avvio la successiva.")
        
        # Funziona solo se stiamo riproducendo dalla libreria locale
        if not self.is_local_playback:
            return

        # Controlla se la libreria è vuota per evitare errori
        num_tracks = self.library_list.count()
        if num_tracks == 0:
            return

        # Calcola l'indice della prossima canzone usando l'operatore modulo.
        # Questo gestisce automaticamente il "ritorno alla prima" (looping).
        # Es: Se ci sono 5 canzoni (indici 0-4) e siamo alla 4,
        # (4 + 1) % 5 = 5 % 5 = 0. Torna alla prima.
        next_index = (self.current_playlist_index + 1) % num_tracks
        
        # Prendi l'elemento della lista corrispondente al nuovo indice
        next_item = self.library_list.item(next_index)

        # Se l'elemento esiste, riproducilo
        if next_item:
            print(f"Riproduco la traccia all'indice: {next_index}")
            self.play_selected_file(next_item)


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
                    self.library_list.addItem(QListWidgetItem("No music files found in library"))
            else:
                os.makedirs(self.music_dir, exist_ok=True)
                self.library_list.addItem(QListWidgetItem("Music library is empty"))
        except Exception as e:
            print(f"Error loading library files: {e}")
            self.library_list.addItem(QListWidgetItem(f"Error: {str(e)}"))

    def scan_directory_for_music(self, directory):
        """Scan a directory for music files recursively."""
        music_extensions = [".mp3", ".wav", ".ogg", ".flac", ".m4a"]
        try:
            for root, _, files in os.walk(directory):
                for file in files:
                    if any(file.lower().endswith(ext) for ext in music_extensions):
                        full_path = os.path.join(root, file)
                        display_name = os.path.basename(file)
                        item = QListWidgetItem(display_name)
                        item.setData(Qt.ItemDataRole.UserRole, full_path)
                        self.library_list.addItem(item)
        except Exception as e:
            print(f"Error scanning directory: {e}")

    def play_selected_file(self, item):
        """Play the selected music file from the library."""

        file_path = item.data(Qt.ItemDataRole.UserRole)
        if not file_path:
            return

        # 1. Avvia la riproduzione (rimane uguale)
        self.current_playlist_index = self.library_list.row(item)
        self.is_local_playback = True
        self.media_player.stop()
        self.media_player.setSource(QUrl.fromLocalFile(file_path))
        self.media_player.play()
        symbol_manager.update_button_symbol(self.btn_play_pause, "pause")

        # --- Aggiornamento preliminare della UI (con valori locali) ---
        filename = os.path.basename(file_path)
        name_parts = os.path.splitext(filename)[0].split(" - ", 1)
        artist, title = (name_parts[0], name_parts[1]) if len(name_parts) > 1 else ("Unknown Artist", name_parts[0])

        self.current_title = title
        self.current_artist = artist
        self.current_album = "Local File"

        self.track_title_label.setText(title)
        self.track_artist_label.setText(artist)
        self.album_name_label.setText("Local File")
        
        # Pulisci immediatamente le informazioni precedenti per evitare di mostrarle
        self.album_art_label.setPixmap(self.default_album_art)
        self.lyrics_content.setText("Loading lyrics...")

        # --- CAMBIO DI SCHERMATA IMMEDIATO ---
        # Questa è la modifica cruciale: torna al player senza attendere la rete.
        self.show_player()

        # 4. MODIFICA CHIAVE: Avvia la richiesta asincrona
        # Questa chiamata ritorna IMMEDIATAMENTE, non blocca nulla.
        if self.main_window and hasattr(self.main_window, "audio_manager"):
            self.main_window.audio_manager.request_media_info(title, artist)

    @pyqtSlot(str, str)
    def on_metadata_received(self, cover_url, lyrics):
        """
        Questo slot viene eseguito nel thread principale quando AudioManager
        emette il segnale 'metadata_ready'. Aggiorna la UI in sicurezza.
        """
        print(f"[UI Thread] Ricevuti metadati. Aggiorno l'interfaccia.")
        
        self.current_lyrics = lyrics if lyrics else "No lyrics available"
        self.parse_lyrics(self.current_lyrics)
        self.update_lyrics_display()

        if cover_url:
            request = QNetworkRequest(QUrl(cover_url))
            self.network_manager.get(request)
        else:
            self.album_art_label.setPixmap(self.default_album_art)
            self.album_art_updated.emit(self.default_album_art)

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
        """Updates the time label while the slider is being dragged."""
        self.current_time_label.setText(self.format_time(position))

    def slider_value_changed(self, _):
        """Called when the slider value changes."""
        # Only update if not being dragged (to avoid conflicts with seek_position)
        if not self.time_slider.isSliderDown():
            # Update lyrics highlighting if lyrics view is active
            if self.lyrics_view_active and self.lyrics_lines:
                self.highlight_current_lyrics_line()

    def slider_released(self):
        """Seeks to the new position when the slider is released."""
        new_position = self.time_slider.value()
        self.current_position_ms = new_position
        
        print(f"Slider released. Seeking to position: {new_position} ms")
        if self.is_local_playback:
            self.media_player.setPosition(new_position)
        else:
            print("Seek in Bluetooth mode not supported.")

        # Aggiorna il testo del tempo per coerenza finale
        self.current_time_label.setText(self.format_time(new_position))

        # Aggiorna l'evidenziazione del testo della canzone, se attivo
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
        pixmap_to_emit = self.default_album_art

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
                pixmap_to_emit = scaled_pixmap
            else:
                self.album_art_label.setPixmap(self.default_album_art)
        else:
            print(f"Error downloading album art: {reply.errorString()}")
            self.album_art_label.setPixmap(self.default_album_art)
        reply.deleteLater()
        self.album_art_updated.emit(pixmap_to_emit)

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
                    cover_url, lyrics = self.main_window.audio_manager.get_media_info(title, artist)
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
            symbol_manager.update_button_symbol(self.btn_play_pause, "pause")
        elif status == "paused":
            symbol_manager.update_button_symbol(self.btn_play_pause, "play")
        else:
            symbol_manager.update_button_symbol(self.btn_play_pause, "play")
            # Clear info ONLY if stopped and track info is already present
            if status == "stopped" and self.track_title_label.text() != "---":
                self.clear_media_info()

    def toggle_lyrics_view(self):
        """Toggle between normal view and lyrics view."""
        self.lyrics_view_active = not self.lyrics_view_active
        if self.lyrics_view_active:
            # Switch to lyrics view - show ONLY title, controls, slider, and lyrics
            self.lyrics_button.setText("Hide Lyrics")

            # Hide everything except essentials
            self.album_art_label.hide()
            self.album_name_label.hide()
            self.track_artist_label.hide()
            self.download_button.hide()
            self.library_button.hide()
            # Keep lyrics button visible so user can exit lyrics view

            # Show lyrics in full space
            self.lyrics_scroll_area.setVisible(True)
            self.lyrics_scroll_area.setMinimumHeight(400)
            self.lyrics_scroll_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

            # Give lyrics area more stretch factor to take up more space
            # Remove and re-add with higher stretch factor
            self.player_layout.removeWidget(self.lyrics_scroll_area)
            self.player_layout.addWidget(self.lyrics_scroll_area, 10)
            self.track_title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.track_title_label.setStyleSheet("font-size: 14pt; font-weight: bold; margin-bottom: 5px; margin-top: 0px;")
            self.left_side_layout.setSpacing(1)
            self.track_info_layout.setSpacing(1)
            self.playback_layout.setSpacing(5)
            if self.lyrics_lines:
                self.highlight_current_lyrics_line()

            print("DEBUG: Switched to lyrics view - showing only title, controls, slider, and lyrics")
        else:
            # Switch back to normal view - restore all elements
            self.lyrics_button.setText("Show Lyrics")

            # Show all hidden elements
            self.album_art_label.show()
            self.album_name_label.show()
            self.track_artist_label.show()
            self.download_button.show()
            self.library_button.show()

            # Hide lyrics
            self.lyrics_scroll_area.setVisible(False)
            self.lyrics_scroll_area.setMinimumHeight(0)
            self.lyrics_scroll_area.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)

            # Reset stretch factor - remove and re-add with normal stretch
            self.player_layout.removeWidget(self.lyrics_scroll_area)
            self.player_layout.addWidget(self.lyrics_scroll_area, 0)
            self.track_title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.track_title_label.setStyleSheet("")

            # Restore normal spacing
            self.left_side_layout.setSpacing(3)  # Back to normal
            self.track_info_layout.setSpacing(2)  # Back to normal
            self.playback_layout.setSpacing(8)  # Back to normal

            print("DEBUG: Switched to normal view - restored all elements")

    def parse_lyrics(self, lyrics_text):
        """Parse lyrics into lines and estimate time positions."""
        self.lyrics_lines = [line.strip() for line in lyrics_text.split("\n") if line.strip()]
        self.current_lyrics_line = 0

        # Estimate time positions for each line (evenly distributed)
        if self.lyrics_lines and self.current_duration_ms > 0:
            # Distribute lines evenly across the song duration
            line_count = len(self.lyrics_lines)
            time_per_line = self.current_duration_ms / line_count
            self.lyrics_line_positions = [int(i * time_per_line) for i in range(line_count)]
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
                line_height = 30
                middle_offset = viewport_height // 2
                scroll_position = max(0, (self.current_lyrics_line * line_height) - middle_offset + (line_height // 2))
                # Set the scroll position
                self.lyrics_scroll_area.verticalScrollBar().setValue(scroll_position)

    def update_lyrics_display(self):
        """Update the lyrics display with highlighted current line."""
        if not self.lyrics_lines:
            self.lyrics_content.setText("No lyrics available")
            return
        html = "<div style='text-align: center;'><div style='height: 100px;'></div>"
        for i, line in enumerate(self.lyrics_lines):
            if i == self.current_lyrics_line:
                # Highlight the current line with blue color, bold text, and larger font
                html += f"<p style='color: #007bff; font-weight: bold; font-size: 140%; margin: 20px 0;'>{line}</p>"
            else:
                # Add more spacing between lines for better readability - bigger font for bigger box
                html += f"<p style='margin: 15px 0; color: #666666; font-size: 110%;'>{line}</p>"
        html += "<div style='height: 100px;'></div></div>"
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
        symbol_manager.update_button_symbol(self.btn_play_pause, "play")
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
        if not self.is_local_playback and self.main_window and self.main_window.bluetooth_manager:
            current_status = self.main_window.bluetooth_manager.playback_status
            if current_status == "playing":
                self.main_window.bluetooth_manager.send_pause()
            else:
                self.main_window.bluetooth_manager.send_play()
        else:
            if self.media_player._playing:
                self.media_player.pause()
                symbol_manager.update_button_symbol(self.btn_play_pause, "play")
                if self.is_local_playback: self.local_playback_status_changed.emit("paused")
            else:
                self.media_player.play()
                symbol_manager.update_button_symbol(self.btn_play_pause, "pause")
                if self.is_local_playback: self.local_playback_status_changed.emit("playing")

    def on_previous_clicked(self):
        """Handle previous button click."""
        if self.is_local_playback:
            # Handle local playback - navigate to previous track in playlist
            if self.current_playlist_index > 0:
                prev_item = self.library_list.item(self.current_playlist_index - 1)
                if prev_item: self.play_selected_file(prev_item)
        elif self.main_window and self.main_window.bluetooth_manager:
            self.main_window.bluetooth_manager.send_previous()

    def on_next_clicked(self):
        """Handle next button click."""
        if self.is_local_playback:
            # Handle local playback - navigate to next track in playlist
            if self.current_playlist_index < self.library_list.count() - 1:
                next_item = self.library_list.item(self.current_playlist_index + 1)
                if next_item: self.play_selected_file(next_item)
        elif self.main_window and self.main_window.bluetooth_manager:
            self.main_window.bluetooth_manager.send_next()

    def download_current_song(self):
        """Adds the currently playing song to the download queue."""
        if not self.current_title or self.current_title == "---":
            QMessageBox.warning(self, "Cannot Download", "Song information is incomplete.")
            return

        song_info = {"title": self.current_title, "artist": self.current_artist, "status": "Queued"}
        
        is_in_queue = any(d['title'] == song_info['title'] and d['artist'] == song_info['artist'] for d in self.download_queue)
        is_in_history = any(h['title'] == song_info['title'] and h['artist'] == song_info['artist'] for h in self.download_history)

        if is_in_queue or is_in_history:
            QMessageBox.information(self, "Already Handled", f"'{song_info['title']}' is already in the queue or history.")
            return

        self.download_queue.append(song_info)
        self._update_queue_list_ui()
        QMessageBox.information(self, "Added to Queue", f"'{song_info['title']}' has been added to the download queue.")
        self._process_download_queue()

    def _process_download_queue(self):
        """Processes the next song in the queue if no download is active."""
        if self.current_download is None and self.download_queue:
            if not self._is_ytdlp_available() or not self._is_ffmpeg_available() or not self._is_internet_available():
                reason = "yt-dlp/ffmpeg is not installed or no internet."
                if not self._is_ytdlp_available(): reason = "yt-dlp is not installed. Please install it with: pip install yt-dlp"
                elif not self._is_ffmpeg_available(): reason = "FFmpeg is not installed. Please install it on your system."
                elif not self._is_internet_available(): reason = "No internet connection."
                
                # If requirements not met, mark the first item as failed and process it.
                song_to_fail = self.download_queue.popleft()
                song_to_fail['status'] = 'Failed'
                self.download_history.insert(0, {**song_to_fail, 'timestamp': datetime.datetime.now().isoformat(), 'error': reason})
                self._save_download_history()
                self._update_history_list_ui()
                self._update_queue_list_ui() # Update queue to remove failed item
                
                QMessageBox.warning(self, "Download Requirement", reason)
                self._process_download_queue() # Try to process the next item
                return

            self.current_download = self.download_queue.popleft()
            self.current_download['status'] = 'Downloading'
            self._update_queue_list_ui()

            self.download_progress_bar.setValue(0)
            self.download_progress_bar.setVisible(True)

            download_thread = threading.Thread(target=self._download_song_thread, args=(self.current_download,))
            download_thread.daemon = True
            download_thread.start()

    def _update_queue_list_ui(self):
        """Refreshes the download queue list widget."""
        self.download_queue_list.clear()
        if self.current_download:
            # Display currently downloading item first
            self.download_queue_list.addItem(f"{self.current_download.get('artist', 'Unknown Artist')} - {self.current_download.get('title', 'Unknown Title')} [Downloading...]")
        # Display remaining queued items
        for song in self.download_queue:
            self.download_queue_list.addItem(f"{song.get('artist', 'Unknown Artist')} - {song.get('title', 'Unknown Title')} [{song.get('status', 'Queued')}]")

    def _update_history_list_ui(self):
        """Refreshes the download history list widget."""
        self.download_history_list.clear()
        for song in self.download_history:
            try:
                ts = datetime.datetime.fromisoformat(song.get('timestamp', '')).strftime('%Y-%m-%d %H:%M')
            except:
                ts = "N/A"
            status_indicator = f"[{song.get('status', 'Unknown')}]" if song.get('status') != 'Completed' else ""
            if song.get('status') == 'Failed':
                status_indicator = f"[Failed: {song.get('error', 'Error')}]"
            self.download_history_list.addItem(f"{song.get('artist', 'Unknown Artist')} - {song.get('title', 'Unknown Title')} {status_indicator} (Downloaded: {ts})")

    def _load_download_history(self):
        """Loads download history from a JSON file."""
        if not os.path.exists(self.history_file): return
        try:
            with open(self.history_file, 'r') as f:
                data = json.load(f)
                # Ensure history is a list and items are dictionaries
                if isinstance(data, list):
                    self.download_history = [item for item in data if isinstance(item, dict)]
                else:
                    self.download_history = [] # Corrupted file, reset
            self._update_history_list_ui()
        except (json.JSONDecodeError, IOError, TypeError) as e:
            print(f"Error loading download history: {e}. Resetting history.")
            self.download_history = [] # Reset on error
            # Optionally, delete corrupted file or log it
            try: os.remove(self.history_file) 
            except OSError: pass


    def _save_download_history(self):
        """Saves download history to a JSON file."""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.download_history, f, indent=4)
        except IOError as e:
            print(f"Error saving download history: {e}")

    def _is_ytdlp_available(self):
        """Check if yt-dlp is installed and available."""
        try:
            # Using capture_output=True for cleaner handling and check=True for error checking
            subprocess.run(["yt-dlp", "--version"], capture_output=True, check=True, timeout=2)
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def _is_internet_available(self):
        """Check if internet connection is available."""
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except OSError:
            return False

    def _is_ffmpeg_available(self):
        """Check if FFmpeg is installed and available."""
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True, timeout=2)
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def _download_song_thread(self, song_info):
        """Background thread for downloading songs."""
        try:
            query = f"{song_info['artist']} - {song_info['title']} audio"
            # Create a safer filename by removing invalid characters
            safe_filename = "".join(c for c in f"{song_info['artist']} - {song_info['title']}" if c.isalnum() or c in " .-_").rstrip()
            output_path = os.path.join(self.music_dir, f"{safe_filename}.%(ext)s")

            expected_filepath = os.path.join(self.music_dir, f"{safe_filename}.mp3")

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
                query,
            ]

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1, # Line buffered
            )
            
            # Read output line by line to parse progress
            for line in iter(process.stdout.readline, ""):
                if "[download]" in line and "%" in line:
                    try:
                        # Extract percentage string and convert to float
                        percent_str = line.split("%")[0].split()[-1]
                        percent = float(percent_str)
                        # Update progress bar in the main thread
                        QTimer.singleShot(0, lambda p=percent: self.update_progress(p))
                    except (ValueError, IndexError):
                        # Ignore lines that don't parse correctly
                        pass 

            # Wait for process to finish and get return code
            return_code = process.wait()

            file_exists = os.path.exists(expected_filepath)

            if return_code == 0 or file_exists:
                # Download succeeded
                self.download_complete(True, song_info)
            else:
                # Download failed, try to get a more specific error message if possible
                error_msg = f"yt-dlp exited with code {return_code}."
                if return_code == 1: error_msg = "No suitable format found or content unavailable."
                elif return_code == 2: error_msg = "Network error occurred."
                elif return_code == 3: error_msg = "Copyright or terms of service violation."
                elif return_code == 4: error_msg = "Download was interrupted."
                elif return_code == 101: error_msg = "Configuration error."
                elif return_code == 102: error_msg = "Internal error."
                
                self.download_complete(False, song_info, error_msg)
        except Exception as e:
            # Catch any exceptions during thread execution
            self.download_complete(False, song_info, f"An unexpected error occurred: {e}")

    def update_progress(self, percent):
        """Update the progress bar value (called from main thread)."""
        self.download_progress_bar.setValue(int(percent))

    def download_complete(self, success, song_info, error_message=None):
        """
        Callback executed when the download thread finishes.
        Schedules the UI update on the main thread.
        """
        QTimer.singleShot(0, lambda: self._update_ui_after_download(success, error_message, song_info))

    def _update_ui_after_download(self, success, error_message, completed_song_info):
        """
        Updates UI elements after download completion (must run on main thread).
        Handles state changes, history logging, and queue processing.
        """
        if success:
            self.download_progress_bar.setValue(100)
            # Hide progress bar after a short delay
            QTimer.singleShot(2000, lambda: self.download_progress_bar.setVisible(False))
            
            # Update status and log to history
            completed_song_info['status'] = 'Completed'
            completed_song_info['timestamp'] = datetime.datetime.now().isoformat()
            self.download_history.insert(0, completed_song_info) # Add to beginning of history
            self._save_download_history()
            self._update_history_list_ui()

            QMessageBox.information(self, "Download Complete", f"Successfully downloaded '{completed_song_info.get('title', 'Unknown Title')}'.")
            
            # Refresh library list if it's visible, so new file can be seen immediately
            if self.stacked_widget.currentWidget() == self.library_widget:
                # Select the correct tab first if needed (Downloads tab might be active)
                current_tab_index = self.library_tab_widget.currentIndex()
                if current_tab_index != 0: # 0 is the index for "My Library"
                    self.library_tab_widget.setCurrentIndex(0) # Switch to Library tab
                self.load_library_files() # Refresh the library

        else:
            # Download failed
            self.download_progress_bar.setVisible(False) # Hide progress bar immediately
            
            QMessageBox.warning(self, "Download Failed", f"Failed to download '{completed_song_info.get('title', 'Unknown Title')}'.\n\nReason: {error_message}")
            
            # Update status to Failed in history
            completed_song_info['status'] = 'Failed'
            completed_song_info['timestamp'] = datetime.datetime.now().isoformat()
            completed_song_info['error'] = error_message # Store error reason
            self.download_history.insert(0, completed_song_info)
            self._save_download_history()
            self._update_history_list_ui()

        # CRITICAL: Reset current_download to None to allow the next download to start
        self.current_download = None
        # Update the UI to reflect the changed queue and processing state
        self._update_queue_list_ui()
        # CRITICAL: Attempt to process the next item in the queue
        self._process_download_queue()