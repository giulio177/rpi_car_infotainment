#!/usr/bin/env python3

import sys
import os
import signal
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QGuiApplication
from gui.main_window import MainWindow
from backend.settings_manager import SettingsManager

def sigint_handler(*args):
    """Handler for the SIGINT signal."""
    print("\nCtrl+C pressed. Exiting gracefully...")
    QApplication.quit()

if __name__ == "__main__":
    # Set the platform to offscreen
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    
    signal.signal(signal.SIGINT, sigint_handler) # Handle Ctrl+C

    app = QApplication(sys.argv)

    settings_manager = SettingsManager('config.json')

    # Create main window
    main_win = MainWindow(settings_manager)
    
    # Set a smaller size for headless mode
    main_win.resize(800, 600)
    
    # Don't show the window in headless mode
    # main_win.show()
    
    print("Application running in headless mode...")
    print("Press Ctrl+C to exit")

    # Timer for reliable Ctrl+C handling in Qt loop
    signal_timer = QTimer()
    signal_timer.timeout.connect(lambda: None)
    signal_timer.start(500)

    sys.exit(app.exec())
