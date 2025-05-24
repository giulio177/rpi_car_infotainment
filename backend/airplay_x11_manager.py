# backend/airplay_x11_manager.py

import subprocess
import threading
import time
import os
import signal
from PyQt6.QtCore import QObject, pyqtSignal, QTimer


class AirPlayX11Manager(QObject):
    """AirPlay manager that uses RPiPlay with X11 support for video mirroring."""

    # Signals
    status_changed = pyqtSignal(str)  # "starting", "running", "stopped", "error"
    connection_changed = pyqtSignal(bool)  # True when device connects, False when disconnects
    video_window_ready = pyqtSignal()  # Emitted when video window is ready
    show_video_screen = pyqtSignal()  # Request to show the video screen

    def __init__(self, main_window=None):
        super().__init__()

        self.main_window = main_window
        self.rpiplay_path = "/home/pi/RPiPlay/build/rpiplay"
        self.airplay_name = "Car Display"
        self.background_mode = "auto"

        # Check if RPiPlay exists
        self.rpiplay_available = os.path.exists(self.rpiplay_path)

        # Process management
        self.rpiplay_process = None
        self.x_process = None
        self.is_running = False
        self.monitor_thread = None
        self.stop_monitoring = False
        self.device_connected = False

        # Video window management
        self.video_window_id = None
        self.video_area_geometry = None

        print(f"AirPlay X11 Manager initialized. RPiPlay available: {self.rpiplay_available}")

    def is_available(self):
        """Check if RPiPlay is available."""
        return self.rpiplay_available

    def start_airplay(self):
        """Start AirPlay service with X11 support."""
        if not self.rpiplay_available:
            print("Error: RPiPlay is not available")
            self.status_changed.emit("error")
            return False

        if self.is_running:
            print("AirPlay is already running")
            return True

        try:
            print("Starting AirPlay service with X11 support...")
            self.status_changed.emit("starting")

            # Ensure X server is running
            if not self._ensure_x_server():
                print("Failed to start X server")
                self.status_changed.emit("error")
                return False

            # Set up environment for X11
            env = os.environ.copy()
            env['DISPLAY'] = ':0'
            env['GST_DEBUG'] = '2'  # Enable some GStreamer debugging

            # Start RPiPlay with X11 backend
            cmd = [
                self.rpiplay_path,
                "-n", self.airplay_name,
                "-b", "auto",  # Let GStreamer choose the best sink (should be X11)
                "-d"           # Enable debug output
            ]

            print(f"Starting RPiPlay with command: {' '.join(cmd)}")
            print("Environment: DISPLAY=:0")

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
            print("Device should be discoverable as 'Car Display'")

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

    def _ensure_x_server(self):
        """Ensure X server is running."""
        # Check if X server is already running
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        if 'Xorg :0' in result.stdout or 'X :0' in result.stdout:
            print("X server is already running")
            return True

        print("Starting X server for AirPlay video...")
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

    def _monitor_process(self):
        """Monitor RPiPlay process and handle connection events."""
        while not self.stop_monitoring and self.rpiplay_process:
            try:
                # Check if process is still running
                if self.rpiplay_process.poll() is not None:
                    print("RPiPlay process has exited")
                    self.is_running = False
                    self.status_changed.emit("stopped")
                    if self.device_connected:
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
                                    print("AirPlay device connected - switching to video screen")
                                    self.device_connected = True
                                    self.connection_changed.emit(True)
                                    # Request to show the video screen
                                    self.show_video_screen.emit()
                                    # Give the video window time to appear, then position it
                                    QTimer.singleShot(3000, self._position_video_window)

                            elif any(keyword in line_lower for keyword in ["client disconnected", "connection closed", "stream stopped"]):
                                if self.device_connected:
                                    print("AirPlay device disconnected")
                                    self.device_connected = False
                                    self.connection_changed.emit(False)
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

    def set_video_area_geometry(self, geometry):
        """Set the geometry where the video should be positioned."""
        self.video_area_geometry = geometry
        print(f"Video area geometry set: {geometry}")

    def _position_video_window(self):
        """Position the RPiPlay video window in the designated area."""
        if not self.video_area_geometry:
            print("No video area geometry set, cannot position window")
            return

        try:
            # Find the RPiPlay window
            result = subprocess.run([
                'xwininfo', '-root', '-tree'
            ], capture_output=True, text=True, env={'DISPLAY': ':0'})

            # Look for RPiPlay window in the output
            lines = result.stdout.split('\n')
            rpiplay_window_id = None

            for line in lines:
                if 'rpiplay' in line.lower() or 'airplay' in line.lower():
                    # Extract window ID from the line
                    parts = line.strip().split()
                    if parts and parts[0].startswith('0x'):
                        rpiplay_window_id = parts[0]
                        break

            if rpiplay_window_id:
                print(f"Found RPiPlay window: {rpiplay_window_id}")
                self.video_window_id = rpiplay_window_id

                # Position and resize the window
                geometry = self.video_area_geometry
                subprocess.run([
                    'wmctrl', '-i', '-r', rpiplay_window_id,
                    '-e', f"0,{geometry['x']},{geometry['y']},{geometry['width']},{geometry['height']}"
                ], env={'DISPLAY': ':0'})

                # Remove window decorations
                subprocess.run([
                    'wmctrl', '-i', '-r', rpiplay_window_id, '-b', 'remove,maximized_vert,maximized_horz'
                ], env={'DISPLAY': ':0'})

                print(f"Positioned video window at {geometry}")
                self.video_window_ready.emit()
            else:
                print("RPiPlay window not found, retrying in 2 seconds...")
                QTimer.singleShot(2000, self._position_video_window)

        except Exception as e:
            print(f"Error positioning video window: {e}")
            # Retry after a delay
            QTimer.singleShot(2000, self._position_video_window)

    def cleanup(self):
        """Clean up resources."""
        print("Cleaning up AirPlay X11 Manager...")
        self.stop_airplay()
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.stop_monitoring = True
            self.monitor_thread.join(timeout=2)

        # Clean up X server if we started it
        if hasattr(self, 'x_process') and self.x_process:
            try:
                print("Stopping X server...")
                os.killpg(os.getpgid(self.x_process.pid), signal.SIGTERM)
                self.x_process.wait(timeout=3)
            except:
                pass  # Ignore cleanup errors
