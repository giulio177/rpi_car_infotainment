# backend/bluetooth_manager.py

import time
import traceback
from PyQt6.QtCore import QThread, pyqtSignal, QVariant, QObject, pyqtSlot
from PyQt6.QtDBus import QDBusConnection, QDBusInterface, QDBusMessage

# Constants for BlueZ D-Bus
BLUEZ_SERVICE = 'org.bluez'
DBUS_OM_IFACE = 'org.freedesktop.DBus.ObjectManager'
DBUS_PROP_IFACE = 'org.freedesktop.DBus.Properties'

DEVICE_IFACE = 'org.bluez.Device1'
MEDIA_PLAYER_IFACE = 'org.bluez.MediaPlayer1'
MEDIA_CONTROL_IFACE = 'org.bluez.MediaControl1' # Might be needed for play/pause actions


# Helper to convert QVariant dictionary/value to Python types recursively
def qvariant_dict_to_python(variant_value):
    """
    Recursively converts a QVariant containing basic types, lists, or
    dictionaries (including nested ones) into standard Python types.
    """
    if not isinstance(variant_value, QVariant):
        # If it's not a QVariant, assume it's already a Python type
        # Handle potential dicts/lists directly if not wrapped
        if isinstance(variant_value, dict):
             # Recursively process nested dictionaries
            py_dict = {}
            for k, v in variant_value.items():
                py_dict[k] = qvariant_dict_to_python(v) # Recurse on values
            return py_dict
        elif isinstance(variant_value, list):
             # Recursively process nested lists
             return [qvariant_dict_to_python(item) for item in variant_value]
        else:
            return variant_value # Return as is (e.g., str, int, bool, None)

    # If it IS a QVariant, unwrap it first
    value = variant_value.value()

    if isinstance(value, dict):
        # If the unwrapped value is a dictionary, recursively process its values
        py_dict = {}
        for k, v in value.items():
            py_dict[k] = qvariant_dict_to_python(v) # Recurse on values
        return py_dict
    elif isinstance(value, list):
        # If the unwrapped value is a list, recursively process its items
        return [qvariant_dict_to_python(item) for item in value]
    else:
        # Otherwise, return the unwrapped primitive value
        return value


class BluetoothManager(QThread):
    # Signals
    connection_changed = pyqtSignal(bool, str)
    battery_updated = pyqtSignal(object)
    media_properties_changed = pyqtSignal(dict)
    playback_status_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        print("DEBUG: BluetoothManager.__init__")
        self._is_running = True
        self.bus = QDBusConnection.systemBus()

        # State variables
        self.adapter_path = None
        self.connected_device_path = None
        self.connected_device_name = "Disconnected"
        self.current_battery = None
        self.media_player_path = None
        self.media_properties = {}
        self.playback_status = "stopped"
        self.dbus_receiver = QObject() # Potentially needed if sender context is required

    def find_adapter(self):
        print("DEBUG: BluetoothManager.find_adapter - Entered")
        """Finds the first available Bluetooth adapter."""
        om = QDBusInterface(BLUEZ_SERVICE, '/', DBUS_OM_IFACE, self.bus)
        print("DEBUG: BluetoothManager.find_adapter - Calling GetManagedObjects...")
        reply_message = om.call('GetManagedObjects')
        print(f"DEBUG: BluetoothManager.find_adapter - GetManagedObjects returned type: {reply_message.type()}")
        if reply_message.type() == QDBusMessage.MessageType.ErrorMessage:
            print("BT Manager: Error getting managed objects:", reply_message.errorMessage())
            return None
        if not reply_message.arguments():
             print("BT Manager: GetManagedObjects reply has no arguments.")
             return None

        # Arguments should contain the dictionary a{oa{sa{sv}}}
        objects_dict_variant = reply_message.arguments()[0]
        objects_dict = qvariant_dict_to_python(objects_dict_variant) # Convert top-level dict

        print(f"DEBUG: BluetoothManager.find_adapter - Processing {len(objects_dict)} managed objects...")
        for path, interfaces in objects_dict.items():
            # Interfaces is now Dict[str, Dict[str, Any]]
            if 'org.bluez.Adapter1' in interfaces:
                print(f"BT Manager: Found adapter at {path}")
                return path
        print("BT Manager: No Bluetooth adapter found.")
        return None

    def process_device_properties(self, path, properties):
        # print(f"DEBUG: BluetoothManager.process_device_properties - Path: {path}, Props: {properties}")
        """Checks device properties for connection and battery. Assumes 'properties' is a Python dict."""
        is_connected = properties.get('Connected', False)
        device_name = properties.get('Name', "Unknown Device")
        alias = properties.get('Alias', device_name)
        battery = properties.get('Battery', None)

        if is_connected:
            if self.connected_device_path != path:
                print(f"BT Manager: Device connected - {alias} ({path})")
                self.connected_device_path = path
                self.connected_device_name = alias
                self.current_battery = battery
                print(f"DEBUG: Emitting connection_changed(True, {self.connected_device_name})")
                self.connection_changed.emit(True, self.connected_device_name)
                print(f"DEBUG: Emitting battery_updated({self.current_battery})")
                self.battery_updated.emit(self.current_battery)
                self.find_media_player(path)
            elif battery != self.current_battery:
                 print(f"BT Manager: Battery updated for {alias} to {battery}")
                 self.current_battery = battery
                 print(f"DEBUG: Emitting battery_updated({self.current_battery})")
                 self.battery_updated.emit(self.current_battery)

        elif self.connected_device_path == path:
             print(f"BT Manager: Device disconnected - {alias} ({path})")
             if self.media_player_path and self.media_player_path.startswith(path):
                  # Also disconnect media player listener if device disconnects
                  print(f"DEBUG: Disconnecting media properties signal for {self.media_player_path} due to device disconnect")
                  self.bus.disconnect(BLUEZ_SERVICE, self.media_player_path, DBUS_PROP_IFACE, 'PropertiesChanged', self.on_media_properties_changed)
                  self.media_player_path = None # Clear media player path

             self.connected_device_path = None
             self.connected_device_name = "Disconnected"
             self.current_battery = None
             self.media_properties = {}
             self.playback_status = "stopped"
             print(f"DEBUG: Emitting connection_changed(False, ...)")
             self.connection_changed.emit(False, "Disconnected") # Send generic name on disconnect
             print(f"DEBUG: Emitting battery_updated(None)")
             self.battery_updated.emit(None)
             print(f"DEBUG: Emitting media_properties_changed({{}})")
             self.media_properties_changed.emit({})
             print(f"DEBUG: Emitting playback_status_changed('stopped')")
             self.playback_status_changed.emit("stopped")

    def find_media_player(self, device_path_hint=None):
        print(f"DEBUG: BluetoothManager.find_media_player - Hint: {device_path_hint}")
        """Finds the active media player, optionally prioritizing one on a specific device."""
        om = QDBusInterface(BLUEZ_SERVICE, '/', DBUS_OM_IFACE, self.bus)
        print("DEBUG: BluetoothManager.find_media_player - Calling GetManagedObjects...")
        reply_message = om.call('GetManagedObjects')
        print(f"DEBUG: BluetoothManager.find_media_player - GetManagedObjects returned type: {reply_message.type()}")
        if reply_message.type() == QDBusMessage.MessageType.ErrorMessage:
            print("BT Manager: Error getting managed objects for media player:", reply_message.errorMessage())
            return False
        if not reply_message.arguments():
             print("BT Manager: GetManagedObjects (media player search) reply has no arguments.")
             return False

        objects_dict_variant = reply_message.arguments()[0]
        objects_dict = qvariant_dict_to_python(objects_dict_variant)
        found_player_path = None
        print(f"DEBUG: BluetoothManager.find_media_player - Processing {len(objects_dict)} objects for media player...")

        for path, interfaces in objects_dict.items():
            # interfaces is Dict[str, Dict[str, Any]]
            if MEDIA_PLAYER_IFACE in interfaces:
                 player_props = interfaces.get(MEDIA_PLAYER_IFACE, {}) # Already Python dict from helper
                 player_device = player_props.get('Device', "")

                 if device_path_hint and player_device == device_path_hint:
                     found_player_path = path
                     print(f"BT Manager: Found media player for connected device at {path}")
                     break
                 elif not device_path_hint and not found_player_path:
                      # Only consider players associated with *some* device path
                      if player_device and player_device.startswith("/org/bluez/hci"):
                           found_player_path = path
                           print(f"BT Manager: Found media player (generic, attached to a device) at {path}")
                      # else: print(f"DEBUG: Skipping player {path} with no device property")


        if found_player_path and found_player_path != self.media_player_path:
            print(f"BT Manager: Media player activated at {found_player_path}")
            # Disconnect old listener before connecting new one
            if self.media_player_path:
                 print(f"DEBUG: Disconnecting OLD media properties signal for {self.media_player_path}")
                 self.bus.disconnect(BLUEZ_SERVICE, self.media_player_path, DBUS_PROP_IFACE, 'PropertiesChanged', self.on_media_properties_changed)
            self.media_player_path = found_player_path
            self.monitor_media_player(found_player_path)
            return True
        elif not found_player_path and self.media_player_path:
             print("BT Manager: Active media player seems to be gone.")
             if self.media_player_path:
                 print(f"DEBUG: Disconnecting media properties signal for {self.media_player_path}")
                 self.bus.disconnect(BLUEZ_SERVICE, self.media_player_path, DBUS_PROP_IFACE, 'PropertiesChanged', self.on_media_properties_changed)
             self.media_player_path = None
             self.media_properties = {}
             self.playback_status = "stopped"
             print(f"DEBUG: Emitting media_properties_changed({{}})")
             self.media_properties_changed.emit({})
             print(f"DEBUG: Emitting playback_status_changed('stopped')")
             self.playback_status_changed.emit("stopped")
             return False
        print(f"DEBUG: BluetoothManager.find_media_player - Result: Found={found_player_path is not None}, CurrentPlayerPath={self.media_player_path}")
        return found_player_path is not None


    def monitor_media_player(self, player_path):
        print(f"DEBUG: BluetoothManager.monitor_media_player - Path: {player_path}")
        """Connects signals for a specific media player."""
        if not player_path: return

        # Monitor PropertiesChanged for the NEW media player
        print(f"DEBUG: Connecting media properties signal for {player_path} (using @pyqtSlot)")
        connection_success = self.bus.connect(
            BLUEZ_SERVICE, player_path, DBUS_PROP_IFACE, 'PropertiesChanged',
            self.on_media_properties_changed # Target method MUST be decorated
        )
        print(f"DEBUG: Connection status for media properties: {connection_success}")

        # Get initial properties using the CORRECT interface
        print("DEBUG: BluetoothManager.monitor_media_player - Getting initial props...")
        props_iface = QDBusInterface(BLUEZ_SERVICE, player_path, DBUS_PROP_IFACE, self.bus)
        reply_message = props_iface.call("GetAll", MEDIA_PLAYER_IFACE) # Pass MediaPlayer1 IFACE as argument
        print(f"DEBUG: BluetoothManager.monitor_media_player - GetAll returned type: {reply_message.type()}")
        if reply_message.type() == QDBusMessage.MessageType.ErrorMessage:
            print(f"BT Manager: Failed to get initial media props from {player_path}: {reply_message.errorMessage()}")
        elif reply_message.arguments():
             # GetAll returns a{sv} which is Dict[str, QVariant]
             initial_props_variant = reply_message.arguments()[0]
             initial_props = qvariant_dict_to_python(initial_props_variant) # Convert here
             print(f"DEBUG: Initial media props: {initial_props}")
             self.update_media_state(initial_props) # Pass the Python dict
        else:
             print(f"BT Manager: Got reply for GetAll media props, but no arguments found for {player_path}.")


    # --- Slots with RESTORED @pyqtSlot decorators and QVariant hints ---

    @pyqtSlot(str, QVariant, "QStringList") # Use QVariant for a{sv} (changed_properties)
    def on_media_properties_changed(self, interface_name, changed_properties_variant, invalidated_properties):
        """Handles D-Bus PropertiesChanged signal for MediaPlayer1."""
        try:
            changed_properties = qvariant_dict_to_python(changed_properties_variant) # Use helper
            print(f"DEBUG: on_media_properties_changed triggered: Iface={interface_name}, Changed={changed_properties}")
            if interface_name == MEDIA_PLAYER_IFACE and isinstance(changed_properties, dict):
                self.update_media_state(changed_properties) # Pass Python dict
            # else: print(f"DEBUG: Ignoring media properties changed for {interface_name}")
        except Exception as e:
            print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print(f"ERROR in on_media_properties_changed: {e}")
            traceback.print_exc()
            print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")


    def update_media_state(self, properties):
        # print(f"DEBUG: BluetoothManager.update_media_state - Python props: {properties}")
        """Updates internal state and emits signals based on media properties. Assumes 'properties' is Python dict."""
        new_track_info = None
        new_status = None
        track_changed = False

        if 'Track' in properties:
            # The 'Track' value itself might be a dict from qvariant_dict_to_python
            track_info = properties.get('Track', {})
            if isinstance(track_info, dict) and track_info != self.media_properties.get('Track', {}):
                new_track_info = track_info
                track_changed = True
                print(f"BT Manager: Track Info Updated: {new_track_info}")
                self.media_properties['Track'] = new_track_info
            elif not isinstance(track_info, dict):
                 print(f"DEBUG: Unexpected type for Track property: {type(track_info)}")


        if 'Status' in properties:
            status = properties.get('Status', 'stopped')
            if status != self.playback_status:
                new_status = status
                print(f"BT Manager: Playback Status Updated: {new_status}")
                self.playback_status = new_status
                print(f"DEBUG: Emitting playback_status_changed({new_status})")
                self.playback_status_changed.emit(new_status)

        if 'Position' in properties:
             position = properties.get('Position', 0)
             self.media_properties['Position'] = position

        if track_changed:
             print(f"DEBUG: Emitting media_properties_changed({self.media_properties})")
             self.media_properties_changed.emit(self.media_properties)


    @pyqtSlot(str, QVariant) # Use QVariant for a{sa{sv}} (interfaces_and_properties)
    def on_interfaces_added(self, path, interfaces_and_properties_variant):
        """Handles D-Bus InterfacesAdded signal."""
        try:
            interfaces_and_properties = qvariant_dict_to_python(interfaces_and_properties_variant) # Use helper
            print(f"DEBUG: on_interfaces_added triggered for path: {path}")
            if isinstance(interfaces_and_properties, dict):
                if DEVICE_IFACE in interfaces_and_properties:
                    print(f"BT Manager: Interface added for Device: {path}")
                    props = interfaces_and_properties.get(DEVICE_IFACE, {}) # Already Python dict
                    self.process_device_properties(path, props)
                elif MEDIA_PLAYER_IFACE in interfaces_and_properties:
                     print(f"BT Manager: Interface added for Media Player: {path}")
                     self.find_media_player()
            else:
                 print(f"DEBUG: on_interfaces_added - Expected dict for interfaces_and_properties, got {type(interfaces_and_properties)}")
        except Exception as e:
            print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print(f"ERROR in on_interfaces_added for path {path}: {e}")
            traceback.print_exc()
            print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")


    @pyqtSlot(str, "QStringList") # Keep this as it worked
    def on_interfaces_removed(self, path, interfaces):
        """Handles D-Bus InterfacesRemoved signal."""
        try:
            print(f"DEBUG: on_interfaces_removed triggered for path: {path}, Interfaces: {interfaces}")
            if DEVICE_IFACE in interfaces:
                 print(f"BT Manager: Interface removed for Device: {path}")
                 if path == self.connected_device_path:
                     # Pass python bool directly
                     self.process_device_properties(path, {'Connected': False})
            elif MEDIA_PLAYER_IFACE in interfaces:
                 print(f"BT Manager: Interface removed for Media Player: {path}")
                 if path == self.media_player_path:
                     self.find_media_player() # Re-evaluate
        except Exception as e:
            print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print(f"ERROR in on_interfaces_removed for path {path}: {e}")
            traceback.print_exc()
            print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")


    @pyqtSlot(str, QVariant, "QStringList") # Use QVariant for a{sv} (changed_properties)
    def on_device_properties_changed(self, interface_name, changed_properties_variant, invalidated_properties):
        """Handles D-Bus PropertiesChanged signal (generic connection)."""
        try:
            changed_properties = qvariant_dict_to_python(changed_properties_variant) # Use helper
            print(f"DEBUG: on_device_properties_changed triggered: Iface={interface_name}, Changed={changed_properties}")

            # Logic to re-fetch properties for connected device remains the same
            if interface_name == DEVICE_IFACE and self.connected_device_path and isinstance(changed_properties, dict):
                 print(f"DEBUG: Device property change detected. Refetching props for {self.connected_device_path}.")
                 props_iface = QDBusInterface(BLUEZ_SERVICE, self.connected_device_path, DBUS_PROP_IFACE, self.bus)
                 reply_message = props_iface.call("GetAll", DEVICE_IFACE)
                 if reply_message.type() != QDBusMessage.MessageType.ErrorMessage and reply_message.arguments():
                     all_props_variant = reply_message.arguments()[0]
                     all_props = qvariant_dict_to_python(all_props_variant) # Convert here
                     self.process_device_properties(self.connected_device_path, all_props) # Pass Python dict
                 else:
                      print(f"BT Manager: Failed to GetAll props for {self.connected_device_path} on change: {reply_message.errorMessage() if reply_message.type() == QDBusMessage.MessageType.ErrorMessage else 'No arguments'}")
            # else: print("DEBUG: Ignoring device properties changed (no connected device or wrong interface/type)")

        except Exception as e:
            print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print(f"ERROR in on_device_properties_changed: {e}")
            traceback.print_exc()
            print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")


    def run(self):
        print("BluetoothManager thread started.")
        if not self.bus.isConnected():
            print("BT Manager: Failed to connect to D-Bus system bus.")
            self._is_running = False
            return

        self.adapter_path = self.find_adapter()
        if not self.adapter_path:
            print("BT Manager: Could not find Bluetooth adapter. Exiting thread.")
            self._is_running = False
            return
        print(f"DEBUG: BluetoothManager.run - Adapter found: {self.adapter_path}")

        # Get initial state
        om = QDBusInterface(BLUEZ_SERVICE, '/', DBUS_OM_IFACE, self.bus)
        print("DEBUG: BluetoothManager.run - Calling initial GetManagedObjects...")
        managed_objects_reply = om.call('GetManagedObjects')
        print(f"DEBUG: BluetoothManager.run - Initial GetManagedObjects type: {managed_objects_reply.type()}")
        if managed_objects_reply.type() != QDBusMessage.MessageType.ErrorMessage and managed_objects_reply.arguments():
             objects_dict_variant = managed_objects_reply.arguments()[0]
             objects_dict = qvariant_dict_to_python(objects_dict_variant) # Convert here
             print(f"DEBUG: BluetoothManager.run - Processing {len(objects_dict)} initial objects...")
             for path, interfaces in objects_dict.items():
                 # interfaces is Dict[str, Dict[str, Any]] after conversion
                 if DEVICE_IFACE in interfaces:
                      dev_props = interfaces.get(DEVICE_IFACE, {}) # Already Python dict
                      self.process_device_properties(path, dev_props)
             print("DEBUG: BluetoothManager.run - Initial object processing done.")
             self.find_media_player(self.connected_device_path)
             print("DEBUG: BluetoothManager.run - Initial media player check done.")
        else:
             print(f"BT Manager: Failed to get initial managed objects: {managed_objects_reply.errorMessage() if managed_objects_reply.type() == QDBusMessage.MessageType.ErrorMessage else 'No arguments'}")


        # Connect signals using the RESTORED decorators and refined signatures
        print("DEBUG: BluetoothManager.run - Connecting D-Bus signals (using @pyqtSlot)...")
        sig1_ok = self.bus.connect(BLUEZ_SERVICE, '/', DBUS_OM_IFACE, 'InterfacesAdded', self.on_interfaces_added)
        sig2_ok = self.bus.connect(BLUEZ_SERVICE, '/', DBUS_OM_IFACE, 'InterfacesRemoved', self.on_interfaces_removed) # Keep working one
        sig3_ok = self.bus.connect(BLUEZ_SERVICE, '', DBUS_PROP_IFACE, 'PropertiesChanged', self.on_device_properties_changed) # Generic properties

        print(f"DEBUG: Signal connection status: InterfacesAdded={sig1_ok}, InterfacesRemoved={sig2_ok}, PropertiesChanged(Device)={sig3_ok}")
        if not sig1_ok or not sig3_ok:
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print("CRITICAL ERROR: Failed to connect essential D-Bus signals (InterfacesAdded or PropertiesChanged). Bluetooth monitoring will not work correctly.")
            print("Check slot signatures (@pyqtSlot) and D-Bus permissions.")
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

        print("BT Manager: Entering wait loop.")
        loop_count = 0
        while self._is_running:
            # if loop_count % 30 == 0: print(f"DEBUG: BluetoothManager running... Loop {loop_count}")
            loop_count += 1
            self.msleep(1000) # Sleep for 1 second

        # Disconnect signals on exit
        print("BT Manager: Disconnecting D-Bus signals.")
        self.bus.disconnect(BLUEZ_SERVICE, '/', DBUS_OM_IFACE, 'InterfacesAdded', self.on_interfaces_added)
        self.bus.disconnect(BLUEZ_SERVICE, '/', DBUS_OM_IFACE, 'InterfacesRemoved', self.on_interfaces_removed)
        self.bus.disconnect(BLUEZ_SERVICE, '', DBUS_PROP_IFACE, 'PropertiesChanged', self.on_device_properties_changed)
        if self.media_player_path:
             print(f"DEBUG: Disconnecting media properties signal for {self.media_player_path} on exit")
             self.bus.disconnect(BLUEZ_SERVICE, self.media_player_path, DBUS_PROP_IFACE, 'PropertiesChanged', self.on_media_properties_changed)

        print("BluetoothManager thread finished.")


    def stop(self):
        print("BluetoothManager: Stop requested.")
        self._is_running = False
