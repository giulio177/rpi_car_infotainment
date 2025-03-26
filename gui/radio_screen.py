from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QSlider, QProgressBar)
from PyQt6.QtCore import pyqtSlot, Qt

class RadioScreen(QWidget):
    def __init__(self, radio_manager, parent=None):
        super().__init__(parent)
        self.radio_manager = radio_manager

        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.title_label = QLabel("FM Radio")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("font-size: 24pt; font-weight: bold; margin-bottom: 15px;")
        self.layout.addWidget(self.title_label)

        # Frequency Display
        self.freq_display = QLabel("--- MHz")
        self.freq_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.freq_display.setStyleSheet("font-size: 36pt; font-weight: bold; color: #17a2b8;") # Teal color example
        self.layout.addWidget(self.freq_display)

        # Status/RDS Display (if implemented)
        self.status_display = QLabel("Status: Initializing...")
        self.status_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.status_display)

        # Signal Strength
        self.signal_bar = QProgressBar()
        self.signal_bar.setRange(0, 100)
        self.signal_bar.setValue(0)
        self.signal_bar.setTextVisible(False)
        self.signal_bar.setFixedHeight(15)
        self.layout.addWidget(self.signal_bar)

        # Controls
        self.controls_layout = QHBoxLayout()
        self.btn_seek_down = QPushButton("<< Seek")
        self.btn_tune_down = QPushButton("< Tune")
        self.btn_tune_up = QPushButton("Tune >")
        self.btn_seek_up = QPushButton("Seek >>")
        # self.btn_scan = QPushButton("Scan") # Add if implementing full scan

        self.controls_layout.addWidget(self.btn_seek_down)
        self.controls_layout.addWidget(self.btn_tune_down)
        self.controls_layout.addStretch(1)
        self.controls_layout.addWidget(self.btn_tune_up)
        self.controls_layout.addWidget(self.btn_seek_up)
        # self.controls_layout.addWidget(self.btn_scan)

        self.layout.addLayout(self.controls_layout)

        # --- Presets (Example - Simple Buttons) ---
        self.presets_layout = QHBoxLayout()
        self.preset_buttons = []
        for i in range(5): # 5 preset buttons
            btn = QPushButton(f"P{i+1}")
            # TODO: Load/Save preset frequencies from settings
            btn.clicked.connect(lambda checked, freq=90.0+i*2: self.radio_manager.tune_frequency(freq)) # Dummy frequencies
            self.presets_layout.addWidget(btn)
            self.preset_buttons.append(btn)
        self.layout.addLayout(self.presets_layout)


        self.layout.addStretch(1) # Push content to top

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
         # Basic scaling for progress bar
        self.signal_bar.setValue(strength)

    @pyqtSlot(str)
    def update_status_display(self, status):
        self.status_display.setText(f"Status: {status}")

    # @pyqtSlot(dict) # Or str, depending on how you format RDS
    # def update_rds(self, rds_data):
    #     # TODO: Display RDS info (Program Service, Radio Text)
    #     ps = rds_data.get('ps', '')
    #     rt = rds_data.get('rt', '')
    #     self.status_display.setText(f"{ps} - {rt}") # Example