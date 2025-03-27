# gui/radio_screen.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QSlider, QProgressBar, QSpacerItem, QSizePolicy)
from PyQt6.QtCore import QTimer, QDateTime, pyqtSlot, Qt

# REMOVE OR COMMENT OUT THIS LINE:
# from .main_window import MainWindow


class RadioScreen(QWidget):
    def __init__(self, radio_manager, parent=None): # parent is likely MainWindow
        super().__init__(parent)
        self.radio_manager = radio_manager
        # Store the parent (which should be the MainWindow instance)
        self.main_window = parent

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(10) # Add some spacing


        # --- NEW: Create Header Layout ---
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(5, 5, 5, 5) # Adjust margins as needed
        header_layout.setSpacing(10)
        
        # --- NEW: Header Title Label ---
        # CHANGE "Screen Title" for each screen
        self.header_title_label = QLabel("FM Radio") # e.g., "Home", "OBD-II Data", "FM Radio", "Settings"
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


        # Frequency Display
        self.freq_display = QLabel("--- MHz")
        self.freq_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.freq_display.setStyleSheet("font-size: 36pt; font-weight: bold; color: #17a2b8;")
        self.main_layout.addWidget(self.freq_display)

        # Status/RDS Display
        self.status_display = QLabel("Status: Initializing...")
        self.status_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.status_display)

        # Signal Strength
        self.signal_bar = QProgressBar()
        self.signal_bar.setRange(0, 100); self.signal_bar.setValue(0); self.signal_bar.setTextVisible(False)
        self.signal_bar.setFixedHeight(15)
        self.main_layout.addWidget(self.signal_bar)

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
        self.main_layout.addLayout(self.controls_layout)

        # Presets
        self.presets_layout = QHBoxLayout()
        self.preset_buttons = []
        for i in range(5):
            btn = QPushButton(f"P{i+1}")
            # TODO: Load/Save preset frequencies from settings
            btn.clicked.connect(lambda checked, freq=90.0+i*2: self.radio_manager.tune_frequency(freq)) # Dummy frequencies
            self.presets_layout.addWidget(btn)
            self.preset_buttons.append(btn)
        self.main_layout.addLayout(self.presets_layout)

        self.main_layout.addStretch(1) # Push content towards the top (below home button)

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


    def _update_clock(self):
        """Updates the clock label with the current time."""
        current_time = QDateTime.currentDateTime()
        time_str = current_time.toString("HH:mm") # Format as Hour:Minute
        self.clock_label.setText(time_str)
