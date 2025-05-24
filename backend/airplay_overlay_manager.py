# backend/airplay_overlay_manager.py

import subprocess
import threading
import time
import os
import signal
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QPixmap, QPainter, QColor
from PyQt6.QtCore import Qt


class AirPlayOverlayManager(QObject):
    """Manager for AirPlay that works as overlay over the main UI."""

    # Signals
    status_changed = pyqtSignal(str)  # "starting", "running", "stopped", "error"
    connection_changed = pyqtSignal(bool)  # True when device connects, False when disconnects
    show_overlay = pyqtSignal(bool)  # True to show overlay, False to hide
    show_control_popup = pyqtSignal()  # Signal to show control popup

    def __init__(self, main_window=None):
        super().__init__()

        self.main_window = main_window
        self.rpiplay_path = "/home/pi/RPiPlay/build/rpiplay"
        self.airplay_name = "Car Display"
        self.background_mode = "auto"

        # Check alternative paths
        if not os.path.exists(self.rpiplay_path):
            alt_path = "/home/pi/rpi_car_infotainment/rpiplay"
            if os.path.exists(alt_path):
                self.rpiplay_path = alt_path

        self.rpiplay_available = os.path.exists(self.rpiplay_path)

        # Process management
        self.rpiplay_process = None
        self.is_running = False
        self.monitor_thread = None
        self.stop_monitoring = False
        self.device_connected = False

        # Overlay widget for showing AirPlay status
        self.overlay_widget = None

        print(f"AirPlay Overlay Manager initialized. RPiPlay available: {self.rpiplay_available}")

    def create_overlay_widget(self, parent):
        """Create overlay widget to show over the main UI."""
        self.overlay_widget = QWidget(parent)
        self.overlay_widget.setObjectName("airplayOverlay")

        # Make it cover the entire parent
        self.overlay_widget.setGeometry(parent.rect())

        # Semi-transparent background
        self.overlay_widget.setStyleSheet("""
            QWidget#airplayOverlay {
                background-color: rgba(0, 0, 0, 128);
                border: 2px solid #00ff00;
            }
            QLabel {
                color: white;
                font-size: 24px;
                font-weight: bold;
            }
        """)

        layout = QVBoxLayout(self.overlay_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.overlay_label = QLabel("AirPlay Mirroring Active\n\nConnect your iPhone/iPad to see content here")
        self.overlay_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.overlay_label.setWordWrap(True)

        layout.addWidget(self.overlay_label)

        # Initially hidden
        self.overlay_widget.hide()

        return self.overlay_widget

    def is_available(self):
        """Check if RPiPlay is available."""
        return self.rpiplay_available

    def start_airplay(self):
        """Start AirPlay service with controlled X server management."""
        if not self.rpiplay_available:
            print("Error: RPiPlay is not available")
            self.status_changed.emit("error")
            return False

        if self.is_running:
            print("AirPlay is already running")
            return True

        try:
            print("Starting AirPlay service with video support...")
            self.status_changed.emit("starting")

            # Ensure X server is available for video display
            if not self._ensure_x_server():
                print("Warning: X server not available, continuing anyway...")

            # Set up environment
            env = os.environ.copy()
            env['DISPLAY'] = ':0'

            # Start RPiPlay with video support but controlled startup
            cmd = [
                self.rpiplay_path,
                "-n", self.airplay_name,
                "-b", self.background_mode,  # Use configured background mode
                "-d"         # Enable debug output
            ]

            print(f"Starting RPiPlay with command: {' '.join(cmd)}")

            self.rpiplay_process = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
                preexec_fn=os.setsid
            )

            self.is_running = True
            self.status_changed.emit("running")

            # Start monitoring thread
            self.stop_monitoring = False
            self.monitor_thread = threading.Thread(target=self._monitor_process)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()

            print(f"RPiPlay started with PID: {self.rpiplay_process.pid}")
            print("Device is now discoverable for video mirroring")

            return True

        except Exception as e:
            print(f"Error starting RPiPlay: {e}")
            self.status_changed.emit("error")
            self.is_running = False
            return False

    def stop_airplay(self):
        """Stop AirPlay service."""
        if not self.is_running or not self.rpiplay_process:
            print("AirPlay is not running")
            return True

        try:
            print("Stopping AirPlay service...")

            # Hide overlay
            self.show_overlay.emit(False)

            # Stop monitoring
            self.stop_monitoring = True

            # Terminate the process group
            os.killpg(os.getpgid(self.rpiplay_process.pid), signal.SIGTERM)

            # Wait for process to terminate
            try:
                self.rpiplay_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't terminate gracefully
                os.killpg(os.getpgid(self.rpiplay_process.pid), signal.SIGKILL)
                self.rpiplay_process.wait()

            self.rpiplay_process = None
            self.is_running = False
            self.device_connected = False
            self.status_changed.emit("stopped")

            print("AirPlay stopped successfully")
            return True

        except Exception as e:
            print(f"Error stopping AirPlay: {e}")
            self.status_changed.emit("error")
            return False

    def _monitor_process(self):
        """Monitor RPiPlay process and handle connection events."""
        while not self.stop_monitoring and self.rpiplay_process:
            try:
                # Check if process is still running
                if self.rpiplay_process.poll() is not None:
                    print("RPiPlay process has exited")
                    self.is_running = False
                    self.status_changed.emit("stopped")
                    # Hide overlay if device was connected
                    if self.device_connected:
                        self.show_overlay.emit(False)
                        self.connection_changed.emit(False)
                        self.device_connected = False
                    break

                # Read output for connection status
                if self.rpiplay_process.stdout:
                    try:
                        line = self.rpiplay_process.stdout.readline()
                        if line:
                            line = line.strip()
                            print(f"RPiPlay: {line}")

                            # Monitor for connection events
                            line_lower = line.lower()
                            if any(keyword in line_lower for keyword in ["client connected", "connection established", "stream started"]):
                                if not self.device_connected:
                                    print("AirPlay device connected - phone screen should be visible")
                                    self.device_connected = True
                                    self.connection_changed.emit(True)
                                    # Show click overlay after a delay to allow video to start
                                    from PyQt6.QtCore import QTimer
                                    QTimer.singleShot(2000, lambda: self.show_overlay.emit(True))

                            elif any(keyword in line_lower for keyword in ["client disconnected", "connection closed", "stream stopped"]):
                                if self.device_connected:
                                    print("AirPlay device disconnected - returning to Qt UI")
                                    self.device_connected = False
                                    self.connection_changed.emit(False)
                                    self.show_overlay.emit(False)
                                    # Force return to Qt framebuffer
                                    self._restore_qt_display()
                    except:
                        pass  # Ignore read errors

                time.sleep(0.1)  # Check frequently for responsive UI

            except Exception as e:
                print(f"Error monitoring RPiPlay process: {e}")
                break

        print("AirPlay monitor thread exiting")

    def get_status(self):
        """Get current AirPlay status."""
        if not self.rpiplay_available:
            return "unavailable"
        elif self.is_running:
            return "running"
        else:
            return "stopped"

    def set_device_name(self, name):
        """Set AirPlay device name."""
        self.airplay_name = name
        if self.is_running:
            # Restart to apply new name
            self.stop_airplay()
            time.sleep(1)
            self.start_airplay()

    def set_background_mode(self, mode):
        """Set background mode."""
        self.background_mode = mode
        if self.is_running:
            # Restart to apply new mode
            self.stop_airplay()
            time.sleep(1)
            self.start_airplay()

    def _ensure_x_server(self):
        """Ensure X server is running for video display."""
        # Check if X server is already running
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        if 'Xorg :0' in result.stdout or 'X :0' in result.stdout:
            print("X server is already running")
            return True

        print("Starting X server for video display...")
        try:
            # Start X server
            self.x_process = subprocess.Popen(
                ['sudo', '/usr/bin/X', ':0', '-nocursor', '-nolisten', 'tcp'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid
            )

            # Give X server time to start
            time.sleep(3)

            # Verify X server started
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            if 'Xorg :0' in result.stdout or 'X :0' in result.stdout:
                print("X server started successfully")
                return True
            else:
                print("Failed to start X server")
                return False

        except Exception as e:
            print(f"Error starting X server: {e}")
            return False

    def _restore_qt_display(self):
        """Restore Qt application to foreground after AirPlay disconnection."""
        try:
            # Clear framebuffer and restore Qt
            if os.path.exists('/dev/fb0'):
                print("Clearing framebuffer for Qt restoration...")
                subprocess.run(['sudo', '/home/pi/rpi_car_infotainment/scripts/clear-framebuffer.sh'],
                             timeout=5, capture_output=True)

            # Force Qt application refresh
            if self.main_window:
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(100, lambda: self.main_window.update())
                QTimer.singleShot(200, lambda: self.main_window.repaint())
                print("Requested Qt application refresh")

        except Exception as e:
            print(f"Error restoring Qt display: {e}")

    def cleanup(self):
        """Clean up resources."""
        print("Cleaning up AirPlay Overlay Manager...")
        self.stop_airplay()
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.stop_monitoring = True
            self.monitor_thread.join(timeout=2)
