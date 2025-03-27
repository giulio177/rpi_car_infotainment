# gui/radio_screen.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QSlider, QProgressBar)
from PyQt6.QtCore import pyqtSlot, Qt

# REMOVE OR COMMENT OUT THIS LINE:
# from .main_window import MainWindow


class RadioScreen(QWidget):
    def __init__(self, radio_manager, parent=None): # parent is likely MainWindow
        super().__init__(parent)
        self.radio_manager = radio_manager
        # Store the parent (which should be the MainWindow instance)
        self.main_window = parent

        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(10) # Add some spacing

        # --- Add Top Bar with Home Button ---
        top_bar_layout = QHBoxLayout()
        top_bar_layout.setContentsMargins(0, 0, 0, 0)

        self.home_button = QPushButton("🏠") # Home symbol
        self.home_button.setFixedSize(40, 40)
        self.home_button.setObjectName("homeNavButton")
        self.home_button.clicked.connect(self.go_home)

        top_bar_layout.addWidget(self.home_button)
        top_bar_layout.addStretch(1) # Push button to the left

        self.restart_button = QPushButton("🔄") # Restart symbol (Or use text "Restart")
        self.restart_button.setFixedSize(40, 40)
        self.restart_button.setObjectName("restartNavButton")
        self.restart_button.setToolTip("Restart Application") # Optional tooltip
        self.restart_button.clicked.connect(self.on_restart_clicked)

        top_bar_layout.addWidget(self.restart_button) # Add to the right

        # Add top bar to the main layout first
        self.layout.addLayout(top_bar_layout)
        # --- End Top Bar ---

        # --- Existing Radio Screen Content ---
        self.title_label = QLabel("FM Radio")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-size: 24pt; font-weight: bold; margin-bottom: 15px;")
        self.layout.addWidget(self.title_label)

        # Frequency Display
        self.freq_display = QLabel("--- MHz")
        self.freq_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.freq_display.setStyleSheet("font-size: 36pt; font-weight: bold; color: #17a2b8;")
        self.layout.addWidget(self.freq_display)

        # Status/RDS Display
        self.status_display = QLabel("Status: Initializing...")
        self.status_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.status_display)

        # Signal Strength
        self.signal_bar = QProgressBar()
        self.signal_bar.setRange(0, 100); self.signal_bar.setValue(0); self.signal_bar.setTextVisible(False)
        self.signal_bar.setFixedHeight(15)
        self.layout.addWidget(self.signal_bar)

        # Controls
        self.controls_layout = QHBoxLayout()
        self.btn_seek_down = QPushButton("<< Seek")
        self.btn_tune_down = QPushButton("< Tune")
        self.btn_tune_up = QPushButton("Tune >")
        self.btn_seek_up = QPushButton("Seek >>")
        self.controls_layout.addWidget(self.btn_seek_down)
        self.controls_layout.addWidget(self.btn_tune_down)
        self.controls_layout.addStretch(1)
        self.controls_layout.addWidget(self.btn_tune_up)
        self.controls_layout.addWidget(self.btn_seek_up)
        self.layout.addLayout(self.controls_layout)

        # Presets
        self.presets_layout = QHBoxLayout()
        self.preset_buttons = []
        for i in range(5):
            btn = QPushButton(f"P{i+1}")
            # TODO: Load/Save preset frequencies from settings
            btn.clicked.connect(lambda checked, freq=90.0+i*2: self.radio_manager.tune_frequency(freq)) # Dummy frequencies
            self.presets_layout.addWidget(btn)
            self.preset_buttons.append(btn)
        self.layout.addLayout(self.presets_layout)

        self.layout.addStretch(1) # Push content towards the top (below home button)

        # --- Connect Buttons to Radio Manager ---
        tune_step = 0.1 # FM tune step
        self.btn_tune_down.clicked.connect(lambda: self.radio_manager.tune_frequency(self.radio_manager.current_frequency - tune_step))
        self.btn_tune_up.clicked.connect(lambda: self.radio_manager.tune_frequency(self.radio_manager.current_frequency + tune_step))
        self.btn_seek_down.clicked.connect(lambda: self.radio_manager.seek("down"))
        self.btn_seek_up.clicked.connect(lambda: self.radio_manager.seek("up"))
        # self.btn_scan.clicked.connect(self.radio_manager.start_scan)


    @pyqtSlot(float)
    def update_frequency(self, frequency_mhz):
        self.freq_display.setText(f"{frequency_mhz:.1f} MHz")

    @pyqtSlot(int)
    def update_signal_strength(self, strength):
        self.signal_bar.setValue(strength)

    @pyqtSlot(str)
    def update_status_display(self, status):
        self.status_display.setText(f"Status: {status}")

    # @pyqtSlot(dict)
    # def update_rds(self, rds_data):
    #     # TODO: Display RDS info
    #     pass

    def on_restart_clicked(self):
        """Triggers the application restart via MainWindow."""
        print(f"Restart requested from {self.__class__.__name__}")
        # Use self.main_window which should hold the MainWindow instance
        if self.main_window is not None and hasattr(self.main_window, 'restart_application'):
            self.main_window.restart_application()
        else:
            print("Error: Cannot trigger restart. Main window reference is invalid or missing 'restart_application' method.")
  
    def go_home(self):
        """Navigate back to the HomeScreen."""
        # Check if self.main_window exists AND has the 'navigate_to' and 'home_screen' methods/attributes
        if self.main_window is not None and hasattr(self.main_window, 'navigate_to') and hasattr(self.main_window, 'home_screen'):
            self.main_window.navigate_to(self.main_window.home_screen)
        else:
            print("Error: Cannot navigate home. Main window reference is invalid or missing required attributes.")
            if self.main_window is None:
                print("Reason: self.main_window is None.")
            elif not hasattr(self.main_window, 'navigate_to'):
                print(f"Reason: Main window object {type(self.main_window)} does not have 'navigate_to' method.")
            elif not hasattr(self.main_window, 'home_screen'):
                 print(f"Reason: Main window object {type(self.main_window)} does not have 'home_screen' attribute.")
