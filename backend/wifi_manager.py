# backend/wifi_manager.py

import subprocess
import re
import time
from PyQt6.QtCore import QThread, pyqtSignal, QTimer


class WiFiManager(QThread):
    """WiFi management using NetworkManager (nmcli)."""

    # Signals
    wifi_status_changed = pyqtSignal(bool)  # enabled/disabled
    networks_updated = pyqtSignal(list)  # list of available networks
    connection_changed = pyqtSignal(bool, str)  # connected, ssid

    def __init__(self):
        super().__init__()
        self._is_running = True
        self.current_ssid = None
        self.is_wifi_enabled = False
        self.available_networks = []

        # Timer for periodic updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(5000)  # Update every 5 seconds

    def run(self):
        """Main thread loop for WiFi monitoring."""
        print("WiFiManager thread started.")

        # Initial status check
        self.update_status()

        while self._is_running:
            time.sleep(1)

        print("WiFiManager thread finished.")

    def stop(self):
        """Stop the WiFi manager thread."""
        print("WiFiManager: Stop requested.")
        self._is_running = False
        if self.update_timer:
            self.update_timer.stop()

    def update_status(self):
        """Update WiFi status and emit signals."""
        try:
            # Check if WiFi is enabled
            self.is_wifi_enabled = self.is_wifi_radio_enabled()
            self.wifi_status_changed.emit(self.is_wifi_enabled)

            if self.is_wifi_enabled:
                # Get current connection
                current_ssid = self.get_current_ssid()
                if current_ssid != self.current_ssid:
                    self.current_ssid = current_ssid
                    self.connection_changed.emit(bool(current_ssid), current_ssid or "")

                # Scan for networks (less frequently)
                networks = self.scan_networks()
                if networks != self.available_networks:
                    self.available_networks = networks
                    self.networks_updated.emit(networks)
            else:
                if self.current_ssid:
                    self.current_ssid = None
                    self.connection_changed.emit(False, "")

        except Exception as e:
            print(f"WiFiManager update error: {e}")

    def is_wifi_radio_enabled(self):
        """Check if WiFi radio is enabled."""
        try:
            result = subprocess.run(
                ["nmcli", "radio", "wifi"],
                capture_output=True, text=True, timeout=5
            )
            return result.stdout.strip() == "enabled"
        except Exception as e:
            print(f"Error checking WiFi radio status: {e}")
            return False

    def enable_wifi(self):
        """Enable WiFi radio."""
        try:
            result = subprocess.run(
                ["sudo", "nmcli", "radio", "wifi", "on"],
                capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0
        except Exception as e:
            print(f"Error enabling WiFi: {e}")
            return False

    def disable_wifi(self):
        """Disable WiFi radio."""
        try:
            result = subprocess.run(
                ["sudo", "nmcli", "radio", "wifi", "off"],
                capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0
        except Exception as e:
            print(f"Error disabling WiFi: {e}")
            return False

    def get_current_ssid(self):
        """Get the currently connected WiFi SSID."""
        try:
            # First try to get active connection
            result = subprocess.run(
                ["nmcli", "-t", "-f", "NAME,TYPE", "connection", "show", "--active"],
                capture_output=True, text=True, timeout=5
            )

            # Look for WiFi connections
            for line in result.stdout.strip().split('\n'):
                if line and ':802-11-wireless' in line:
                    ssid = line.split(':')[0]
                    return ssid if ssid else None

            # Fallback: check device status
            result = subprocess.run(
                ["nmcli", "-t", "-f", "DEVICE,STATE,CONNECTION", "dev", "status"],
                capture_output=True, text=True, timeout=5
            )

            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split(':')
                    if len(parts) >= 3 and 'wifi' in parts[0] and 'connected' in parts[1]:
                        connection_name = parts[2]
                        return connection_name if connection_name else None

            return None
        except Exception as e:
            print(f"Error getting current SSID: {e}")
            return None

    def scan_networks(self):
        """Scan for available WiFi networks."""
        try:
            # Trigger a rescan
            subprocess.run(
                ["nmcli", "dev", "wifi", "rescan"],
                capture_output=True, timeout=10
            )

            # Get the list
            result = subprocess.run(
                ["nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY", "dev", "wifi"],
                capture_output=True, text=True, timeout=10
            )

            networks = []
            seen_ssids = set()

            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split(':')
                    if len(parts) >= 3:
                        ssid = parts[0]
                        signal = parts[1]
                        security = parts[2]

                        # Skip empty SSIDs and duplicates
                        if ssid and ssid not in seen_ssids:
                            seen_ssids.add(ssid)
                            networks.append({
                                'ssid': ssid,
                                'signal': int(signal) if signal.isdigit() else 0,
                                'security': security,
                                'secured': bool(security and security != '--')
                            })

            # Sort by signal strength
            networks.sort(key=lambda x: x['signal'], reverse=True)
            return networks

        except Exception as e:
            print(f"Error scanning networks: {e}")
            return []

    def connect_to_network(self, ssid, password=None):
        """Connect to a WiFi network."""
        try:
            cmd = ["sudo", "nmcli", "dev", "wifi", "connect", ssid]
            if password:
                cmd.extend(["password", password])

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30
            )

            success = result.returncode == 0
            if success:
                print(f"Successfully connected to {ssid}")
            else:
                print(f"Failed to connect to {ssid}: {result.stderr}")

            return success, result.stderr if not success else ""

        except Exception as e:
            error_msg = f"Error connecting to {ssid}: {e}"
            print(error_msg)
            return False, error_msg

    def disconnect_current(self):
        """Disconnect from current WiFi network."""
        try:
            # Get the current connection name
            result = subprocess.run(
                ["nmcli", "-t", "-f", "NAME", "connection", "show", "--active"],
                capture_output=True, text=True, timeout=5
            )

            for line in result.stdout.strip().split('\n'):
                if line:
                    # Try to disconnect this connection
                    disconnect_result = subprocess.run(
                        ["sudo", "nmcli", "connection", "down", line],
                        capture_output=True, text=True, timeout=10
                    )
                    if disconnect_result.returncode == 0:
                        print(f"Disconnected from {line}")
                        return True

            return False

        except Exception as e:
            print(f"Error disconnecting: {e}")
            return False

    def forget_network(self, ssid):
        """Forget a saved WiFi network."""
        try:
            result = subprocess.run(
                ["sudo", "nmcli", "connection", "delete", ssid],
                capture_output=True, text=True, timeout=10
            )

            success = result.returncode == 0
            if success:
                print(f"Forgot network {ssid}")
            else:
                print(f"Failed to forget {ssid}: {result.stderr}")

            return success

        except Exception as e:
            print(f"Error forgetting network {ssid}: {e}")
            return False

    def get_saved_networks(self):
        """Get list of saved WiFi networks."""
        try:
            result = subprocess.run(
                ["nmcli", "-t", "-f", "NAME,TYPE", "connection", "show"],
                capture_output=True, text=True, timeout=5
            )

            networks = []
            for line in result.stdout.strip().split('\n'):
                if line and ':802-11-wireless' in line:
                    name = line.split(':')[0]
                    networks.append(name)

            return networks

        except Exception as e:
            print(f"Error getting saved networks: {e}")
            return []
