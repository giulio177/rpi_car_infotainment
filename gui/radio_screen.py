# gui/radio_screen.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QSlider, QProgressBar, QSpacerItem, QSizePolicy)
from PyQt6.QtCore import QTimer, QDateTime, pyqtSlot, Qt

# --- Import scale_value helper ---
from .styling import scale_value

class RadioScreen(QWidget):
    def __init__(self, radio_manager, parent=None): # parent is likely MainWindow
        super().__init__(parent)
        self.radio_manager = radio_manager
        self.main_window = parent

        # --- Base sizes ---
        self.base_margin = 10
        self.base_spacing = 10 # General spacing
        self.base_controls_spacing = 10
        self.base_presets_spacing = 5

        # --- Main Layout ---
        self.main_layout = QVBoxLayout(self)
        # Margins/Spacing set by update_scaling

        # --- Header Layout ---
        self.header_layout = QHBoxLayout()
        self.header_title_label = QLabel("Home") # Or screen-specific title
        self.header_title_label.setObjectName("headerTitle")
        self.header_layout.addWidget(self.header_title_label)

        header_spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.header_layout.addItem(header_spacer) # Pushes right-aligned items

        # --- ADDED: Header BT Labels ---
        self.bt_battery_label = QLabel("") # Placeholder for battery %
        self.bt_battery_label.setObjectName("headerBtBattery")
        self.bt_battery_label.hide() # Initially hidden
        self.header_layout.addWidget(self.bt_battery_label)

        self.bt_icon_label = QLabel() # Placeholder for icon
        self.bt_icon_label.setObjectName("headerBtIcon")
        self.bt_icon_label.hide() # Initially hidden
        self.header_layout.addWidget(self.bt_icon_label)
        # --- END ADDED ---

        self.clock_label = QLabel("00:00")
        self.clock_label.setObjectName("headerClock")
        self.header_layout.addWidget(self.clock_label) # Clock is last
        self.clock_timer = QTimer(self) # Assign to self.clock_timer
        # ----------------------
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(10000)
        self._update_clock()
        self.main_layout.addLayout(self.header_layout)
        # --- END Header ---


        # Frequency Display
        self.freq_display = QLabel("--- MHz")
        self.freq_display.setObjectName("freq_display") # Use ID for styling in QSS
        # self.freq_display.setAlignment(Qt.AlignmentFlag.AlignCenter) # Set in QSS if possible
        # self.freq_display.setStyleSheet(...) # REMOVE - Style via QSS
        self.main_layout.addWidget(self.freq_display)

        # Status/RDS Display
        self.status_display = QLabel("Status: Initializing...")
        self.status_display.setObjectName("radioStatusLabel") # ID for styling
        self.status_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.addWidget(self.status_display)

        # Signal Strength
        self.signal_bar = QProgressBar()
        self.signal_bar.setObjectName("signalBar") # ID for styling
        self.signal_bar.setRange(0, 100); self.signal_bar.setValue(0); self.signal_bar.setTextVisible(False)
        # self.signal_bar.setFixedHeight(15) # REMOVE - Style via QSS
        self.main_layout.addWidget(self.signal_bar)

        # Controls
        self.controls_layout = QHBoxLayout() # Store reference
        # Spacing set by update_scaling
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
        self.presets_layout = QHBoxLayout() # Store reference
         # Spacing set by update_scaling
        self.preset_buttons = []
        for i in range(5): # Number of presets
            btn = QPushButton(f"P{i+1}")
            btn.setObjectName(f"presetButton{i+1}") # ID for styling
            # TODO: Load/Save preset frequencies from settings
            btn.clicked.connect(lambda checked, index=i: self.preset_clicked(index)) # Connect to handler
            self.presets_layout.addWidget(btn)
            self.preset_buttons.append(btn)
        self.main_layout.addLayout(self.presets_layout)

        self.main_layout.addStretch(1) # Push content towards the top

        # --- Connect Buttons to Radio Manager ---
        tune_step = 0.1 # FM tune step
        self.btn_tune_down.clicked.connect(lambda: self.radio_manager.tune_frequency(self.radio_manager.current_frequency - tune_step))
        self.btn_tune_up.clicked.connect(lambda: self.radio_manager.tune_frequency(self.radio_manager.current_frequency + tune_step))
        self.btn_seek_down.clicked.connect(lambda: self.radio_manager.seek("down"))
        self.btn_seek_up.clicked.connect(lambda: self.radio_manager.seek("up"))


    def update_scaling(self, scale_factor, scaled_main_margin):
        """Applies scaling to internal layouts."""
        scaled_spacing = scale_value(self.base_spacing, scale_factor)
        scaled_controls_spacing = scale_value(self.base_controls_spacing, scale_factor)
        scaled_presets_spacing = scale_value(self.base_presets_spacing, scale_factor)

        # Apply to layouts
        self.main_layout.setContentsMargins(scaled_main_margin, scaled_main_margin, scaled_main_margin, scaled_main_margin)
        self.main_layout.setSpacing(scaled_spacing)
        self.header_layout.setSpacing(scaled_spacing)
        self.controls_layout.setSpacing(scaled_controls_spacing)
        self.presets_layout.setSpacing(scaled_presets_spacing)

    def preset_clicked(self, index):
        # TODO: Retrieve the frequency associated with this preset index (e.g., from settings)
        # Placeholder: dummy frequency calculation
        dummy_freq = 90.0 + index * 2.5
        print(f"Preset {index+1} clicked. Tuning to {dummy_freq:.1f} MHz (placeholder)")
        self.radio_manager.tune_frequency(dummy_freq)

    @pyqtSlot(float)
    def update_frequency(self, frequency_mhz):
        self.freq_display.setText(f"{frequency_mhz:.1f} MHz")

    @pyqtSlot(int)
    def update_signal_strength(self, strength):
        self.signal_bar.setValue(strength)

    @pyqtSlot(str)
    def update_status_display(self, status):
        self.status_display.setText(f"Status: {status}")

    def _update_clock(self):
        """Updates the clock label with the current time."""
        current_time = QDateTime.currentDateTime()
        time_str = current_time.toString("HH:mm")
        self.clock_label.setText(time_str)
