#!/usr/bin/env python3

import sys
import os
import pathlib

# Add the project root directory to the Python path
script_dir = pathlib.Path(__file__).parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
from PyQt6.QtCore import Qt

# Import our music player screen
from gui.music_player_screen import MusicPlayerScreen

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set up the main window
        self.setWindowTitle("Music Player Test")
        self.setGeometry(100, 100, 800, 600)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create the music player screen
        self.music_player = MusicPlayerScreen(parent=self)
        layout.addWidget(self.music_player)

        # Set up a dummy audio manager for testing
        self.audio_manager = DummyAudioManager()

        # Set up a dummy bluetooth manager for testing
        self.bluetooth_manager = DummyBluetoothManager()

        # Set up a dummy settings manager for testing
        self.settings_manager = DummySettingsManager()

class DummyAudioManager:
    def get_media_info(self, title, artist):
        # Return dummy cover URL and lyrics
        return None, "No lyrics available for testing"

    def get_volume(self):
        return 50

    def set_volume(self, volume):
        print(f"Setting volume to {volume}")

    def get_mute_status(self):
        return False

    def set_mute(self, mute):
        print(f"Setting mute to {mute}")

class DummyBluetoothManager:
    def __init__(self):
        self.connected_device_path = None
        self.media_player_path = None
        self.playback_status = "stopped"

class DummySettingsManager:
    def get(self, key):
        if key == "developer_mode":
            return True
        return None

def main():
    # Use offscreen mode for testing
    os.environ["QT_QPA_PLATFORM"] = "offscreen"

    # Create the application
    app = QApplication(sys.argv)

    # Create and show the main window
    window = TestWindow()
    window.show()

    print("Test window created. Music player functionality is ready for testing.")
    print("Music library directory:", window.music_player.music_dir)

    # Simulate a song playing
    window.music_player.current_title = "Test Song"
    window.music_player.current_artist = "Test Artist"
    window.music_player.track_title_label.setText("Test Song")
    window.music_player.track_artist_label.setText("Test Artist")

    # Test the download functionality
    print("\nTesting download functionality:")

    # Test 1: yt-dlp not available
    print("1. Testing download with yt-dlp not available")
    # Override the _is_ytdlp_available method to simulate yt-dlp not being installed
    window.music_player._is_ytdlp_available = lambda: False
    # Reset the _is_internet_available method to its original state
    window.music_player._is_internet_available = lambda: True
    window.music_player.download_current_song()
    print("Expected result: A popup should appear saying yt-dlp is not installed")

    # Wait a moment for the popup to be processed
    app.processEvents()

    # Test 2: No internet connection
    print("\n2. Testing download with no internet connection")
    # Override the _is_ytdlp_available method to simulate yt-dlp being installed
    window.music_player._is_ytdlp_available = lambda: True
    # Override the _is_internet_available method to simulate no internet connection
    window.music_player._is_internet_available = lambda: False
    window.music_player.download_current_song()
    print("Expected result: A popup should appear saying no internet connection")

    print("\nPress Ctrl+C to exit")

    # Run the application
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
