# backend/airplay_manager.py

import subprocess
import threading
import time
import os
import signal
from PyQt6.QtCore import QObject, pyqtSignal


class AirPlayManager(QObject):
    """Manager for controlling RPiPlay AirPlay mirroring functionality."""

    # Signals
    status_changed = pyqtSignal(str)  # "starting", "running", "stopped", "error"
    connection_changed = pyqtSignal(bool)  # True when device connects, False when disconnects

    def __init__(self):
        super().__init__()

        # RPiPlay configuration
        self.rpiplay_path = "/home/pi/RPiPlay/build/rpiplay"
        self.airplay_name = "Car Display"
        self.background_mode = "auto"  # Options: auto, fill, fit, stretch

        # Check if we should copy RPiPlay to project directory for easier access
        self.project_rpiplay_path = "/home/pi/rpi_car_infotainment/rpiplay"
        self._ensure_rpiplay_available()

        # Process management
        self.rpiplay_process = None
        self.x_process = None  # X server process if we started it
        self.is_running = False
        self.monitor_thread = None
        self.stop_monitoring = False

        # Check if RPiPlay is available
        self.rpiplay_available = os.path.exists(self.rpiplay_path)
        if not self.rpiplay_available:
            print(f"Warning: RPiPlay not found at {self.rpiplay_path}")

    def _ensure_rpiplay_available(self):
        """Ensure RPiPlay is available, optionally copy to project directory."""
        if os.path.exists(self.rpiplay_path):
            # Original RPiPlay is available
            self.rpiplay_available = True

            # Optionally copy to project directory for easier access
            if not os.path.exists(self.project_rpiplay_path):
                try:
                    import shutil
                    shutil.copy2(self.rpiplay_path, self.project_rpiplay_path)
                    os.chmod(self.project_rpiplay_path, 0o755)  # Make executable
                    print(f"Copied RPiPlay to project directory: {self.project_rpiplay_path}")
                    # Use the project copy
                    self.rpiplay_path = self.project_rpiplay_path
                except Exception as e:
                    print(f"Could not copy RPiPlay to project directory: {e}")
                    # Continue using original path
            else:
                # Use existing project copy
                self.rpiplay_path = self.project_rpiplay_path
                print(f"Using existing RPiPlay in project directory: {self.project_rpiplay_path}")
        else:
            # Check if project copy exists
            if os.path.exists(self.project_rpiplay_path):
                self.rpiplay_path = self.project_rpiplay_path
                self.rpiplay_available = True
                print(f"Using RPiPlay from project directory: {self.project_rpiplay_path}")
            else:
                self.rpiplay_available = False
                print(f"Warning: RPiPlay not found at {self.rpiplay_path} or {self.project_rpiplay_path}")

    def is_available(self):
        """Check if RPiPlay is available on the system."""
        return self.rpiplay_available

    def start_airplay(self):
        """Start the RPiPlay AirPlay service."""
        if not self.rpiplay_available:
            print("Error: RPiPlay is not available")
            self.status_changed.emit("error")
            return False

        if self.is_running:
            print("AirPlay is already running")
            return True

        try:
            print("Starting RPiPlay AirPlay service...")
            self.status_changed.emit("starting")

            # First, ensure X server is running
            if not self._ensure_x_server():
                print("Failed to start X server")
                self.status_changed.emit("error")
                return False

            # Set up environment
            env = os.environ.copy()
            env['DISPLAY'] = ':0'

            # Start RPiPlay process with overlay mode - no fullscreen takeover
            cmd = [
                self.rpiplay_path,
                "-n", self.airplay_name,
                "-b", self.background_mode,
                "-w",  # Windowed mode instead of fullscreen
                "-d"   # Enable debug output
            ]

            print(f"Starting RPiPlay with command: {' '.join(cmd)}")

            self.rpiplay_process = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Combine stderr with stdout for easier monitoring
                preexec_fn=os.setsid,  # Create new process group
                universal_newlines=True,
                bufsize=1  # Line buffered
            )

            self.is_running = True
            self.status_changed.emit("running")

            # Start monitoring thread
            self.stop_monitoring = False
            self.monitor_thread = threading.Thread(target=self._monitor_process)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()

            print(f"RPiPlay started with PID: {self.rpiplay_process.pid}")

            # Give it a moment to initialize
            time.sleep(2)

            # Check if it's still running
            if self.rpiplay_process.poll() is not None:
                print("RPiPlay process exited immediately")
                self._read_process_output()
                self.status_changed.emit("error")
                self.is_running = False
                return False

            return True

        except Exception as e:
            print(f"Error starting RPiPlay: {e}")
            self.status_changed.emit("error")
            self.is_running = False
            return False

    def stop_airplay(self):
        """Stop the RPiPlay AirPlay service."""
        if not self.is_running or not self.rpiplay_process:
            print("AirPlay is not running")
            return True

        try:
            print("Stopping RPiPlay AirPlay service...")

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
            self.status_changed.emit("stopped")

            print("RPiPlay stopped successfully")
            return True

        except Exception as e:
            print(f"Error stopping RPiPlay: {e}")
            self.status_changed.emit("error")
            return False

    def restart_airplay(self):
        """Restart the RPiPlay AirPlay service."""
        print("Restarting RPiPlay AirPlay service...")
        self.stop_airplay()
        time.sleep(1)  # Brief pause between stop and start
        return self.start_airplay()

    def get_status(self):
        """Get the current status of the AirPlay service."""
        if not self.rpiplay_available:
            return "unavailable"
        elif self.is_running and self.rpiplay_process:
            return "running"
        else:
            return "stopped"

    def set_device_name(self, name):
        """Set the AirPlay device name."""
        self.airplay_name = name
        # If running, restart to apply the new name
        if self.is_running:
            self.restart_airplay()

    def set_background_mode(self, mode):
        """Set the background mode for video display."""
        if mode in ["auto", "fill", "fit", "stretch"]:
            self.background_mode = mode
            # If running, restart to apply the new mode
            if self.is_running:
                self.restart_airplay()
        else:
            print(f"Invalid background mode: {mode}")

    def _ensure_x_server(self):
        """Ensure X server is running on display :0."""
        try:
            # Check if X server is already running
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            if 'Xorg :0' in result.stdout or 'X :0' in result.stdout:
                print("X server is already running")
                return True

            print("Starting X server using startx...")

            # Create a minimal xinitrc for our use
            xinitrc_content = """#!/bin/bash
# Minimal xinitrc for AirPlay
exec sleep infinity
"""
            xinitrc_path = "/tmp/xinitrc_airplay"
            with open(xinitrc_path, 'w') as f:
                f.write(xinitrc_content)
            os.chmod(xinitrc_path, 0o755)

            # Use startx which handles permissions better
            env = os.environ.copy()
            env['DISPLAY'] = ':0'

            # Start X server using startx in background
            self.x_process = subprocess.Popen(
                ['startx', xinitrc_path, '--', ':0', '-nocursor', '-nolisten', 'tcp'],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid
            )

            # Give X server time to start
            print("Waiting for X server to start...")
            time.sleep(5)

            # Verify X server started
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            if 'Xorg :0' in result.stdout or 'X :0' in result.stdout:
                print("X server started successfully")
                return True
            else:
                print("Failed to start X server with startx")
                # Try alternative method with sudo
                return self._try_sudo_x_server()

        except Exception as e:
            print(f"Error starting X server: {e}")
            return self._try_sudo_x_server()

    def _try_sudo_x_server(self):
        """Try to start X server with sudo as fallback."""
        try:
            print("Trying to start X server with sudo...")

            # Try the custom X-airplay wrapper first
            if os.path.exists('/usr/local/bin/X-airplay'):
                print("Using X-airplay wrapper...")
                self.x_process = subprocess.Popen(
                    ['sudo', '/usr/local/bin/X-airplay', '-nocursor'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    preexec_fn=os.setsid
                )
            else:
                # Fallback to regular X server
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
                print("X server started successfully with sudo")
                return True
            else:
                print("Failed to start X server even with sudo")
                # Read error output for debugging
                if self.x_process:
                    try:
                        stdout, stderr = self.x_process.communicate(timeout=1)
                        if stderr:
                            print(f"X server error: {stderr}")
                    except:
                        pass
                return False

        except Exception as e:
            print(f"Error starting X server with sudo: {e}")
            return False

    def _read_process_output(self):
        """Read and print output from RPiPlay process for debugging."""
        if self.rpiplay_process and self.rpiplay_process.stdout:
            try:
                # Read any available output
                output = self.rpiplay_process.stdout.read()
                if output:
                    print(f"RPiPlay output: {output}")
            except Exception as e:
                print(f"Error reading RPiPlay output: {e}")

    def _monitor_process(self):
        """Monitor the RPiPlay process in a separate thread."""
        while not self.stop_monitoring and self.rpiplay_process:
            try:
                # Check if process is still running
                poll_result = self.rpiplay_process.poll()
                if poll_result is not None:
                    # Process has terminated
                    print(f"RPiPlay process terminated with code: {poll_result}")
                    self._read_process_output()  # Read any final output
                    self.is_running = False
                    self.rpiplay_process = None
                    self.status_changed.emit("stopped")
                    break

                # Read output for connection status and debugging
                if self.rpiplay_process.stdout:
                    try:
                        # Non-blocking read
                        import select
                        if select.select([self.rpiplay_process.stdout], [], [], 0.1)[0]:
                            line = self.rpiplay_process.stdout.readline()
                            if line:
                                print(f"RPiPlay: {line.strip()}")
                                # Look for connection indicators
                                if "client connected" in line.lower():
                                    self.connection_changed.emit(True)
                                elif "client disconnected" in line.lower():
                                    self.connection_changed.emit(False)
                    except:
                        pass  # Ignore read errors

                time.sleep(0.5)  # Check more frequently

            except Exception as e:
                print(f"Error monitoring RPiPlay process: {e}")
                break

    def cleanup(self):
        """Clean up resources when shutting down."""
        print("Cleaning up AirPlay manager...")
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
