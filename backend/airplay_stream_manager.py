# backend/airplay_stream_manager.py

import subprocess
import threading
import time
import os
import signal
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QPixmap, QPainter, QColor
from PyQt6.QtCore import Qt


class AirPlayStreamManager(QObject):
    """AirPlay manager that streams to a Qt widget instead of taking over display."""

    # Signals
    status_changed = pyqtSignal(str)  # "starting", "running", "stopped", "error"
    connection_changed = pyqtSignal(bool)  # True when device connects, False when disconnects
    show_stream_widget = pyqtSignal(bool)  # True to show stream widget, False to hide

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

        # Stream widget for showing AirPlay content
        self.stream_widget = None

        print(f"AirPlay Stream Manager initialized. RPiPlay available: {self.rpiplay_available}")

    def is_available(self):
        """Check if RPiPlay is available."""
        return self.rpiplay_available

    def start_airplay(self):
        """Start AirPlay service in discovery mode only - no display takeover."""
        if not self.rpiplay_available:
            print("Error: RPiPlay is not available")
            self.status_changed.emit("error")
            return False

        if self.is_running:
            print("AirPlay is already running")
            return True

        try:
            print("Starting AirPlay service in network discovery mode...")
            self.status_changed.emit("starting")

            # Start RPiPlay in audio-only mode for discovery
            # We'll handle video differently through Qt
            cmd = [
                self.rpiplay_path,
                "-n", self.airplay_name,
                "-a",  # Audio only - no video conflicts
                "-d"   # Enable debug output
            ]

            print(f"Starting RPiPlay with command: {' '.join(cmd)}")

            # No DISPLAY environment - pure network service
            env = os.environ.copy()
            if 'DISPLAY' in env:
                del env['DISPLAY']

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

            print(f"RPiPlay started in discovery mode with PID: {self.rpiplay_process.pid}")
            print("Device is discoverable for audio streaming")

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

            # Hide stream widget
            self.show_stream_widget.emit(False)

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
                    # Hide stream widget if device was connected
                    if self.device_connected:
                        self.show_stream_widget.emit(False)
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
                                    print("AirPlay device connected - showing stream widget")
                                    self.device_connected = True
                                    self.connection_changed.emit(True)
                                    self.show_stream_widget.emit(True)

                            elif any(keyword in line_lower for keyword in ["client disconnected", "connection closed", "stream stopped"]):
                                if self.device_connected:
                                    print("AirPlay device disconnected - hiding stream widget")
                                    self.device_connected = False
                                    self.connection_changed.emit(False)
                                    self.show_stream_widget.emit(False)
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

    def cleanup(self):
        """Clean up resources."""
        print("Cleaning up AirPlay Stream Manager...")
        self.stop_airplay()
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.stop_monitoring = True
            self.monitor_thread.join(timeout=2)
