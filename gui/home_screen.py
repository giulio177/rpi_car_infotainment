# gui/home_screen.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QPushButton, QLabel, QSpacerItem, QSizePolicy,
                             QSlider)
from PyQt6.QtCore import Qt, QSize # Import QSize
from PyQt6.QtGui import QPixmap, QIcon # Import QPixmap and QIcon

class HomeScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # --- Main Layout ---
        # Use QVBoxLayout: Top section (Grid + Media) and Bottom Bar
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10) # Add some padding
        self.main_layout.setSpacing(10)

        # --- Top Section Layout (Grid + Media Player) ---
        top_section_layout = QHBoxLayout()
        top_section_layout.setSpacing(15)

        # --- 1. Grid Layout for Main Buttons ---
        grid_widget = QWidget() # Container for the grid
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(10)

        # Placeholder buttons - icons and better styling needed later
        buttons_data = [
            ("Telephone", "phone-icon.png"), # Replace with actual icon paths
            ("Android Auto", "android-auto-icon.png"),
            ("Autobox", "placeholder-icon.png"), # Renamed? OBD?
            ("Mirroring", "mirroring-icon.png"),
            ("Rear Camera", "camera-icon.png"),
            ("Dashboards", "dashboard-icon.png"), # OBD Screen?
            ("Music", "music-icon.png"),
            ("Equalizer", "eq-icon.png"),
            ("Applications", "apps-icon.png")
            # Add or remove as needed
        ]

        rows = 3 # Adjust grid dimensions
        cols = 3
        btn_index = 0
        icon_size = QSize(48, 48) # Adjust icon size as needed

        for r in range(rows):
            for c in range(cols):
                if btn_index < len(buttons_data):
                    name, icon_path = buttons_data[btn_index]
                    button = QPushButton(name) # Keep text for now, add icon later

                    # --- Load Icon ---
                    # icon = QIcon(icon_path) # Load icon from file
                    # if not icon.isNull():
                    #     button.setIcon(icon)
                    #     button.setIconSize(icon_size)
                    # else:
                    #     print(f"Warning: Could not load icon {icon_path}")
                    #     button.setText(name) # Fallback to text

                    # Basic Styling (can be moved to QSS later)
                    button.setMinimumHeight(80) # Make buttons reasonably sized
                    button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                    # button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon) # If using icons+text

                    button.setObjectName(f"homeBtn{name.replace(' ', '')}") # For QSS styling
                    button.clicked.connect(lambda checked, b=name: self.on_home_button_clicked(b))
                    grid_layout.addWidget(button, r, c)
                    btn_index += 1

        # Add grid widget to the left side of the top section
        # Use stretch factor 2 for grid, 1 for media (grid takes 2/3 space)
        top_section_layout.addWidget(grid_widget, 2)

        # --- 2. Media Player Section ---
        media_widget = QWidget()
        media_layout = QVBoxLayout(media_widget)
        media_layout.setSpacing(10)
        media_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Album Art (Placeholder)
        self.album_art_label = QLabel("Album Art")
        self.album_art_label.setMinimumSize(150, 150) # Example size
        self.album_art_label.setMaximumSize(250, 250)
        self.album_art_label.setStyleSheet("background-color: #555; color: white; border: 1px solid grey;")
        self.album_art_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # To set an image:
        # pixmap = QPixmap("path/to/album_art.jpg").scaled(self.album_art_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        # self.album_art_label.setPixmap(pixmap)
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
        btn_prev = QPushButton("<<") # Use Icons later: "⏮" or QIcon
        btn_play_pause = QPushButton("▶") # Use Icons later: "▶" / "⏸" or QIcon
        btn_next = QPushButton(">>") # Use Icons later: "⏭" or QIcon
        playback_layout.addStretch(1)
        playback_layout.addWidget(btn_prev)
        playback_layout.addWidget(btn_play_pause)
        playback_layout.addWidget(btn_next)
        playback_layout.addStretch(1)
        media_layout.addLayout(playback_layout)

        media_layout.addStretch(1) # Push content up

        # Add media widget to the right side of the top section
        top_section_layout.addWidget(media_widget, 1)


        # --- Add Top Section to Main Layout ---
        self.main_layout.addLayout(top_section_layout, 1) # Give it stretch factor


        # --- 3. Bottom Control Bar (Optional - could be in MainWindow instead) ---
        bottom_bar_widget = QWidget()
        bottom_bar_layout = QHBoxLayout(bottom_bar_widget)
        bottom_bar_layout.setContentsMargins(5, 5, 5, 5)
        bottom_bar_layout.setSpacing(15)

        btn_settings = QPushButton("⚙️") # Settings Icon/Button (Placeholder)
        btn_power = QPushButton("🔌")    # Power Icon/Button (Placeholder)
        volume_slider = QSlider(Qt.Orientation.Horizontal)
        volume_slider.setRange(0, 100)
        volume_slider.setValue(50)
        volume_slider.setFixedWidth(150) # Adjust size

        bottom_bar_layout.addWidget(btn_settings)
        bottom_bar_layout.addStretch(1) # Push volume slider to center/right
        bottom_bar_layout.addWidget(QLabel("Volume:"))
        bottom_bar_layout.addWidget(volume_slider)
        bottom_bar_layout.addStretch(1)
        bottom_bar_layout.addWidget(btn_power)

        # --- Add Bottom Bar to Main Layout ---
        self.main_layout.addWidget(bottom_bar_widget)
        # Set fixed height or flexible height for bottom bar?
        bottom_bar_widget.setFixedHeight(60) # Example fixed height


    def on_home_button_clicked(self, button_name):
        """Handle clicks on the main grid buttons."""
        print(f"Home button clicked: {button_name}")
        # --- TODO: Add navigation logic ---
        # Example: Find the main window and switch the stacked widget
        # main_win = self.window() # Get the MainWindow instance
        # if isinstance(main_win, MainWindow): # Check if it's the correct type
        #      if button_name == "Dashboards":
        #          main_win.stacked_widget.setCurrentWidget(main_win.obd_screen)
        #      elif button_name == "Music":
        #          # Need a dedicated Music Screen separate from Radio?
        #          # main_win.stacked_widget.setCurrentWidget(main_win.music_screen)
        #          print("Music screen not implemented yet.")
        #      elif button_name == "Settings": # If you add a settings button here
        #          main_win.stacked_widget.setCurrentWidget(main_win.settings_screen)
        #      # Add other navigation cases...
        # else:
        #      print("Could not find MainWindow to navigate.")


# --- You might need to import MainWindow here if type hinting ---
# from .main_window import MainWindow # Careful with circular imports
