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
    # Handle Ctrl+C gracefully
    signal.signal(signal.SIGINT, sigint_handler)

    app = QApplication(sys.argv)

    settings_manager = SettingsManager('config.json')

    main_win = MainWindow(settings_manager)
    main_win.show() # Or main_win.showFullScreen() for kiosk mode

    # --- Correct Timer for Signal Handling ---
    # Create a QTimer instance
    signal_timer = QTimer()
    # You don't strictly need to connect the timeout signal for this workaround,
    # but connecting it to a no-op lambda is harmless and explicit.
    signal_timer.timeout.connect(lambda: None)
    # Start the timer to fire every 500ms
    signal_timer.start(500)
    # --- End Timer Correction ---

    sys.exit(app.exec())
