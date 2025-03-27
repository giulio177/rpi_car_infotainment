# gui/home_screen.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QPushButton, QLabel, QSpacerItem, QSizePolicy,
                             QSlider)
from PyQt6.QtCore import QTimer, QDateTime, Qt, QSize
from PyQt6.QtGui import QPixmap, QIcon

# REMOVE OR COMMENT OUT THIS LINE:
# from .main_window import MainWindow


class HomeScreen(QWidget):
    def __init__(self, parent=None): # parent is likely MainWindow now
        super().__init__(parent)
        # Store the parent (which should be the MainWindow instance)
        self.main_window = parent

        # --- Main Layout ---
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10) # Add some padding
        self.main_layout.setSpacing(10)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(5, 5, 5, 5) # Adjust margins as needed
        header_layout.setSpacing(10)

        # --- NEW: Header Title Label ---
        # CHANGE "Screen Title" for each screen
        self.header_title_label = QLabel("Home") # e.g., "Home", "OBD-II Data", "FM Radio", "Settings"
        self.header_title_label.setObjectName("headerTitle")
        self.header_title_label.setStyleSheet("font-size: 16pt; font-weight: bold;") # Basic style
        header_layout.addWidget(self.header_title_label)

        # --- NEW: Spacer to push elements right ---
        spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        header_layout.addItem(spacer)
        
        # --- NEW: Clock Label ---
        self.clock_label = QLabel("00:00")
        self.clock_label.setObjectName("headerClock")
        self.clock_label.setStyleSheet("font-size: 16pt;") # Basic style
        header_layout.addWidget(self.clock_label)
        
        # --- NEW: Clock Timer Setup ---
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(10000) # Update every 10 seconds (1000ms = 1 sec) - adjust as needed
        self._update_clock() # Initial update
        
        # --- ADD Header Layout to Main Layout (at the TOP) ---
        self.main_layout.addLayout(header_layout)


        # --- Top Section Layout (Grid + Media Player) ---
        top_section_layout = QHBoxLayout()
        top_section_layout.setSpacing(15)

        # --- 1. Grid Layout for Main Buttons ---
        grid_widget = QWidget() # Container for the grid
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

        rows = 4 # Adjust grid dimensions
        cols = 6
        btn_index = 0
        icon_size = QSize(20, 20) # Adjust icon size as needed

        for r in range(rows):
            for c in range(cols):
                if btn_index < len(buttons_data):
                    name, icon_path = buttons_data[btn_index]
                    button = QPushButton(name) # Keep text for now, add icon later

                    # --- Load Icon (Placeholder - uncomment and provide paths) ---
                    # try:
                    #     icon = QIcon(icon_path)
                    #     if not icon.isNull():
                    #         button.setIcon(icon)
                    #         button.setIconSize(icon_size)
                    #     else:
                    #         # Keep text if icon fails or path is placeholder
                    #         print(f"Warning: Could not load or find icon {icon_path}")
                    #         pass # Keep text
                    # except Exception as e:
                    #     print(f"Error loading icon {icon_path}: {e}")
                    #     pass # Keep text on error

                    # Basic Styling (can be moved to QSS later)
                    button.setMinimumHeight(80) # Make buttons reasonably sized
                    button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                    # button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon) # If using icons+text

                    button.setObjectName(f"homeBtn{name.replace(' ', '')}") # For QSS styling
                    # Connect to the handler
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

        media_layout.addStretch(1) # Push content up

        # Add media widget to the right side of the top section
        top_section_layout.addWidget(media_widget, 1)

        # --- Add Top Section to Main Layout ---
        self.main_layout.addLayout(top_section_layout, 1) # Give it stretch factor

      

    
    def on_home_button_clicked(self, button_name):
        """Handle clicks on the main grid buttons and navigate."""
        print(f"Home button clicked: {button_name}")

        # Check if self.main_window exists AND has the 'navigate_to' method
        if self.main_window is not None and hasattr(self.main_window, 'navigate_to'):
            # Now access screen attributes directly from self.main_window
            if button_name == "OBD" and hasattr(self.main_window, 'obd_screen'):
                self.main_window.navigate_to(self.main_window.obd_screen)
            elif button_name == "Radio" and hasattr(self.main_window, 'radio_screen'):
                self.main_window.navigate_to(self.main_window.radio_screen)
            elif button_name == "Settings" and hasattr(self.main_window, 'settings_screen'):
                self.main_window.navigate_to(self.main_window.settings_screen)
            # Add cases for other buttons...
            elif button_name == "Music":
                 print("Music screen/action not implemented yet.")
            elif button_name == "Telephone":
                 print("Telephone screen/action not implemented yet.")
            elif button_name == "Android Auto":
                 print("Android Auto integration not implemented yet.")
            elif button_name == "Mirroring":
                 print("Mirroring not implemented yet.")
            elif button_name == "Rear Camera":
                 print("Rear Camera switching not implemented yet.")
            elif button_name == "Equalizer":
                 print("Equalizer screen/action not implemented yet.")
            else:
                 print(f"No navigation action defined for: {button_name}")
        else:
            print("Error: Could not navigate. Main window reference is invalid or missing 'navigate_to' method.")
            if self.main_window is None:
                print("Reason: self.main_window is None.")
            elif not hasattr(self.main_window, 'navigate_to'):
                print(f"Reason: Main window object {type(self.main_window)} does not have 'navigate_to' method.")

    def go_to_settings(self):
        """Navigate to the SettingsScreen."""
        print("Settings icon clicked, navigating to settings...")
        if self.main_window is not None and hasattr(self.main_window, 'navigate_to') and hasattr(self.main_window, 'settings_screen'):
            self.main_window.navigate_to(self.main_window.settings_screen)
        else:
            print("Error: Cannot navigate to settings. Main window reference invalid or missing required attributes.")
            if self.main_window is None:
                print("Reason: self.main_window is None.")
            elif not hasattr(self.main_window, 'navigate_to'):
                print(f"Reason: Main window object {type(self.main_window)} does not have 'navigate_to' method.")
            elif not hasattr(self.main_window, 'settings_screen'):
                 print(f"Reason: Main window object {type(self.main_window)} does not have 'settings_screen' attribute.")


    def _update_clock(self):
        """Updates the clock label with the current time."""
        current_time = QDateTime.currentDateTime()
        time_str = current_time.toString("HH:mm") # Format as Hour:Minute
        self.clock_label.setText(time_str)
