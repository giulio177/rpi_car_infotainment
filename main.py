# main.py

import sys
import signal
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow
from backend.settings_manager import SettingsManager

def sigint_handler(*args):
    """Handler for the SIGINT signal."""
    print("\nCtrl+C pressed. Exiting gracefully...")
    QApplication.quit()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, sigint_handler) # Handle Ctrl+C

    app = QApplication(sys.argv)

    settings_manager = SettingsManager('config.json')
    main_win = MainWindow(settings_manager)

    # --- MODIFIED: Show in Full Screen ---
    # main_win.show() # Previous line
    main_win.showFullScreen() # Show maximized without window decorations
    # --- END MODIFICATION ---

    # Timer for reliable Ctrl+C handling in Qt loop
    signal_timer = QTimer()
    signal_timer.timeout.connect(lambda: None)
    signal_timer.start(500)

    sys.exit(app.exec())
