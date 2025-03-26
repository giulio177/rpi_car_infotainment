import sys
import signal
from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow
from backend.settings_manager import SettingsManager

def sigint_handler(*args):
    """Handler for the SIGINT signal."""
    print("\nCtrl+C pressed. Exiting gracefully...")
    QApplication.quit()

if __name__ == "__main__":
    # Handle Ctrl+C gracefully
    signal.signal(signal.SIGINT, sigint_handler)

    app = QApplication(sys.argv)

    settings_manager = SettingsManager('config.json')

    main_win = MainWindow(settings_manager)
    main_win.show() # Or main_win.showFullScreen() for kiosk mode

    # Create a timer to allow Python's signal handler to run
    timer = app.timerEvent # Workaround for PyQt signal handling
    timer.start(500) # Check every 500 ms

    sys.exit(app.exec())