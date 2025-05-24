# main.py

import sys
import os
import signal
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow
from backend.settings_manager import SettingsManager
import psutil


def sigint_handler(*args):
    """Handler for the SIGINT signal."""
    print("\nCtrl+C pressed. Exiting gracefully...")
    QApplication.quit()


if __name__ == "__main__":
    # Prevent multiple instances of the app
    current_pid = os.getpid()
    process_name = os.path.basename(__file__)
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['pid'] != current_pid and proc.info['cmdline']:
                if 'main.py' in proc.info['cmdline'] or process_name in proc.info['cmdline']:
                    print("Another instance of the infotainment app is already running. Exiting.")
                    sys.exit(1)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    # Set Qt platform for embedded systems without X server
    # Try different platforms in order of preference
    if "QT_QPA_PLATFORM" not in os.environ:
        # First try linuxfb (Linux framebuffer) which is more compatible
        os.environ["QT_QPA_PLATFORM"] = "linuxfb"

    signal.signal(signal.SIGINT, sigint_handler)  # Handle Ctrl+C

    app = QApplication(sys.argv)

    settings_manager = SettingsManager("config.json")

    # Apply cursor visibility setting
    show_cursor = settings_manager.get("show_cursor")
    if not show_cursor:
        app.setOverrideCursor(Qt.CursorShape.BlankCursor)
        print("Cursor hidden based on settings")
    else:
        print("Cursor visible based on settings")

    main_win = MainWindow(settings_manager)

    # Get resolution from settings
    resolution = settings_manager.get("window_resolution")
    target_width = resolution[0]
    target_height = resolution[1]
    print(f"Setting window size to: {target_width}x{target_height}")

    # Position the window
    position_bottom_right = settings_manager.get("position_bottom_right")
    primary_screen = app.primaryScreen()

    if primary_screen is not None:
        desktop = primary_screen.geometry()

        if position_bottom_right:
            # Calculate position to align bottom-right corner
            x = desktop.width() - target_width
            y = desktop.height() - target_height
            print(f"Positioning window at bottom-right corner: ({x}, {y})")
            main_win.setGeometry(x, y, target_width, target_height)
        else:
            # Default top-left positioning
            print("Positioning window at top-left corner")
            main_win.resize(target_width, target_height)
    else:
        # No screen available, just set the size
        print("No primary screen available, setting default size")
        main_win.resize(target_width, target_height)

    main_win.showFullScreen()

    # Timer for reliable Ctrl+C handling in Qt loop
    signal_timer = QTimer()
    signal_timer.timeout.connect(lambda: None)
    signal_timer.start(500)

    sys.exit(app.exec())
