# gui/airplay_screen.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox, QMessageBox
)
from PyQt6.QtCore import pyqtSlot, QTimer

class AirPlayScreen(QWidget):
    screen_title = "AirPlay Mirroring"

    def __init__(self, airplay_manager, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.airplay_manager = airplay_manager

        # Timer per aggiornare lo stato della UI periodicamente
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.update_ui_state)
        
        self.setup_ui()
        self.update_ui_state()

    def setup_ui(self):
        """Imposta l'interfaccia utente."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # Sezione Stato
        status_group = QGroupBox("Stato del Servizio")
        status_layout = QHBoxLayout(status_group)
        self.status_label = QLabel("Inizializzazione...")
        self.status_label.setObjectName("statusLabel")
        status_layout.addWidget(self.status_label)
        layout.addWidget(status_group)

        # Sezione Controlli
        control_group = QGroupBox("Controlli")
        control_layout = QHBoxLayout(control_group)
        self.start_button = QPushButton("Avvia Mirroring")
        self.start_button.setObjectName("startAirPlayButton")
        self.start_button.clicked.connect(self.handle_start_click)
        
        self.stop_button = QPushButton("Ferma Mirroring")
        self.stop_button.setObjectName("stopAirPlayButton")
        self.stop_button.clicked.connect(self.handle_stop_click)
        
        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.stop_button)
        layout.addWidget(control_group)

        # Sezione Istruzioni
        info_group = QGroupBox("Come Connettersi")
        info_layout = QVBoxLayout(info_group)
        instructions_text = (
            "1. Clicca su 'Avvia Mirroring'.\n"
            "2. Assicurati che il tuo iPhone/iPad sia sulla stessa rete Wi-Fi.\n"
            "3. Apri il Centro di Controllo sul tuo dispositivo Apple.\n"
            "4. Tocca 'Duplica Schermo' e seleziona 'Car-Display' dalla lista."
        )
        info_label = QLabel(instructions_text)
        info_label.setWordWrap(True)
        info_layout.addWidget(info_label)
        layout.addWidget(info_group)

        layout.addStretch()

    def handle_start_click(self):
        """Gestisce il clic sul pulsante 'Avvia'."""
        self.airplay_manager.start_airplay()
        # Diamo un istante allo script per avviarsi prima di controllare lo stato.
        # Questo forza l'aggiornamento della UI quasi immediatamente.
        QTimer.singleShot(100, self.update_ui_state)

    def handle_stop_click(self):
        """Gestisce il clic sul pulsante 'Ferma'."""
        self.airplay_manager.stop_airplay()
        # Diamo un istante al comando pkill per terminare il processo.
        QTimer.singleShot(100, self.update_ui_state)

    def update_ui_state(self):
        """Aggiorna lo stato dei pulsanti e del testo in base allo stato del manager."""
        if self.airplay_manager.is_running():
            self.status_label.setText("ATTIVO - Rilevabile come 'Car-Display'")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
        else:
            self.status_label.setText("NON ATTIVO")
            self.status_label.setStyleSheet("color: gray;")
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)

    def showEvent(self, event):
        """Chiamato quando la schermata diventa visibile."""
        super().showEvent(event)
        self.update_ui_state() # Aggiorna subito lo stato
        self.status_timer.start(2000) # Controlla lo stato ogni 2 secondi

    def hideEvent(self, event):
        """Chiamato quando la schermata viene nascosta."""
        super().hideEvent(event)
        self.status_timer.stop()