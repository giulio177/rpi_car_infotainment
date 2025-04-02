# gui/home_screen.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QPushButton, QLabel, QSpacerItem, QSizePolicy,
                             QSlider)
# Import QSize and Qt for alignment flags
from PyQt6.QtCore import QTimer, QDateTime, Qt, QSize
from PyQt6.QtGui import QPixmap, QIcon

# REMOVE OR COMMENT OUT THIS LINE (if present):
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

        # --- Header Layout (No changes needed here) ---
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(5, 5, 5, 5)
        header_layout.setSpacing(10)
        self.header_title_label = QLabel("Home")
        self.header_title_label.setObjectName("headerTitle")
        self.header_title_label.setStyleSheet("font-size: 16pt; font-weight: bold;")
        header_layout.addWidget(self.header_title_label)
        spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        header_layout.addItem(spacer)
        self.clock_label = QLabel("00:00")
        self.clock_label.setObjectName("headerClock")
        self.clock_label.setStyleSheet("font-size: 16pt;")
        header_layout.addWidget(self.clock_label)
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(10000)
        self._update_clock()
        self.main_layout.addLayout(header_layout)
        # --- End Header ---

        # --- Top Section Layout (Grid + Media Player) ---
        top_section_layout = QHBoxLayout()
        top_section_layout.setSpacing(15) # Keep spacing between grid and media player

        # --- 1. Grid Layout for Main Buttons ---
        grid_widget = QWidget() # Container for the grid
        grid_layout = QGridLayout(grid_widget)
        # Adjust spacing between buttons in the grid if needed
        grid_layout.setSpacing(8) # Smaller spacing between buttons
        # grid_layout.setHorizontalSpacing(5)
        # grid_layout.setVerticalSpacing(5)

        # --- Button Data (Ensure you have enough for 5x4=20, or handle fewer) ---
        # Example: If you only have 9, it will only fill the first 9 slots.
        buttons_data = [
            ("Telephone", "phone-icon.png"),
            ("Android Auto", "android-auto-icon.png"),
            ("OBD", "obd-icon.png"),
            ("Mirroring", "mirroring-icon.png"),
            ("Rear Camera", "camera-icon.png"),
            # --- Start Row 2 ---
            ("Music", "music-icon.png"),
            ("Radio", "radio-icon.png"),
            ("Equalizer", "eq-icon.png"),
            ("Settings", "settings-icon.png"),
            ("Placeholder 1", "placeholder1.png"), # Add placeholders or real buttons
            # --- Start Row 3 ---
            ("Placeholder 2", "placeholder2.png"),
            ("Placeholder 3", "placeholder3.png"),
            ("Placeholder 4", "placeholder4.png"),
            ("Placeholder 5", "placeholder5.png"),
            ("Placeholder 6", "placeholder6.png"),
            # --- Start Row 4 ---
            ("Placeholder 7", "placeholder7.png"),
            ("Placeholder 8", "placeholder8.png"),
            ("Placeholder 9", "placeholder9.png"),
            ("Placeholder 10", "placeholder10.png"),
            ("Placeholder 11", "placeholder11.png"),
        ]

        # --- Define Grid Dimensions and Button Size ---
        target_rows = 4
        target_cols = 5
        # Define the fixed size for each button (Width, Height) - Adjust as needed!
        button_fixed_size = QSize(110, 45) # Example: Smaller rectangular size
        # icon_size = QSize(20, 20) # Keep icon size if you add icons later

        btn_index = 0
        for r in range(target_rows):
            for c in range(target_cols):
                if btn_index < len(buttons_data):
                    name, icon_path = buttons_data[btn_index]
                    button = QPushButton(name)

                    # --- Set FIXED Size ---
                    button.setFixedSize(button_fixed_size)

                    # --- Remove Expanding Size Policy ---
                    # button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding) # REMOVE this line

                    # Optional: Load Icon (Keep your icon loading logic if needed)
                    # try:
                    #     icon = QIcon(f"assets/icons/{icon_path}") # Assuming icons are in assets/icons/
                    #     if not icon.isNull():
                    #         button.setIcon(icon)
                    #         button.setIconSize(icon_size)
                    #     else:
                    #         print(f"Warning: Could not load or find icon {icon_path}")
                    # except Exception as e:
                    #     print(f"Error loading icon {icon_path}: {e}")

                    button.setObjectName(f"homeBtn{name.replace(' ', '')}")
                    button.clicked.connect(lambda checked, b=name: self.on_home_button_clicked(b))

                    # --- Add widget to grid layout WITH alignment ---
                    # This ensures the fixed-size button sits top-left within its grid cell
                    grid_layout.addWidget(button, r, c, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

                    btn_index += 1
                else:
                    # Optional: If you have fewer buttons than grid slots, you can break
                    # or add empty spacers if you want to maintain grid structure
                    # Example: add an empty spacer
                    # grid_layout.addItem(QSpacerItem(button_fixed_size.width(), button_fixed_size.height(), QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed), r, c)
                    pass # Or just do nothing, leaving grid cells empty

        # --- Adjust how the grid_widget itself behaves in the QHBoxLayout ---
        # Option 1: Make the grid widget take only its preferred size
        grid_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        # Option 2: (Alternative) Set Maximum size if Preferred is too large
        # grid_widget.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)

        # Add grid widget to the left side of the top section (NO stretch factor here)
        top_section_layout.addWidget(grid_widget) # Removed stretch factor '2'

        # --- 2. Media Player Section (No changes needed here) ---
        media_widget = QWidget()
        media_layout = QVBoxLayout(media_widget)
        media_layout.setSpacing(10)
        media_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.album_art_label = QLabel("Album Art")
        self.album_art_label.setMinimumSize(150, 150)
        self.album_art_label.setMaximumSize(200, 200) # Maybe slightly smaller media player?
        self.album_art_label.setStyleSheet("background-color: #555; color: white; border: 1px solid grey;")
        self.album_art_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        media_layout.addWidget(self.album_art_label, 0, Qt.AlignmentFlag.AlignHCenter)
        self.track_title_label = QLabel("Track Title")
        self.track_title_label.setStyleSheet("font-weight: bold; font-size: 14pt;")
        self.track_artist_label = QLabel("Artist Name")
        self.track_time_label = QLabel("00:00 / 00:00")
        media_layout.addWidget(self.track_title_label)
        media_layout.addWidget(self.track_artist_label)
        media_layout.addWidget(self.track_time_label)
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

        # Add media widget to the right side (NO stretch factor here)
        top_section_layout.addWidget(media_widget) # Removed stretch factor '1'

        # --- Add a single stretch at the end ---
        # This will push the grid_widget and media_widget together to the left
        top_section_layout.addStretch(1)

        # --- Add Top Section to Main Layout ---
        # The top section layout itself can still take available vertical space if needed
        self.main_layout.addLayout(top_section_layout, 1) # Keep stretch factor here if desired


    # --- on_home_button_clicked method (no changes needed) ---
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
            # ... (rest of the conditions) ...
            else:
                 print(f"No navigation action defined for: {button_name}")
        else:
            print("Error: Could not navigate. Main window reference is invalid or missing 'navigate_to' method.")
            # ... (rest of the error handling) ...

    # --- go_to_settings method (no changes needed) ---
    def go_to_settings(self):
        # ... (implementation remains the same) ...
        pass

    # --- _update_clock method (no changes needed) ---
    def _update_clock(self):
        """Updates the clock label with the current time."""
        current_time = QDateTime.currentDateTime()
        time_str = current_time.toString("HH:mm") # Format as Hour:Minute
        self.clock_label.setText(time_str)
