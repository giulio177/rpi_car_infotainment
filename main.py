# main.py

import sys
import os
import signal
import logging
import psutil
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow
from backend.settings_manager import SettingsManager

# --- 1. SETUP DEL SISTEMA DI LOGGING ---
LOG_FILE_PATH = "/tmp/infotainment_app.log"

def setup_logging():
    """Configura il logging per scrivere su file e sulla console."""
    # Cancella il file di log precedente se esiste
    if os.path.exists(LOG_FILE_PATH):
        os.remove(LOG_FILE_PATH)
    
    # Configura il logger principale per catturare tutto
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - [%(name)s:%(lineno)d] - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE_PATH, mode='w', encoding='utf-8'),
            logging.StreamHandler(sys.stdout) # Continua a stampare anche sul terminale
        ]
    )
    logging.info("--- Inizio del Log di RPi Car Infotainment ---")

def handle_exception(exc_type, exc_value, exc_traceback):
    """
    Questa funzione viene chiamata automaticamente da Python quando c'è un crash (eccezione non gestita).
    Scriverà il traceback completo nel nostro file di log prima di terminare.
    """
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    # Logga l'errore fatale che ha causato il crash
    logging.critical("!!! ERRORE FATALE NON GESTITO (CRASH) !!!", exc_info=(exc_type, exc_value, exc_traceback))

# Imposta la nostra funzione per gestire i crash il prima possibile
sys.excepthook = handle_exception
# --- FINE SETUP LOGGING ---


def sigint_handler(*args):
    """Handler for the SIGINT signal (Ctrl+C)."""
    logging.info("Ctrl+C premuto. Chiusura in corso...")
    QApplication.quit()


if __name__ == "__main__":
    # --- 2. ATTIVAZIONE DEL LOGGING ALL'AVVIO ---
    setup_logging()
    
    logging.info("Applicazione in avvio. Controllo istanze multiple...")

    # Prevent multiple instances of the app
    current_pid = os.getpid()
    process_name = os.path.basename(__file__)
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['pid'] != current_pid and proc.info['cmdline']:
                if 'main.py' in proc.info['cmdline'] or process_name in proc.info['cmdline']:
                    logging.warning("Un'altra istanza dell'app è già in esecuzione. Chiusura.")
                    sys.exit(1)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    logging.info("Nessuna altra istanza trovata. Proseguo con l'avvio.")

    # La configurazione di QT_QPA_PLATFORM viene ora gestita dal servizio systemd o dallo script di avvio
    # Lasciamo questo controllo per l'avvio manuale
    if "QT_QPA_PLATFORM" not in os.environ:
        logging.warning("QT_QPA_PLATFORM non impostata, default a 'linuxfb'.")
        os.environ["QT_QPA_PLATFORM"] = "linuxfb"

    signal.signal(signal.SIGINT, sigint_handler)  # Handle Ctrl+C

    app = QApplication(sys.argv)
    logging.info("QApplication creata.")

    settings_manager = SettingsManager("config.json")
    logging.info("SettingsManager inizializzato.")

    # Apply cursor visibility setting
    show_cursor = settings_manager.get("show_cursor")
    if not show_cursor:
        app.setOverrideCursor(Qt.CursorShape.BlankCursor)
        logging.info("Cursore nascosto in base alle impostazioni.")
    else:
        logging.info("Cursore visibile in base alle impostazioni.")

    main_win = MainWindow(settings_manager)
    logging.info("Finestra principale creata.")

    # Get resolution from settings
    resolution = settings_manager.get("window_resolution")
    target_width = resolution[0]
    target_height = resolution[1]
    logging.info(f"Impostazione dimensione finestra a: {target_width}x{target_height}")

    # Force window to stay exactly within screen bounds
    position_bottom_right = settings_manager.get("position_bottom_right")
    primary_screen = app.primaryScreen()

    if primary_screen is not None:
        desktop = primary_screen.geometry()
        screen_width = desktop.width()
        screen_height = desktop.height()
        logging.info(f"Schermo primario trovato con geometria: {screen_width}x{screen_height}")

        # Ensure the window never exceeds screen dimensions
        actual_width = min(target_width, screen_width)
        actual_height = min(target_height, screen_height)

        if actual_width != target_width or actual_height != target_height:
            logging.info(f"Dimensioni finestra ridotte per adattarsi allo schermo: {actual_width}x{actual_height}")

        if position_bottom_right:
            # Position in bottom-right, ensuring it stays within screen bounds
            x = max(0, screen_width - actual_width)
            y = max(0, screen_height - actual_height)
            logging.info(f"Posizionamento finestra in basso a destra: ({x}, {y})")
            main_win.setGeometry(x, y, actual_width, actual_height)
        else:
            # Position at top-left (0, 0)
            logging.info("Posizionamento finestra in alto a sinistra.")
            main_win.setGeometry(0, 0, actual_width, actual_height)

        # Set size constraints to prevent the window from being resized beyond screen bounds
        main_win.setMinimumSize(actual_width, actual_height)
        main_win.setMaximumSize(actual_width, actual_height)

    else:
        logging.warning("Nessuno schermo primario disponibile, imposto dimensione di default.")
        main_win.setGeometry(0, 0, target_width, target_height)
        main_win.setMinimumSize(target_width, target_height)
        main_win.setMaximumSize(target_width, target_height)

    # Show the window normally instead of fullscreen to maintain exact control
    main_win.show()
    logging.info("Finestra principale mostrata con dimensioni fisse.")

    # Timer for reliable Ctrl+C handling in Qt loop
    signal_timer = QTimer()
    signal_timer.timeout.connect(lambda: None)
    signal_timer.start(500)

    logging.info("Avvio del ciclo di eventi dell'applicazione (app.exec).")
    sys.exit(app.exec())