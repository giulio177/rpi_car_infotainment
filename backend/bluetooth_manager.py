# backend/bluetooth_manager.py

import time
import traceback
import dbus
from PyQt6.QtCore import QThread, pyqtSignal, QVariant, QObject, pyqtSlot
from PyQt6.QtDBus import QDBusConnection, QDBusInterface, QDBusMessage, QDBusVariant, QDBusObjectPath

# Constants for BlueZ D-Bus
BLUEZ_SERVICE = "org.bluez"
DBUS_OM_IFACE = "org.freedesktop.DBus.ObjectManager"
DBUS_PROP_IFACE = "org.freedesktop.DBus.Properties"

ADAPTER_IFACE = "org.bluez.Adapter1"
DEVICE_IFACE = "org.bluez.Device1"
MEDIA_PLAYER_IFACE = "org.bluez.MediaPlayer1"
MEDIA_CONTROL_IFACE = "org.bluez.MediaControl1"

# Constants for UPower D-Bus
UPOWER_SERVICE = "org.freedesktop.UPower"
UPOWER_PATH = "/org/freedesktop/UPower"
UPOWER_IFACE = "org.freedesktop.UPower"
UPOWER_DEVICE_IFACE = "org.freedesktop.UPower.Device"


# Helper to convert QVariant dictionary/value to Python types recursively
def qvariant_dict_to_python(variant_value):
    """
    Recursively converts a QVariant containing basic types, lists, or
    dictionaries (including nested ones) into standard Python types.
    """
    if not isinstance(variant_value, QVariant):
        if isinstance(variant_value, dict):
            py_dict = {}
            for k, v in variant_value.items():
                py_dict[k] = qvariant_dict_to_python(v)
            return py_dict
        elif isinstance(variant_value, list):
            return [qvariant_dict_to_python(item) for item in variant_value]
        else:
            return variant_value

    value = variant_value.value()

    if isinstance(value, dict):
        py_dict = {}
        for k, v in value.items():
            py_dict[k] = qvariant_dict_to_python(v)
        return py_dict
    elif isinstance(value, list):
        return [qvariant_dict_to_python(item) for item in value]
    else:
        return value


class BluetoothManager(QThread):
    # Signals
    connection_changed = pyqtSignal(bool, str)
    battery_updated = pyqtSignal(object)  # Use object for None support
    media_properties_changed = pyqtSignal(dict)
    playback_status_changed = pyqtSignal(str)
    devices_discovered = pyqtSignal(list) # List of dictionaries {path, name, address, paired, connected, trusted}

    def __init__(self, settings_manager=None):
        super().__init__()
        print("DEBUG: BluetoothManager.__init__")
        self.settings_manager = settings_manager
        self._is_running = True
        
        # Check emulation mode
        self.emulation_mode = False
        if self.settings_manager:
            self.emulation_mode = self.settings_manager.get("emulation_mode") or False
            
        if self.emulation_mode:
            print("[BT Manager] Running in EMULATION MODE (Mock Data)")
            self.bus = None # No DBus
            # Mock Data State
            self.mock_devices = [
                {"path": "/org/bluez/hci0/dev_11_22_33_44_55_66", "name": "Pixel 7 Pro", "address": "11:22:33:44:55:66", "paired": True, "connected": False, "trusted": True, "rssi": -55},
                {"path": "/org/bluez/hci0/dev_AA_BB_CC_DD_EE_FF", "name": "iPhone 15", "address": "AA:BB:CC:DD:EE:FF", "paired": False, "connected": False, "trusted": False, "rssi": -70},
                {"path": "/org/bluez/hci0/dev_12_34_56_78_90_AB", "name": "JBL Speaker", "address": "12:34:56:78:90:AB", "paired": True, "connected": False, "trusted": True, "rssi": -40},
            ]
            self.mock_scanning = False
            self.mock_discoverable = False
        else:
            self.bus = QDBusConnection.systemBus()

        # State variables
        self.adapter_path = None
        self.connected_device_path = None
        self.connected_device_name = "Disconnected"
        self.current_battery = None
        self.media_player_path = None
        self.media_properties = {}
        self.playback_status = "stopped"
        self.dbus_receiver = QObject()  # Potentially needed if sender context required
        self.scanning = False

    def find_adapter(self):
        print("DEBUG: BluetoothManager.find_adapter - Entered")
        """Finds the first available Bluetooth adapter."""
        om = QDBusInterface(BLUEZ_SERVICE, "/", DBUS_OM_IFACE, self.bus)
        print("DEBUG: BluetoothManager.find_adapter - Calling GetManagedObjects...")
        reply_message = om.call("GetManagedObjects")
        print(
            f"DEBUG: BluetoothManager.find_adapter - GetManagedObjects returned type: {reply_message.type()}"
        )
        if reply_message.type() == QDBusMessage.MessageType.ErrorMessage:
            print(
                "BT Manager: Error getting managed objects:",
                reply_message.errorMessage(),
            )
            return None
        if not reply_message.arguments():
            print("BT Manager: GetManagedObjects reply has no arguments.")
            return None

        objects_dict_variant = reply_message.arguments()[0]
        objects_dict = qvariant_dict_to_python(objects_dict_variant)

        print(
            f"DEBUG: BluetoothManager.find_adapter - Processing {len(objects_dict)} managed objects..."
        )
        for path, interfaces in objects_dict.items():
            if "org.bluez.Adapter1" in interfaces:
                print(f"BT Manager: Found adapter at {path}")
                return path
        print("BT Manager: No Bluetooth adapter found.")
        return None

    def _get_upower_device_path(self, device_bluez_path):
        """Tries to find the corresponding UPower D-Bus path for a BlueZ device path."""
        if not device_bluez_path:
            return None
        try:
            mac_suffix = device_bluez_path.split("/")[
                -1
            ]  # Gets 'dev_XX_XX_XX_XX_XX_XX'

            # --- CORRECTED: Construct path based on observed format ---
            upower_path = f"/org/freedesktop/UPower/devices/phone_{mac_suffix}"
            # --- END CORRECTION ---

            print(f"DEBUG: Constructed UPower path guess: {upower_path}")

            # Verify the path exists on UPower's D-Bus interface
            upower_obj = QDBusInterface(
                UPOWER_SERVICE, upower_path, DBUS_PROP_IFACE, self.bus
            )
            reply = upower_obj.call(
                "Get", UPOWER_DEVICE_IFACE, "Type"
            )  # Check if object/interface/prop exists

            if reply.type() != QDBusMessage.MessageType.ErrorMessage:
                print(f"DEBUG: Found matching UPower device path: {upower_path}")
                return upower_path
            else:
                # Optional: Try other common formats as fallbacks if needed
                print(
                    f"DEBUG: UPower path {upower_path} not found/valid for {mac_suffix}. Error: {reply.errorMessage()}"
                )
                return None
        except Exception as e:
            print(f"ERROR finding UPower path for {device_bluez_path}: {e}")
            return None

    def _get_battery_from_upower(self, upower_device_path):
        """Queries UPower D-Bus for battery percentage."""
        if not upower_device_path:
            return None
        try:
            upower_props = QDBusInterface(
                UPOWER_SERVICE, upower_device_path, DBUS_PROP_IFACE, self.bus
            )
            reply_message = upower_props.call("Get", UPOWER_DEVICE_IFACE, "Percentage")

            if (
                reply_message.type() != QDBusMessage.MessageType.ErrorMessage
                and reply_message.arguments()
            ):
                percentage_variant = reply_message.arguments()[0]
                percentage = qvariant_dict_to_python(percentage_variant)
                if isinstance(percentage, (float, int)):
                    print(
                        f"DEBUG: Battery from UPower ({upower_device_path}): {percentage}"
                    )
                    return int(percentage)  # Return as integer
                else:
                    print(
                        f"DEBUG: UPower Percentage property was unexpected type: {type(percentage)}"
                    )
            else:
                print(
                    f"DEBUG: Failed to get Percentage from UPower {upower_device_path}: {reply_message.errorMessage() if reply_message.type() == QDBusMessage.MessageType.ErrorMessage else 'No arguments'}"
                )
            return None
        except Exception as e:
            print(f"ERROR getting UPower battery from {upower_device_path}: {e}")
            return None

    def _reset_connection_state(self):
        """Resets all connection and media state variables and emits signals."""
        print("BT Manager: Resetting connection state...")
        
        # Disconnect signal if active
        if self.media_player_path and self.bus and self.bus.isConnected():
            try:
                self.bus.disconnect(
                    BLUEZ_SERVICE,
                    self.media_player_path,
                    DBUS_PROP_IFACE,
                    "PropertiesChanged",
                    self.on_media_properties_changed,
                )
            except Exception:
                pass # Ignore errors during disconnect

        self.connected_device_path = None
        self.connected_device_name = "Disconnected"
        self.current_battery = None
        self.media_player_path = None
        self.media_properties = {}
        self.playback_status = "stopped"
        
        print("DEBUG: Emitting connection_changed(False, ...)")
        self.connection_changed.emit(False, "Disconnected")
        print("DEBUG: Emitting battery_updated(None)")
        self.battery_updated.emit(None)
        print("DEBUG: Emitting media_properties_changed({})")
        self.media_properties_changed.emit({})
        print("DEBUG: Emitting playback_status_changed('stopped')")
        self.playback_status_changed.emit("stopped")

    def process_device_properties(self, path, properties):
        """Checks device properties. Tries UPower for battery if BlueZ property is missing."""
        try:
            is_connected = properties.get("Connected", False)
            device_name = properties.get("Name", "Unknown Device")
            alias = properties.get("Alias", device_name)
            battery = properties.get("Battery", None)  # BlueZ property

            upower_battery = None
            if is_connected:
                upower_path = self._get_upower_device_path(path)
                if upower_path:
                    upower_battery = self._get_battery_from_upower(upower_path)

            final_battery = upower_battery if battery is None else battery
            
            # Se siamo connessi al dispositivo X, ma riceviamo proprietà per X che dicono Connected=False
            if self.connected_device_path == path and not is_connected:
                 print(f"BT Manager: Detected disconnection via properties for {alias}")
                 self._reset_connection_state()
                 return

            if is_connected:
                battery_changed = final_battery != self.current_battery
                
                # Se è una nuova connessione O se è un dispositivo diverso da quello che pensavamo
                newly_connected = (self.connected_device_path != path)

                if newly_connected:
                    # Se eravamo connessi a qualcos'altro, resettiamo prima
                    if self.connected_device_path:
                        print(f"BT Manager: Switching connection from {self.connected_device_path} to {path}")
                        self._reset_connection_state()
                        
                    print(f"BT Manager: Device connected - {alias} ({path})")
                    self.connected_device_path = path
                    self.connected_device_name = alias
                    self.current_battery = final_battery
                    print(
                        f"DEBUG: Emitting connection_changed(True, '{self.connected_device_name}')"
                    )
                    self.connection_changed.emit(True, self.connected_device_name)
                    print(f"DEBUG: Emitting battery_updated('{self.current_battery}')")
                    self.battery_updated.emit(self.current_battery)
                    self.find_media_player(path)  # Check for player on connect
                elif battery_changed and self.connected_device_path == path:
                    print(f"BT Manager: Battery updated for {alias} to {final_battery}")
                    self.current_battery = final_battery
                    print(f"DEBUG: Emitting battery_updated('{self.current_battery}')")
                    self.battery_updated.emit(self.current_battery)

        except Exception as e:
            print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print(f"ERROR in process_device_properties for path {path}: {e}")
            traceback.print_exc()
            print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

    def find_media_player(self, device_path_hint=None):
        # ... (Implementation remains the same as the previous working version) ...
        print(f"DEBUG: BluetoothManager.find_media_player - Hint: {device_path_hint}")
        om = QDBusInterface(BLUEZ_SERVICE, "/", DBUS_OM_IFACE, self.bus)
        reply_message = om.call("GetManagedObjects")
        if (
            reply_message.type() == QDBusMessage.MessageType.ErrorMessage
        ):  # ... error handling ...
            return False
        if not reply_message.arguments():  # ... error handling ...
            return False

        objects_dict = qvariant_dict_to_python(reply_message.arguments()[0])
        found_player_path = None
        # ... (Loop through objects, find matching player) ...
        for path, interfaces in objects_dict.items():
            if MEDIA_PLAYER_IFACE in interfaces:
                player_props = interfaces.get(MEDIA_PLAYER_IFACE, {})
                player_device = player_props.get("Device", "")
                if device_path_hint and player_device == device_path_hint:
                    found_player_path = path
                    break
                elif not device_path_hint and not found_player_path:
                    if player_device and player_device.startswith("/org/bluez/hci"):
                        found_player_path = path

        if found_player_path and found_player_path != self.media_player_path:
            print(f"BT Manager: Media player activated at {found_player_path}")
            if self.media_player_path and self.bus.isConnected():
                self.bus.disconnect(
                    BLUEZ_SERVICE,
                    self.media_player_path,
                    DBUS_PROP_IFACE,
                    "PropertiesChanged",
                    self.on_media_properties_changed,
                )
            self.media_player_path = found_player_path
            self.monitor_media_player(found_player_path)
            return True
        elif not found_player_path and self.media_player_path:
            print("BT Manager: Active media player seems to be gone.")
            if self.media_player_path and self.bus.isConnected():
                self.bus.disconnect(
                    BLUEZ_SERVICE,
                    self.media_player_path,
                    DBUS_PROP_IFACE,
                    "PropertiesChanged",
                    self.on_media_properties_changed,
                )
            # ... (clear state and emit signals) ...
            self.media_player_path = None
            self.media_properties = {}
            self.playback_status = "stopped"
            self.media_properties_changed.emit({})
            self.playback_status_changed.emit("stopped")
            return False
        # print(f"DEBUG: BluetoothManager.find_media_player - Result: Found={found_player_path is not None}, CurrentPlayerPath={self.media_player_path}")
        return found_player_path is not None

    def monitor_media_player(self, player_path):
        # ... (Implementation remains the same - Get initial props via GetAll on Properties IFace) ...
        print(f"DEBUG: BluetoothManager.monitor_media_player - Path: {player_path}")
        if not player_path:
            return
        props_iface = QDBusInterface(
            BLUEZ_SERVICE, player_path, DBUS_PROP_IFACE, self.bus
        )
        reply_message = props_iface.call("GetAll", MEDIA_PLAYER_IFACE)
        if (
            reply_message.type() != QDBusMessage.MessageType.ErrorMessage
            and reply_message.arguments()
        ):
            initial_props = qvariant_dict_to_python(reply_message.arguments()[0])
            self.update_media_state(initial_props)
        # else: # Error logging

    # --- Slots (Only the working InterfacesRemoved is connected/used by signals) ---

    # Method kept, but not connected to failing signal
    # @pyqtSlot(str, object, "QStringList")
    def on_media_properties_changed(
        self, interface_name, changed_properties_obj, invalidated_properties
    ):
        print("!!! on_media_properties_changed called unexpectedly !!!")
        pass

    # This method IS called by polling loop and initial setup
    def update_media_state(self, properties):
        """Updates internal state and emits signals based on media properties. Assumes 'properties' is Python dict."""
        # ... (Implementation remains the same - compares with self state, emits signals) ...
        track_changed = False
        status_changed = False
        position_changed = False
        position_value = properties.get("Position", -1)
        if "Track" in properties:
            track_info = properties.get("Track", {})
            if isinstance(track_info, dict) and track_info != self.media_properties.get(
                "Track", {}
            ):
                track_changed = True
                self.media_properties["Track"] = track_info
        if "Status" in properties:
            status = properties.get("Status", "stopped")
            if status != self.playback_status:
                status_changed = True
                self.playback_status = status
        if "Position" in properties:
            if position_value >= 0 and position_value != self.media_properties.get(
                "Position", -1
            ):
                position_changed = True
            if "Track" in self.media_properties or track_changed:
                self.media_properties["Position"] = position_value
        # Emit signals
        if status_changed:
            self.playback_status_changed.emit(self.playback_status)
        if track_changed or (position_changed and self.playback_status == "playing"):
            if "Position" in properties:
                self.media_properties["Position"] = position_value
            self.media_properties_changed.emit(self.media_properties)

    # Method kept, but not connected to failing signal
    # @pyqtSlot(str, object)
    def on_interfaces_added(self, path, interfaces_and_properties_obj):
        print("!!! on_interfaces_added called unexpectedly !!!")
        pass

    # Keep working slot connected to signal
    @pyqtSlot(str, "QStringList")
    def on_interfaces_removed(self, path, interfaces):
        """Handles D-Bus InterfacesRemoved signal."""
        # ... (Implementation remains the same) ...
        try:
            if DEVICE_IFACE in interfaces and path == self.connected_device_path:
                self.process_device_properties(path, {"Connected": False})
            elif MEDIA_PLAYER_IFACE in interfaces and path == self.media_player_path:
                print("DEBUG: Clearing media player state due to InterfacesRemoved")
                self.media_player_path = None
                self.media_properties = {}
                self.playback_status = "stopped"
                self.media_properties_changed.emit({})
                self.playback_status_changed.emit("stopped")
        except Exception as e:  # ... Error handling ...
            print(f"ERROR in on_interfaces_removed: {e}")

    # Method kept, but not connected to failing signal
    # @pyqtSlot(str, object, "QStringList")
    def on_device_properties_changed(
        self, interface_name, changed_properties_obj, invalidated_properties
    ):
        print("!!! on_device_properties_changed called unexpectedly !!!")
        pass

    # --- Scanning and Device Management Methods ---

    def start_scan(self):
        """Starts device discovery."""
        if self.emulation_mode:
            print("[BT Manager - Mock] Scanning started...")
            self.mock_scanning = True
            return True

        if not self.adapter_path:
            self.adapter_path = self.find_adapter()
        
        if not self.adapter_path:
            print("BT Manager: No adapter found to start scan.")
            return False

        try:
            adapter = QDBusInterface(BLUEZ_SERVICE, self.adapter_path, ADAPTER_IFACE, self.bus)
            reply = adapter.call("StartDiscovery")
            if reply.type() != QDBusMessage.MessageType.ErrorMessage:
                print("BT Manager: Scanning started.")
                self.scanning = True
                return True
            else:
                print(f"BT Manager: Failed to start scan: {reply.errorMessage()}")
                return False
        except Exception as e:
            print(f"BT Manager: Exception starting scan: {e}")
            return False

    def stop_scan(self):
        """Stops device discovery."""
        if self.emulation_mode:
            print("[BT Manager - Mock] Scanning stopped.")
            self.mock_scanning = False
            return True

        if not self.adapter_path:
            return False

        try:
            adapter = QDBusInterface(BLUEZ_SERVICE, self.adapter_path, ADAPTER_IFACE, self.bus)
            reply = adapter.call("StopDiscovery")
            if reply.type() != QDBusMessage.MessageType.ErrorMessage:
                print("BT Manager: Scanning stopped.")
                self.scanning = False
                return True
            else:
                # "No discovery started" is a common error, treat as success
                if "No discovery started" in reply.errorMessage():
                     self.scanning = False
                     return True
                print(f"BT Manager: Failed to stop scan: {reply.errorMessage()}")
                return False
        except Exception as e:
            print(f"BT Manager: Exception stopping scan: {e}")
            return False

    def get_available_devices(self):
        """Returns a list of all known devices (paired or discovered)."""
        if self.emulation_mode:
            # Add random device occasionally if scanning
            if self.mock_scanning and time.time() % 5 < 1 and len(self.mock_devices) < 5:
                 self.mock_devices.append({
                     "path": f"/org/bluez/hci0/dev_MOCK_{int(time.time())}", 
                     "name": f"New Mock Device {len(self.mock_devices)}", 
                     "address": f"FF:FF:FF:00:00:{len(self.mock_devices)}", 
                     "paired": False, 
                     "connected": False, 
                     "trusted": False, 
                     "rssi": -80 + (int(time.time()) % 20)
                 })
            return self.mock_devices

        devices = []
        try:
            om = QDBusInterface(BLUEZ_SERVICE, "/", DBUS_OM_IFACE, self.bus)
            reply = om.call("GetManagedObjects")
            
            if reply.type() == QDBusMessage.MessageType.ErrorMessage:
                return []

            objects = qvariant_dict_to_python(reply.arguments()[0])
            
            for path, interfaces in objects.items():
                if DEVICE_IFACE in interfaces:
                    props = interfaces.get(DEVICE_IFACE, {})
                    address = props.get("Address", "")
                    name = props.get("Name", props.get("Alias", address))
                    paired = props.get("Paired", False)
                    connected = props.get("Connected", False)
                    trusted = props.get("Trusted", False)
                    rssi = props.get("RSSI", -100) # Signal strength

                    devices.append({
                        "path": path,
                        "name": name,
                        "address": address,
                        "paired": paired,
                        "connected": connected,
                        "trusted": trusted,
                        "rssi": rssi
                    })
            
            # Sort by connected (first), then paired (second), then RSSI (desc)
            devices.sort(key=lambda x: (not x['connected'], not x['paired'], -x['rssi']))
            return devices

        except Exception as e:
            print(f"BT Manager: Error getting available devices: {e}")
            return []

    def pair_device(self, device_path):
        """Pairs with a device."""
        if self.emulation_mode:
            print(f"[BT Manager - Mock] Pairing with {device_path}...")
            # Find and update mock device
            for dev in self.mock_devices:
                if dev['path'] == device_path:
                    dev['paired'] = True
                    dev['trusted'] = True
                    break
            return True, "Pairing initiated"

        try:
            device = QDBusInterface(BLUEZ_SERVICE, device_path, DEVICE_IFACE, self.bus)
            print(f"BT Manager: Pairing with {device_path}...")
            reply = device.call("Pair")
            
            if reply.type() != QDBusMessage.MessageType.ErrorMessage:
                print(f"BT Manager: Pair request sent/successful for {device_path}")
                # Often good to set Trusted after pairing
                props = QDBusInterface(BLUEZ_SERVICE, device_path, DBUS_PROP_IFACE, self.bus)
                props.call("Set", DEVICE_IFACE, "Trusted", QDBusVariant(True))
                return True, "Pairing initiated"
            else:
                err = reply.errorMessage()
                print(f"BT Manager: Pairing failed: {err}")
                return False, err
        except Exception as e:
            return False, str(e)

    def connect_device(self, device_path):
        """Connects to a device."""
        if self.emulation_mode:
            print(f"[BT Manager - Mock] Connecting to {device_path}...")
            # Update mock state
            for dev in self.mock_devices:
                if dev['path'] == device_path:
                    dev['connected'] = True
                    self.connected_device_path = dev['path']
                    self.connected_device_name = dev['name']
                    self.current_battery = 85 # Mock battery
                    self.connection_changed.emit(True, self.connected_device_name)
                    self.battery_updated.emit(self.current_battery)
                    # Also mock media player appearing
                    self.media_player_path = device_path + "/player0"
                    self.update_media_state({"Status": "playing", "Track": {"Title": "Mock Song", "Artist": "Mock Artist", "Album": "Mock Album", "Duration": 300000}, "Position": 1000})
                else:
                    dev['connected'] = False # Disconnect others
            return True, "Connected"

        try:
            device = QDBusInterface(BLUEZ_SERVICE, device_path, DEVICE_IFACE, self.bus)
            print(f"BT Manager: Connecting to {device_path}...")
            # Connect is often blocking, consider running in worker if UI freezes
            reply = device.call("Connect")
            
            if reply.type() != QDBusMessage.MessageType.ErrorMessage:
                print(f"BT Manager: Connected to {device_path}")
                return True, "Connected"
            else:
                err = reply.errorMessage()
                print(f"BT Manager: Connection failed: {err}")
                return False, err
        except Exception as e:
            return False, str(e)

    def disconnect_device(self, device_path):
        """Disconnects from a device."""
        if self.emulation_mode:
            print(f"[BT Manager - Mock] Disconnecting from {device_path}...")
            for dev in self.mock_devices:
                if dev['path'] == device_path:
                    dev['connected'] = False
            
            if self.connected_device_path == device_path:
                self._reset_connection_state()
            
            return True, "Disconnected"

        try:
            device = QDBusInterface(BLUEZ_SERVICE, device_path, DEVICE_IFACE, self.bus)
            print(f"BT Manager: Disconnecting from {device_path}...")
            reply = device.call("Disconnect")
            
            if reply.type() != QDBusMessage.MessageType.ErrorMessage:
                print(f"BT Manager: Disconnected from {device_path}")
                # Force reset state immediately if we were connected to this device
                if self.connected_device_path == device_path:
                    self._reset_connection_state()
                return True, "Disconnected"
            else:
                err = reply.errorMessage()
                print(f"BT Manager: Disconnection failed: {err}")
                return False, err
        except Exception as e:
            return False, str(e)
            
    def remove_device_dbus(self, device_path):
        """Removes a device using D-Bus Adapter.RemoveDevice."""
        if self.emulation_mode:
            print(f"[BT Manager - Mock] Removing device {device_path}...")
            self.mock_devices = [d for d in self.mock_devices if d['path'] != device_path]
            if self.connected_device_path == device_path:
                self.disconnect_device(device_path)
            return True, "Removed"

        if not self.adapter_path:
             return False, "No adapter"
             
        try:
            adapter = QDBusInterface(BLUEZ_SERVICE, self.adapter_path, ADAPTER_IFACE, self.bus)
            print(f"BT Manager: Removing device {device_path}...")
            reply = adapter.call("RemoveDevice", QDBusObjectPath(device_path))
            
            if reply.type() != QDBusMessage.MessageType.ErrorMessage:
                print(f"BT Manager: Device {device_path} removed.")
                return True, "Removed"
            else:
                err = reply.errorMessage()
                print(f"BT Manager: Removal failed: {err}")
                return False, err
        except Exception as e:
            return False, str(e)

    # --- run Method (Polling Implementation) ---
    def run(self):
        print("BluetoothManager thread started.")
        if self.emulation_mode:
            # Emulation Loop
            print("[BT Manager] Entering EMULATION polling loop")
            while self._is_running:
                # Simulate media position update if playing
                if self.playback_status == "playing":
                    current_pos = self.media_properties.get("Position", 0)
                    new_pos = current_pos + 1000 # +1 sec
                    self.media_properties["Position"] = new_pos
                    # Emit sometimes to update UI
                    # self.media_properties_changed.emit(self.media_properties) 
                    # (Actually UI updates on event, let's just sleep)
                
                self.msleep(1000)
            return

        if not self.bus.isConnected():  # ... error handling ...
            return
        self.adapter_path = self.find_adapter()
        if not self.adapter_path:  # ... error handling ...
            return
        print(f"DEBUG: BluetoothManager.run - Adapter found: {self.adapter_path}")

        # Get initial state
        om = QDBusInterface(BLUEZ_SERVICE, "/", DBUS_OM_IFACE, self.bus)
        managed_objects_reply = om.call("GetManagedObjects")
        if (
            managed_objects_reply.type() != QDBusMessage.MessageType.ErrorMessage
            and managed_objects_reply.arguments()
        ):
            objects_dict = qvariant_dict_to_python(managed_objects_reply.arguments()[0])
            print(
                f"DEBUG: BluetoothManager.run - Processing {len(objects_dict)} initial objects..."
            )
            for path, interfaces in objects_dict.items():
                if DEVICE_IFACE in interfaces:
                    dev_props = interfaces.get(DEVICE_IFACE, {})
                    self.process_device_properties(
                        path, dev_props
                    )  # Handles initial connect + battery check
            print("DEBUG: BluetoothManager.run - Initial object processing done.")
        # else: # Error logging

        # Connect ONLY working signals
        print(
            "DEBUG: BluetoothManager.run - Connecting D-Bus signals (Polling approach)..."
        )
        sig2_ok = self.bus.connect(
            BLUEZ_SERVICE,
            "/",
            DBUS_OM_IFACE,
            "InterfacesRemoved",
            self.on_interfaces_removed,
        )
        print(f"DEBUG: Signal connection status: InterfacesRemoved={sig2_ok}")

        print("BT Manager: Entering polling loop.")
        poll_interval_ms = 500  # Poll every 0.5 seconds for responsive media controls
        loop_count = 0
        om_iface = QDBusInterface(BLUEZ_SERVICE, "/", DBUS_OM_IFACE, self.bus)

        while self._is_running:
            # --- POLLING LOGIC ---
            try:
                # 1. Poll Connected Device Properties (BlueZ + UPower implicitly via process_device_properties)
                current_connected_path = self.connected_device_path
                if current_connected_path:
                    dev_props_iface = QDBusInterface(
                        BLUEZ_SERVICE, current_connected_path, DBUS_PROP_IFACE, self.bus
                    )
                    dev_reply = dev_props_iface.call("GetAll", DEVICE_IFACE)
                    if (
                        dev_reply.type() != QDBusMessage.MessageType.ErrorMessage
                        and dev_reply.arguments()
                    ):
                        dev_props_all = qvariant_dict_to_python(
                            dev_reply.arguments()[0]
                        )
                        self.process_device_properties(
                            current_connected_path, dev_props_all
                        )
                        if not self.connected_device_path:
                            continue  # Skip rest if disconnected by previous call
                    else:  # Failed to poll device, assume disconnect
                        print(
                            f"DEBUG: Failed to poll device {current_connected_path}, assuming disconnect."
                        )
                        self.process_device_properties(
                            current_connected_path, {"Connected": False}
                        )
                        continue

                # 2. Poll Media Player Properties
                current_media_path = self.media_player_path
                if current_media_path:
                    media_props_iface = QDBusInterface(
                        BLUEZ_SERVICE, current_media_path, DBUS_PROP_IFACE, self.bus
                    )
                    media_reply = media_props_iface.call("GetAll", MEDIA_PLAYER_IFACE)
                    if (
                        media_reply.type() != QDBusMessage.MessageType.ErrorMessage
                        and media_reply.arguments()
                    ):
                        media_props_all = qvariant_dict_to_python(
                            media_reply.arguments()[0]
                        )
                        self.update_media_state(media_props_all)
                    # else: print(f"DEBUG: Failed to poll media player {current_media_path}")

                # 3. Poll for NEW devices/players (less frequent?)
                if loop_count % 6 == 0:  # Check every ~3 seconds (6 * 0.5s)
                    om_reply = om_iface.call("GetManagedObjects")
                    if (
                        om_reply.type() != QDBusMessage.MessageType.ErrorMessage
                        and om_reply.arguments()
                    ):
                        obj_dict = qvariant_dict_to_python(om_reply.arguments()[0])
                        # Find newly connected device
                        if not self.connected_device_path:
                            for path, interfaces in obj_dict.items():
                                if DEVICE_IFACE in interfaces:
                                    dev_props = interfaces.get(DEVICE_IFACE, {})
                                    if dev_props.get("Connected", False):
                                        print(
                                            "DEBUG: New device connection detected via polling."
                                        )
                                        self.process_device_properties(path, dev_props)
                                        break
                        # Find newly appeared media player
                        elif not self.media_player_path and self.connected_device_path:
                            self.find_media_player(self.connected_device_path)

            except Exception as e:
                print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                print(f"ERROR in BluetoothManager polling loop: {e}")
                traceback.print_exc()
                print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

            loop_count += 1
            self.msleep(poll_interval_ms)

        # Disconnect signals on exit
        print("BT Manager: Disconnecting D-Bus signals.")
        if self.bus.isConnected():
            self.bus.disconnect(
                BLUEZ_SERVICE,
                "/",
                DBUS_OM_IFACE,
                "InterfacesRemoved",
                self.on_interfaces_removed,
            )
        print("BluetoothManager thread finished.")

    def stop(self):
        print("BluetoothManager: Stop requested.")
        self._is_running = False

    def poll_media_player_immediately(self):
        """Poll media player immediately for instant feedback after commands."""
        if not self.media_player_path:
            return

        try:
            media_props_iface = QDBusInterface(
                BLUEZ_SERVICE, self.media_player_path, DBUS_PROP_IFACE, self.bus
            )
            media_reply = media_props_iface.call("GetAll", MEDIA_PLAYER_IFACE)
            if (
                media_reply.type() != QDBusMessage.MessageType.ErrorMessage
                and media_reply.arguments()
            ):
                media_props_all = qvariant_dict_to_python(
                    media_reply.arguments()[0]
                )
                self.update_media_state(media_props_all)
                print("BT Manager: Immediate media poll completed")
        except Exception as e:
            print(f"Error in immediate media poll: {e}")

    # --- Media Control Methods ---
    def _send_media_command(self, command):
        """Sends a simple command (Play, Pause, Next, Previous) to the media player."""
        if not self.media_player_path:
            print("BT Manager: No active media player path to send command to.")
            return False
        if not self.bus.isConnected():
            print("BT Manager: D-Bus not connected.")
            return False
        print(f"BT Manager: Sending command '{command}' to {self.media_player_path}")
        try:
            player_iface = QDBusInterface(
                BLUEZ_SERVICE, self.media_player_path, MEDIA_PLAYER_IFACE, self.bus
            )
            reply_message = player_iface.call(command)
            if reply_message.type() == QDBusMessage.MessageType.ErrorMessage:
                print(
                    f"BT Manager: Error sending command '{command}': {reply_message.errorMessage()}"
                )
                return False
            else:
                print(f"BT Manager: Command '{command}' sent successfully.")
                # Force immediate poll for faster feedback
                self.poll_media_player_immediately()
                return True
        except Exception as e:
            print(f"ERROR sending command '{command}': {e}")
            traceback.print_exc()
            return False

    def send_play(self):
        return self._send_media_command("Play")

    def send_pause(self):
        return self._send_media_command("Pause")

    def send_next(self):
        return self._send_media_command("Next")

    def send_previous(self):
        return self._send_media_command("Previous")

    # --- Discoverability Methods ---
    # --- NUOVO BLOCCO PER LA GESTIONE DELLA VISIBILITÀ (SOSTITUISCI IL VECCHIO) ---

    # All'interno della classe BluetoothManager

    def set_discoverability(self, state: bool):
        """
        Attiva o disattiva la visibilità e l'associabilità dell'adattatore
        con un ciclo di riprova per la massima affidabilità.
        """
        if not self.adapter_path or not self.bus.isConnected():
            print("BT Manager: Adapter not found or bus not connected.")
            return False

        print(f"--- Impostazione visibilità a: {state} ---")
        try:
            adapter_iface = QDBusInterface(
                BLUEZ_SERVICE, self.adapter_path, ADAPTER_IFACE, self.bus
            )
            props_iface = QDBusInterface(
                BLUEZ_SERVICE, self.adapter_path, DBUS_PROP_IFACE, self.bus
            )

            # 1. Imposta le proprietà di base
            props_iface.call("Set", ADAPTER_IFACE, "Pairable", QDBusVariant(state))
            props_iface.call("Set", ADAPTER_IFACE, "Discoverable", QDBusVariant(state))

            if state:
                # 2. Avvia la discovery attiva con un CICLO DI RIPROVA
                max_retries = 5
                discovery_started = False
                for i in range(max_retries):
                    print(f"Tentativo {i + 1}/{max_retries} di avviare la discovery attiva...")
                    discovery_reply = adapter_iface.call("StartDiscovery")
                    
                    if discovery_reply.type() != QDBusMessage.MessageType.ErrorMessage:
                        print("Discovery attiva avviata con successo.")
                        discovery_started = True
                        break  # Esci dal ciclo se ha successo
                    
                    error_message = discovery_reply.errorMessage()
                    if "Resource Not Ready" in error_message:
                        print(f"Avviso: risorsa non pronta, nuovo tentativo tra 0.5s...")
                        time.sleep(0.5)  # Attendi mezzo secondo prima di riprovare
                    else:
                        # Se è un errore diverso, è inutile riprovare
                        print(f"Errore critico nell'avviare la discovery: {error_message}")
                        break # Esci dal ciclo
                
                if not discovery_started:
                    print("ERRORE: Impossibile avviare la discovery attiva dopo vari tentativi.")
                    # Non restituiamo False, perché la visibilità di base potrebbe funzionare

            else:
                # 3. Ferma la discovery quando si nasconde
                print("Interruzione della sessione di discovery...")
                adapter_iface.call("StopDiscovery")

            print(f"Procedura di impostazione visibilità a {state} completata.")
            return True

        except Exception as e:
            print(f"Eccezione durante l'impostazione della visibilità: {e}")
            return False

    def is_discoverable(self):
        """
        Controlla se l'adattatore è visibile.
        Questo ora legge direttamente la proprietà.
        """
        if not self.adapter_path or not self.bus.isConnected():
            return False
        try:
            props_iface = QDBusInterface(
                BLUEZ_SERVICE, self.adapter_path, DBUS_PROP_IFACE, self.bus
            )
            reply = props_iface.call("Get", ADAPTER_IFACE, "Discoverable")
            if reply.type() == QDBusMessage.MessageType.ErrorMessage:
                return False
            return qvariant_dict_to_python(reply.arguments()[0])
        except:
            return False

    def send_stop(self):
        return self._send_media_command("Stop")
