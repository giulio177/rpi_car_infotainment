# gui/home_screen.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QPushButton, QLabel, QSpacerItem, QSizePolicy,
                             QSlider)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QIcon

# Try importing MainWindow for type hinting - handle potential circularity if it becomes an issue
try:
    from .main_window import MainWindow
except ImportError:
    MainWindow = None # Or define a placeholder/protocol

class HomeScreen(QWidget):
    def __init__(self, parent=None): # parent is likely MainWindow now
        super().__init__(parent)
        self.main_window = parent # Store reference if needed

        # --- Main Layout ---
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)

        # --- Top Section Layout (Grid + Media Player) ---
        top_section_layout = QHBoxLayout()
        top_section_layout.setSpacing(15)

        # --- 1. Grid Layout for Main Buttons ---
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(10)

        # --- Updated Buttons Data ---
        buttons_data = [
            ("Telephone", "phone-icon.png"),
            ("Android Auto", "android-auto-icon.png"),
            ("OBD", "obd-icon.png"), # Changed from Autobox
            ("Mirroring", "mirroring-icon.png"),
            ("Rear Camera", "camera-icon.png"),
            ("Music", "music-icon.png"),
            ("Radio", "radio-icon.png"), # Changed from Applications
            ("Equalizer", "eq-icon.png"),
            ("Settings", "settings-icon.png") # Added Settings
        ]

        rows = 3
        cols = 3
        btn_index = 0
        icon_size = QSize(48, 48)

        for r in range(rows):
            for c in range(cols):
                if btn_index < len(buttons_data):
                    name, icon_path = buttons_data[btn_index]
                    button = QPushButton(name) # Keep text for now

                    # --- Icon Loading (same as before) ---
                    # icon = QIcon(icon_path)
                    # ... (icon loading logic) ...

                    button.setMinimumHeight(80)
                    button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                    button.setObjectName(f"homeBtn{name.replace(' ', '')}")

                    # Connect to the handler
                    button.clicked.connect(lambda checked, b=name: self.on_home_button_clicked(b))
                    grid_layout.addWidget(button, r, c)
                    btn_index += 1

        top_section_layout.addWidget(grid_widget, 2) # Grid takes more space

        # --- 2. Media Player Section (remains the same) ---
        media_widget = QWidget()
        media_layout = QVBoxLayout(media_widget)
        # ... (Album art, track info, playback controls setup as before) ...
        # Album Art (Placeholder)
        self.album_art_label = QLabel("Album Art")
        self.album_art_label.setMinimumSize(150, 150)
        self.album_art_label.setMaximumSize(250, 250)
        self.album_art_label.setStyleSheet("background-color: #555; color: white; border: 1px solid grey;")
        self.album_art_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        media_layout.addWidget(self.album_art_label, 0, Qt.AlignmentFlag.AlignHCenter)
        # Track Info
        self.track_title_label = QLabel("Track Title")
        self.track_title_label.setStyleSheet("font-weight: bold; font-size: 14pt;")
        self.track_artist_label = QLabel("Artist Name")
        self.track_time_label = QLabel("00:00 / 00:00")
        media_layout.addWidget(self.track_title_label)
        media_layout.addWidget(self.track_artist_label)
        media_layout.addWidget(self.track_time_label)
        # Playback Controls
        playback_layout = QHBoxLayout()
        btn_prev = QPushButton("<<")
        btn_play_pause = QPushButton("▶")
        btn_next = QPushButton(">>")
        playback_layout.addStretch(1)
        playback_layout.addWidget(btn_prev)
        playback_layout.addWidget(btn_play_pause)
        playback_layout.addWidget(btn_next)
        playback_layout.addStretch(1)
        media_layout.addLayout(playback_layout)
        media_layout.addStretch(1)
        top_section_layout.addWidget(media_widget, 1)


        self.main_layout.addLayout(top_section_layout, 1)

        # --- 3. Bottom Control Bar (keep or remove as desired) ---
        # ... (Bottom bar setup as before, maybe remove if redundant now) ...
        bottom_bar_widget = QWidget()
        bottom_bar_layout = QHBoxLayout(bottom_bar_widget)
        bottom_bar_layout.setContentsMargins(5, 5, 5, 5)
        bottom_bar_layout.setSpacing(15)
        btn_settings_icon = QPushButton("⚙️") # Maybe redundant now
        btn_power = QPushButton("🔌")
        volume_slider = QSlider(Qt.Orientation.Horizontal)
        volume_slider.setRange(0, 100); volume_slider.setValue(50); volume_slider.setFixedWidth(150)
        # bottom_bar_layout.addWidget(btn_settings_icon) # REMOVED - Settings is in grid
        bottom_bar_layout.addStretch(1)
        bottom_bar_layout.addWidget(QLabel("Volume:"))
        bottom_bar_layout.addWidget(volume_slider)
        bottom_bar_layout.addStretch(1)
        bottom_bar_layout.addWidget(btn_power)
        self.main_layout.addWidget(bottom_bar_widget)
        bottom_bar_widget.setFixedHeight(60)


    def on_home_button_clicked(self, button_name):
        """Handle clicks on the main grid buttons and navigate."""
        print(f"Home button clicked: {button_name}")

        # Access MainWindow instance (passed as parent during init)
        main_win = self.main_window
        if main_win and isinstance(main_win, MainWindow):
             if button_name == "OBD":
                 main_win.navigate_to(main_win.obd_screen)
             elif button_name == "Radio":
                 main_win.navigate_to(main_win.radio_screen)
             elif button_name == "Settings":
                 main_win.navigate_to(main_win.settings_screen)
             # Add cases for other buttons like Music, Telephone etc.
             elif button_name == "Music":
                  print("Music screen not implemented yet.")
             elif button_name == "Telephone":
                  print("Telephone screen not implemented yet.")
             # ... other buttons ...
             else:
                  print(f"No navigation action defined for: {button_name}")
        elif main_win:
             print(f"Error: Parent window is not MainWindow type ({type(main_win)}). Cannot navigate.")
        else:
             print("Error: Could not find parent window to navigate.")
