import obd
import time
from PyQt6.QtCore import QThread, pyqtSignal

# Configure OBD logging (optional, helps debugging)
# obd.logger.setLevel(obd.logging.DEBUG)


class OBDManager(QThread):
    # Define signals to emit data
    connection_status = pyqtSignal(bool, str)  # connected (bool), status_message (str)
    data_updated = pyqtSignal(dict)  # Emits a dictionary of {command_name: value}

    def __init__(self, port=None, baudrate=None):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.connection = None
        self._is_running = True
        self._is_connected = False
        # Commands to monitor - Add more as needed!
        self.watch_commands = {
            obd.commands.SPEED,
            obd.commands.RPM,
            obd.commands.COOLANT_TEMP,
            obd.commands.FUEL_LEVEL,  # May not be supported on all cars
            # Add obd.commands.ENGINE_LOAD, obd.commands.INTAKE_TEMP, etc.
        }
        self.data = {
            cmd.name: None for cmd in self.watch_commands
        }  # Initialize data dict

    def run(self):
        print("OBDManager thread started.")
        while self._is_running:
            if not self._is_connected:
                self._connect()
                time.sleep(5)  # Wait before retrying connection
                continue  # Go back to start of loop to check _is_running

            # --- Query OBD Data ---
            try:
                updated_data = {}
                for cmd in self.watch_commands:
                    response = self.connection.query(
                        cmd, _force=True
                    )  # Force query even if not 'supported' initially

                    if not response.is_null():
                        value = response.value
                        # Handle different data types (value could be Quantity, string, etc.)
                        if isinstance(value, obd.UnitsAndScaling.Unit.Quantity):
                            current_val = round(
                                value.magnitude, 1
                            )  # Get numerical value, rounded
                            # Store value and optionally unit if needed later
                            self.data[cmd.name] = current_val
                            updated_data[cmd.name] = current_val
                            # print(f"OBD Read - {cmd.name}: {current_val} {str(value.units)}") # Debug
                        else:
                            self.data[cmd.name] = str(
                                value
                            )  # Store as string if not a Quantity
                            updated_data[cmd.name] = str(value)
                            # print(f"OBD Read - {cmd.name}: {value}") # Debug

                    else:
                        # print(f"OBD Read - {cmd.name}: No response or not supported")
                        if (
                            self.data.get(cmd.name) is not None
                        ):  # Clear old value if no response
                            self.data[cmd.name] = None
                            updated_data[cmd.name] = None

                if updated_data:
                    self.data_updated.emit(
                        updated_data
                    )  # Emit all updated values at once

                time.sleep(0.5)  # Query frequency (adjust as needed)

            except Exception as e:
                print(f"OBDManager error during query: {e}")
                # Handle specific errors like BrokenPipeError, SerialException etc.
                self._disconnect("Query Error")
                time.sleep(2)  # Wait a bit before attempting reconnect

        self._disconnect("Stopped")
        print("OBDManager thread finished.")

    def _connect(self):
        if self._is_connected:
            return True

        print(
            f"OBDManager: Attempting connection to port={self.port}, baud={self.baudrate}..."
        )
        try:
            # Use obd.Async() for non-blocking, but let's start with sync OBD()
            # Ensure python-obd supports the connection string format you need
            # For Bluetooth: Often requires pre-pairing and rfcomm binding in the OS
            # Example: sudo rfcomm bind /dev/rfcomm0 YOUR_BT_MAC_ADDRESS 1
            if self.port and self.baudrate:
                self.connection = obd.OBD(
                    portstr=self.port, baudrate=self.baudrate, fast=False, timeout=10
                )
            elif self.port:
                self.connection = obd.OBD(
                    portstr=self.port, fast=False, timeout=10
                )  # Auto baudrate
            else:
                self.connection = obd.OBD(
                    fast=False, timeout=10
                )  # Auto port and baudrate (might scan USB/BT)

            if self.connection.is_connected():
                status = self.connection.status()
                protocol = self.connection.protocol_name()
                print(f"OBDManager: Connected! Status: {status}, Protocol: {protocol}")
                self._is_connected = True
                self.connection_status.emit(True, f"Connected ({protocol})")

                # Add commands after connection
                # for cmd in self.watch_commands:
                #     self.connection.watch(cmd) # Might use too much CPU with sync OBD, query directly instead

                return True
            else:
                print("OBDManager: Connection failed.")
                self._is_connected = False
                self.connection_status.emit(False, "Connection Failed")
                self.connection.close()  # Ensure resources are released
                self.connection = None
                return False

        except Exception as e:
            print(f"OBDManager connection exception: {e}")
            self._is_connected = False
            self.connection_status.emit(False, f"Error: {e}")
            if self.connection:
                self.connection.close()
            self.connection = None
            return False

    def _disconnect(self, reason=""):
        if self.connection and self._is_connected:
            print(f"OBDManager: Disconnecting... Reason: {reason}")
            # for cmd in self.watch_commands: # Stop watching if using watch()
            #      try: self.connection.unwatch(cmd)
            #      except: pass
            self.connection.close()
        self._is_connected = False
        self.connection = None
        if reason != "Stopped":  # Don't emit disconnected if stopping intentionally
            self.connection_status.emit(False, f"Disconnected: {reason}")
        # Clear last known data? Optional.
        # self.data = {cmd.name: None for cmd in self.watch_commands}
        # self.data_updated.emit(self.data)

    def stop(self):
        print("OBDManager: Stop requested.")
        self._is_running = False
        # No need to explicitly disconnect here, run loop will handle it
