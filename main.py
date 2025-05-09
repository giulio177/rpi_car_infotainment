# main.py

import sys
import signal
from PyQt6.QtCore import QTimer, Qt
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

    app.setOverrideCursor(Qt.CursorShape.BlankCursor)

    settings_manager = SettingsManager('config.json')
    main_win = MainWindow(settings_manager)

    target_width = 1024
    target_height = 600
    print(f"Setting fixed window size to: {target_width}x{target_height}")
    main_win.resize(target_width, target_height)
    main_win.showFullScreen()

    # Timer for reliable Ctrl+C handling in Qt loop
    signal_timer = QTimer()
    signal_timer.timeout.connect(lambda: None)
    signal_timer.start(500)

    sys.exit(app.exec())
