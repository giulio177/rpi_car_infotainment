# main.py

import sys
import os
import signal
import logging
import psutil
from datetime import datetime  # <--- Necessario per la data/ora
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow
from backend.settings_manager import SettingsManager

# --- 1. SETUP DEL SISTEMA DI LOGGING (VERSIONE ROBUSTA) ---

# Calcola la cartella base dove si trova QUESTO file (main.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")

# Classe helper per reindirizzare print() e stderr dentro il sistema di logging
class StreamToLogger(object):
    def __init__(self, logger, log_level=logging.INFO):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ''

    def write(self, buf):
        # Scrive ogni linea nel logger invece che sul terminale grezzo
        for line in buf.rstrip().splitlines():
            self.logger.log(self.log_level, line.rstrip())

    def flush(self):
        pass

def setup_logging():
    """Configura il logging resettando eventuali config di Qt e catturando stdout/stderr."""
    
    # 1. Crea la cartella log se non esiste
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
    except OSError as e:
        print(f"Errore critico creazione cartella log: {e}")
        return

    # 2. Genera il nome del file con timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = f"infotainment_app_{timestamp}.log"
    current_log_path = os.path.join(LOG_DIR, log_filename)
    
    # 3. RESET DEL LOGGER ROOT (Il passaggio fondamentale!)
    # Otteniamo il logger principale
    root_logger = logging.getLogger()
    
    # Rimuoviamo TUTTI gli handler esistenti (es. quelli messi da Qt o Pygame)
    if root_logger.handlers:
        for handler in root_logger.handlers[:]: # Copia della lista per iterare e rimuovere
            root_logger.removeHandler(handler)
    
    # Impostiamo il livello base
    root_logger.setLevel(logging.DEBUG)

    # 4. Creiamo manualmente i nuovi Handler
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(name)s:%(lineno)d] - %(message)s')

    # A) File Handler (Scrive su disco)
    file_handler = logging.FileHandler(current_log_path, mode='w', encoding='utf-8')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    # B) Console Handler (Scrive a video)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG)

    # Aggiungiamo i nostri handler puliti
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # 5. CATTURA DI STDOUT E STDERR (Opzionale ma consigliato)
    # Questo fa sì che anche i "print()" e gli errori di sistema finiscano nel file .log
    sys.stdout = StreamToLogger(logging.getLogger('STDOUT'), logging.INFO)
    sys.stderr = StreamToLogger(logging.getLogger('STDERR'), logging.ERROR)

    logging.info("--- Inizio del Log di RPi Car Infotainment ---")
    logging.info(f"File di log creato: {current_log_path}")
    logging.info(f"Piattaforma: {sys.platform}")


def handle_exception(exc_type, exc_value, exc_traceback):
    """
    Gestisce i crash scrivendo il traceback nel log.
    """
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logging.critical("!!! ERRORE FATALE NON GESTITO (CRASH) !!!", exc_info=(exc_type, exc_value, exc_traceback))

# Imposta la nostra funzione per gestire i crash
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
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['pid'] != current_pid and proc.info['cmdline']:
                    if 'main.py' in proc.info['cmdline'] or process_name in proc.info['cmdline']:
                        logging.warning("Un'altra istanza dell'app è già in esecuzione. Chiusura.")
                        sys.exit(1)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                # Ignore transient process states while scanning for duplicates
                continue
    except PermissionError:
        logging.warning("Permessi insufficienti per verificare processi paralleli; proseguo comunque.")

    logging.info("Nessuna altra istanza trovata. Proseguo con l'avvio.")

    # La configurazione di QT_QPA_PLATFORM viene ora gestita dal servizio systemd o dallo script di avvio
    # Lasciamo questo controllo per l'avvio manuale
    if "QT_QPA_PLATFORM" not in os.environ:
        def _detect_default_platform():
            """Choose a sensible Qt platform plugin based on the host environment."""
            if sys.platform == "darwin":
                return "cocoa"
            if sys.platform.startswith("win"):
                return "windows"
            if os.environ.get("DISPLAY"):
                return "xcb"
            return "linuxfb"

        platform_plugin = _detect_default_platform()
        logging.warning(
            "QT_QPA_PLATFORM non impostata, uso valore di default '%s'.",
            platform_plugin,
        )
        os.environ["QT_QPA_PLATFORM"] = platform_plugin

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

    # Determine platform capabilities
    qpa_platform = os.environ.get("QT_QPA_PLATFORM", "").lower()
    framebuffer_platforms = ("linuxfb", "eglfs")
    is_framebuffer = any(qpa_platform.startswith(name) for name in framebuffer_platforms)

    # Position the window
    position_bottom_right = settings_manager.get("position_bottom_right")
    primary_screen = app.primaryScreen()

    if primary_screen is not None:
        desktop = primary_screen.geometry()
        logging.info(f"Schermo primario trovato con geometria: {desktop.width()}x{desktop.height()}")

        if position_bottom_right:
            x = desktop.width() - target_width
            y = desktop.height() - target_height
            logging.info(f"Posizionamento finestra in basso a destra: ({x}, {y})")
            window_pos = (desktop.x() + max(0, x), desktop.y() + max(0, y))
        else:
            logging.info("Posizionamento finestra in alto a sinistra.")
            window_pos = (desktop.x(), desktop.y())
    else:
        logging.warning("Nessuno schermo primario disponibile, imposto dimensione di default.")
        window_pos = None


    main_win.setFixedSize(target_width, target_height)
    
    if is_framebuffer:
        logging.info("Piattaforma framebuffer rilevata (%s). Avvio in fullscreen.", qpa_platform or "default")
        logging.info(f"FORZATURA: Applico dimensione {target_width}x{target_height} e posiziono a (0,0).")
        
        # Rimuove bordi e decorazioni (simula fullscreen ma con dimensioni controllate)
        main_win.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        
        # Forza la posizione in alto a sinistra
        main_win.move(0, 0)
        
        # Usa .show() invece di .showFullScreen() per evitare l'override del driver
        main_win.show()
    else:
        main_win.setFixedSize(target_width, target_height)
        if window_pos is not None:
            main_win.move(*window_pos)
        logging.info("Avvio in modalità finestra con dimensione fissa %dx%d.", target_width, target_height)
        main_win.show()

    # Timer for reliable Ctrl+C handling in Qt loop
    signal_timer = QTimer()
    signal_timer.timeout.connect(lambda: None)
    signal_timer.start(500)

    logging.info("Avvio del ciclo di eventi dell'applicazione (app.exec).")
    sys.exit(app.exec())
