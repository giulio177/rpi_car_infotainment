# gui/home_screen.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QPushButton, QLabel, QSpacerItem, QSizePolicy,
                             QSlider)
from PyQt6.QtCore import QTimer, QDateTime, Qt, QSize
from PyQt6.QtGui import QPixmap, QIcon


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
            ("Music", "music-icon.png"),
            ("Radio", "radio-icon.png"),
            ("Equalizer", "eq-icon.png"),
            ("Settings", "settings-icon.png") # Keep only your actual buttons
        ]

        # --- Define Grid Dimensions and Button Size ---
        target_cols = 5
        num_buttons = len(buttons_data)
        num_rows = (num_buttons + target_cols - 1) // target_cols # Calculate rows needed

        btn_index = 0
        for r in range(num_rows):
            for c in range(target_cols):
                if btn_index < len(buttons_data):
                    name, icon_path = buttons_data[btn_index]
                    button = QPushButton(name)

                    # --- Set FIXED Size ---
                    button.setFixedSize(button_fixed_size)

                    # Buttons will now fill their grid cell automatically
                    button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

                    # --- REMOVED: Fixed size setting ---
                    # button.setFixedSize(button_fixed_size) # No longer needed

                    # ... (optional icon loading logic - keep if used) ...

                    button.setObjectName(f"homeBtn{name.replace(' ', '')}")
                    button.clicked.connect(lambda checked, b=name: self.on_home_button_clicked(b))

                    # --- MODIFIED: Add button without alignment flags ---
                    # The Expanding policy handles cell filling
                    grid_layout.addWidget(button, r, c)
                    btn_index += 1

        # This spacer expands vertically, pushing the button rows upwards.
        vertical_spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        # Add it to the grid layout, spanning all columns in the row below the last buttons
        grid_layout.addItem(vertical_spacer, num_rows, 0, 1, target_cols)

                # --- 2. Media Player Section (Setup remains the same) ---
        media_widget = QWidget()
        media_layout = QVBoxLayout(media_widget)
        # ... [all the labels, buttons, etc. for the media player - NO CHANGES HERE] ...
        media_widget.setLayout(media_layout) # Ensure layout is set for the media player widget

        # --- Grid Widget setup (comes from earlier in the code) ---
        # Assume 'grid_widget' is already created and has its QGridLayout populated with buttons
        # Ensure its layout is set: grid_widget.setLayout(grid_layout)

        # --- MODIFIED: Adding widgets to top_section_layout for correct positioning ---

        # 1. Add grid_widget FIRST. Give it a horizontal stretch factor of 1.
        #    This tells it to expand horizontally and take up available space.
        top_section_layout.addWidget(grid_widget, 1) # The '1' is the stretch factor

        # 2. Add a stretch item (a flexible, empty space).
        #    This will push everything after it (the media_widget) to the right.
        top_section_layout.addStretch(1)

        # 3. Add media_widget LAST. Do NOT give it a stretch factor (or use 0).
        #    This makes it take only its preferred size, staying on the right.
        top_section_layout.addWidget(media_widget) # No stretch factor = 0

        # --- Add Top Section (the QHBoxLayout) to the Main Layout (the QVBoxLayout) ---
        # The stretch factor here (e.g., 1) controls how much *vertical* space
        # this entire top section takes relative to other items in main_layout (like the header).
        self.main_layout.addLayout(top_section_layout, 1)


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
