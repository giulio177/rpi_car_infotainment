# backend/bluetooth_manager.py

import time
import traceback # Import traceback for detailed exception printing
from PyQt6.QtCore import QThread, pyqtSignal, QVariant, QObject, pyqtSlot
# Make sure QDBusMessage is imported if you are using it in signatures, otherwise remove
from PyQt6.QtDBus import QDBusConnection, QDBusInterface, QDBusMessage

# Constants for BlueZ D-Bus
BLUEZ_SERVICE = 'org.bluez'
DBUS_OM_IFACE = 'org.freedesktop.DBus.ObjectManager'
DBUS_PROP_IFACE = 'org.freedesktop.DBus.Properties'
DEVICE_IFACE = 'org.bluez.Device1'
MEDIA_PLAYER_IFACE = 'org.bluez.MediaPlayer1'
MEDIA_CONTROL_IFACE = 'org.bluez.MediaControl1'


# Helper to convert QVariant dictionary to Python dict
def qvariant_dict_to_python(qvariant_dict):
    py_dict = {}
    actual_dict = qvariant_dict.value() if isinstance(qvariant_dict, QVariant) else qvariant_dict
    if isinstance(actual_dict, dict):
        for key, value in actual_dict.items():
            if isinstance(value, QVariant):
                # Recursively handle nested dicts that might be variants
                if value.typeName() == 'a{sv}' or isinstance(value.value(), dict):
                     py_dict[key] = qvariant_dict_to_python(value) # Recursive call
                else:
                     py_dict[key] = value.value()
            else:
                py_dict[key] = value
    return py_dict


class BluetoothManager(QThread):
    # Signals
    connection_changed = pyqtSignal(bool, str)
    battery_updated = pyqtSignal(object)
    media_properties_changed = pyqtSignal(dict)
    playback_status_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        print("DEBUG: BluetoothManager.__init__") # DEBUG
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
        self.dbus_receiver = QObject() # Receiver object for generic signal connections

    def find_adapter(self):
        print("DEBUG: BluetoothManager.find_adapter - Entered") # DEBUG
        """Finds the first available Bluetooth adapter."""
        om = QDBusInterface(BLUEZ_SERVICE, '/', DBUS_OM_IFACE, self.bus)
        print("DEBUG: BluetoothManager.find_adapter - Calling GetManagedObjects...") # DEBUG
        reply_message = om.call('GetManagedObjects')
        print(f"DEBUG: BluetoothManager.find_adapter - GetManagedObjects returned type: {reply_message.type()}") # DEBUG
        if reply_message.type() == QDBusMessage.MessageType.ErrorMessage:
            print("BT Manager: Error getting managed objects:", reply_message.errorMessage())
            return None
        if not reply_message.arguments():
             print("BT Manager: GetManagedObjects reply has no arguments.")
             return None

        objects_dict = reply_message.arguments()[0]
        print(f"DEBUG: BluetoothManager.find_adapter - Processing {len(objects_dict)} managed objects...") # DEBUG
        for path, interfaces in objects_dict.items():
            if 'org.bluez.Adapter1' in interfaces:
                print(f"BT Manager: Found adapter at {path}")
                return path
        print("BT Manager: No Bluetooth adapter found.")
        return None

    def process_device_properties(self, path, properties):
        # print(f"DEBUG: BluetoothManager.process_device_properties - Path: {path}, Props: {properties}") # DEBUG - Can be noisy
        """Checks device properties for connection and battery."""
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
                print(f"DEBUG: Emitting connection_changed(True, {self.connected_device_name})") # DEBUG
                self.connection_changed.emit(True, self.connected_device_name)
                print(f"DEBUG: Emitting battery_updated({self.current_battery})") # DEBUG
                self.battery_updated.emit(self.current_battery)
                self.find_media_player(path)
            elif battery != self.current_battery:
                 print(f"BT Manager: Battery updated for {alias} to {battery}")
                 self.current_battery = battery
                 print(f"DEBUG: Emitting battery_updated({self.current_battery})") # DEBUG
                 self.battery_updated.emit(self.current_battery)

        elif self.connected_device_path == path:
             print(f"BT Manager: Device disconnected - {alias} ({path})")
             # ... (clear state) ...
             self.connected_device_path = None
             self.connected_device_name = "Disconnected"
             self.current_battery = None
             self.media_player_path = None
             self.media_properties = {}
             self.playback_status = "stopped"
             print(f"DEBUG: Emitting connection_changed(False, ...)") # DEBUG
             self.connection_changed.emit(False, self.connected_device_name)
             print(f"DEBUG: Emitting battery_updated(None)") # DEBUG
             self.battery_updated.emit(None)
             print(f"DEBUG: Emitting media_properties_changed({{}})") # DEBUG
             self.media_properties_changed.emit({})
             print(f"DEBUG: Emitting playback_status_changed('stopped')") # DEBUG
             self.playback_status_changed.emit("stopped")

    def find_media_player(self, device_path_hint=None):
        print(f"DEBUG: BluetoothManager.find_media_player - Hint: {device_path_hint}") # DEBUG
        """Finds the active media player, optionally prioritizing one on a specific device."""
        om = QDBusInterface(BLUEZ_SERVICE, '/', DBUS_OM_IFACE, self.bus)
        print("DEBUG: BluetoothManager.find_media_player - Calling GetManagedObjects...") # DEBUG
        reply_message = om.call('GetManagedObjects')
        print(f"DEBUG: BluetoothManager.find_media_player - GetManagedObjects returned type: {reply_message.type()}") # DEBUG
        if reply_message.type() == QDBusMessage.MessageType.ErrorMessage:
            print("BT Manager: Error getting managed objects for media player:", reply_message.errorMessage())
            return False
        if not reply_message.arguments():
             print("BT Manager: GetManagedObjects (media player search) reply has no arguments.")
             return False

        objects_dict = reply_message.arguments()[0]
        found_player_path = None
        print(f"DEBUG: BluetoothManager.find_media_player - Processing {len(objects_dict)} objects for media player...") # DEBUG

        for path, interfaces in objects_dict.items():
            if MEDIA_PLAYER_IFACE in interfaces:
                 player_props_variant = interfaces.get(MEDIA_PLAYER_IFACE, {})
                 player_props = qvariant_dict_to_python(player_props_variant)
                 player_device = player_props.get('Device', "")

                 if device_path_hint and player_device == device_path_hint:
                     found_player_path = path
                     print(f"BT Manager: Found media player for connected device at {path}")
                     break
                 elif not device_path_hint and not found_player_path:
                      found_player_path = path
                      print(f"BT Manager: Found media player (generic) at {path}")

        if found_player_path and found_player_path != self.media_player_path:
            print(f"BT Manager: Media player activated at {found_player_path}")
            self.media_player_path = found_player_path
            self.monitor_media_player(found_player_path)
            return True
        elif not found_player_path and self.media_player_path:
             print("BT Manager: Active media player seems to be gone.")
             if self.media_player_path: # Disconnect previous signal if path existed
                 print(f"DEBUG: Disconnecting media properties signal for {self.media_player_path}")
                 self.bus.disconnect(BLUEZ_SERVICE, self.media_player_path, DBUS_PROP_IFACE, 'PropertiesChanged', self.on_media_properties_changed)
             self.media_player_path = None
             self.media_properties = {}
             self.playback_status = "stopped"
             print(f"DEBUG: Emitting media_properties_changed({{}})") # DEBUG
             self.media_properties_changed.emit({})
             print(f"DEBUG: Emitting playback_status_changed('stopped')") # DEBUG
             self.playback_status_changed.emit("stopped")
             return False
        print(f"DEBUG: BluetoothManager.find_media_player - Result: Found={found_player_path is not None}") # DEBUG
        return found_player_path is not None


    def monitor_media_player(self, player_path):
        print(f"DEBUG: BluetoothManager.monitor_media_player - Path: {player_path}") # DEBUG
        """Connects signals for a specific media player."""
        if not player_path: return

        # Disconnect previous listener if different player
        if self.media_player_path and self.media_player_path != player_path:
             print(f"DEBUG: Disconnecting OLD media properties signal for {self.media_player_path}")
             self.bus.disconnect(BLUEZ_SERVICE, self.media_player_path, DBUS_PROP_IFACE, 'PropertiesChanged', self.on_media_properties_changed)

        # Monitor PropertiesChanged for the NEW media player
        print(f"DEBUG: Connecting media properties signal for {player_path}") # DEBUG
        connection_success = self.bus.connect(
            BLUEZ_SERVICE, player_path, DBUS_PROP_IFACE, 'PropertiesChanged',
            self.on_media_properties_changed
        )
        print(f"DEBUG: Connection status for media properties: {connection_success}") # DEBUG

        # Get initial properties
        media_player_iface = QDBusInterface(BLUEZ_SERVICE, player_path, MEDIA_PLAYER_IFACE, self.bus)
        print("DEBUG: BluetoothManager.monitor_media_player - Calling GetAll...") # DEBUG
        reply_message = media_player_iface.call("GetAll", MEDIA_PLAYER_IFACE)
        print(f"DEBUG: BluetoothManager.monitor_media_player - GetAll returned type: {reply_message.type()}") # DEBUG
        if reply_message.type() == QDBusMessage.MessageType.ErrorMessage:
            print(f"BT Manager: Failed to get initial media props from {player_path}: {reply_message.errorMessage()}")
        elif reply_message.arguments():
             initial_props = reply_message.arguments()[0]
             print(f"DEBUG: Initial media props: {initial_props}") # DEBUG
             self.update_media_state(initial_props)
        else:
             print(f"BT Manager: Got reply for GetAll media props, but no arguments found for {player_path}.")


    # --- Wrap slots in try/except ---
    @pyqtSlot(str, dict, "QStringList") # Using dict based on previous fixes
    def on_media_properties_changed(self, interface_name, changed_properties, invalidated_properties):
        """Handles D-Bus PropertiesChanged signal for MediaPlayer1."""
        try:
            changed_properties = changed_properties_variant.value() if isinstance(changed_properties_variant, QVariant) else changed_properties_variant
            print(f"DEBUG: on_media_properties_changed triggered: Iface={interface_name}, Changed={changed_properties}") # DEBUG
            if interface_name == MEDIA_PLAYER_IFACE:
                print("BT Manager: Media properties changed (in slot):", changed_properties)
                self.update_media_state(changed_properties)
        except Exception as e:
            print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print(f"ERROR in on_media_properties_changed: {e}")
            traceback.print_exc()
            print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")


    def update_media_state(self, properties_variant_map):
        # print(f"DEBUG: BluetoothManager.update_media_state - Props map: {properties_variant_map}") # DEBUG - Can be noisy
        """Updates internal state and emits signals based on media properties."""
        properties = qvariant_dict_to_python(properties_variant_map)
        # print(f"DEBUG: BluetoothManager.update_media_state - Python props: {properties}") # DEBUG

        new_track_info = None
        new_status = None
        track_changed = False

        if 'Track' in properties:
            track_info = qvariant_dict_to_python(properties.get('Track', {}))
            if track_info != self.media_properties.get('Track', {}):
                new_track_info = track_info
                track_changed = True # Flag that track details changed
                print(f"BT Manager: Track Info Updated: {new_track_info}")
                self.media_properties['Track'] = new_track_info
                # Defer emitting until other props checked

        if 'Status' in properties:
            status = properties.get('Status', 'stopped')
            if status != self.playback_status:
                new_status = status
                print(f"BT Manager: Playback Status Updated: {new_status}")
                self.playback_status = new_status
                print(f"DEBUG: Emitting playback_status_changed({new_status})") # DEBUG
                self.playback_status_changed.emit(new_status)

        if 'Position' in properties:
             position = properties.get('Position', 0)
             self.media_properties['Position'] = position # Just store it

        # Emit media_properties_changed only if track info actually changed
        if track_changed:
             print(f"DEBUG: Emitting media_properties_changed({self.media_properties})") # DEBUG
             self.media_properties_changed.emit(self.media_properties)


    # --- Wrap slots in try/except ---
    # Use signature based on actual D-Bus signal arguments for InterfacesAdded
    @pyqtSlot(str, dict) # path (str), interfaces_and_properties (dict mapping str -> dict)
    def on_interfaces_added(self, path, interfaces_and_properties):
        try:
            interfaces_and_properties = interfaces_and_properties_variant.value() if isinstance(interfaces_and_properties_variant, QVariant) else interfaces_and_properties_variant
            print(f"DEBUG: on_interfaces_added triggered for path: {path}") # DEBUG
            # interfaces_and_properties is Dict[str, Dict[str, QVariant]]
            if isinstance(interfaces_and_properties, dict): # Check it's actually a dict after unwrapping
                if DEVICE_IFACE in interfaces_and_properties:
                    print(f"BT Manager: Interface added for Device: {path}")
                    props_variant = interfaces_and_properties.get(DEVICE_IFACE, {})
                    props = qvariant_dict_to_python(props_variant) # Unwraps inner QVariants
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

    # --- Wrap slots in try/except ---
    # Use signature based on actual D-Bus signal arguments for InterfacesRemoved
    @pyqtSlot(str, "QStringList") # path (str), interfaces (list of str)
    def on_interfaces_removed(self, path, interfaces):
        try:
            print(f"DEBUG: on_interfaces_removed triggered for path: {path}, Interfaces: {interfaces}") # DEBUG
            if DEVICE_IFACE in interfaces:
                 print(f"BT Manager: Interface removed for Device: {path}")
                 if path == self.connected_device_path:
                     self.process_device_properties(path, {'Connected': False}) # Trigger disconnect
            elif MEDIA_PLAYER_IFACE in interfaces:
                 print(f"BT Manager: Interface removed for Media Player: {path}")
                 if path == self.media_player_path:
                     self.find_media_player() # Re-evaluate (likely gone)
        except Exception as e:
            print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print(f"ERROR in on_interfaces_removed for path {path}: {e}")
            traceback.print_exc()
            print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")


    # --- Wrap slots in try/except ---
    @pyqtSlot(str, dict, "QStringList") # Using dict based on previous fixes
    def on_device_properties_changed(self, interface_name, changed_properties, invalidated_properties):
        try:
            # --- Get sender path (IMPORTANT) ---
            # D-Bus signals connected without a specific path don't inherently know the object path.
            # We often have to rely on context or potentially message properties if available.
            # A common workaround if the sender() context isn't reliable is to iterate through known devices.
            # Let's assume for now changed_properties might give clues, or we refetch all if ambiguous.
            # This part is tricky without sender context.

            changed_properties = changed_properties_variant.value() if isinstance(changed_properties_variant, QVariant) else changed_properties_variant
            # TEMPORARY: Just log, this might not be reliable for path identification
            print(f"DEBUG: on_device_properties_changed triggered: Iface={interface_name}, Changed={changed_properties}")

            # If we know the connected device path, only process changes for that one
            if interface_name == DEVICE_IFACE and self.connected_device_path and isinstance(changed_properties, dict):
                # Check if the change affects our connected device - this requires getting sender path if possible
                # Or, simply re-fetch if ANY device property changes (less efficient)
                # Let's just re-fetch for the connected device for now if the signal arrives
                print(f"DEBUG: Device property change detected. Refetching all props for connected device {self.connected_device_path}.")
                device_iface = QDBusInterface(BLUEZ_SERVICE, self.connected_device_path, DEVICE_IFACE, self.bus)
                reply_message = device_iface.call("GetAll", DEVICE_IFACE)
                if reply_message.type() == QDBusMessage.MessageType.ErrorMessage:
                      print(f"BT Manager: Failed to get all props for {self.connected_device_path} on change: {reply_message.errorMessage()}")
                elif reply_message.arguments():
                      all_props = qvariant_dict_to_python(reply_message.arguments()[0])
                      self.process_device_properties(self.connected_device_path, all_props)
                else:
                      print(f"BT Manager: Got reply for GetAll device props {self.connected_device_path}, but no arguments.")

        except Exception as e:
            print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print(f"ERROR in on_device_properties_changed: {e}")
            traceback.print_exc()
            print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")


    def run(self):
        print("BluetoothManager thread started.") # DEBUG
        if not self.bus.isConnected():
            print("BT Manager: Failed to connect to D-Bus system bus.")
            self._is_running = False
            return

        self.adapter_path = self.find_adapter()
        if not self.adapter_path:
            print("BT Manager: Could not find Bluetooth adapter. Exiting thread.")
            self._is_running = False
            return
        print(f"DEBUG: BluetoothManager.run - Adapter found: {self.adapter_path}") # DEBUG

        # Get initial state
        om = QDBusInterface(BLUEZ_SERVICE, '/', DBUS_OM_IFACE, self.bus)
        print("DEBUG: BluetoothManager.run - Calling initial GetManagedObjects...") # DEBUG
        managed_objects_reply = om.call('GetManagedObjects')
        print(f"DEBUG: BluetoothManager.run - Initial GetManagedObjects type: {managed_objects_reply.type()}") # DEBUG
        if managed_objects_reply.type() == QDBusMessage.MessageType.ErrorMessage:
            print("BT Manager: Failed to get initial managed objects:", managed_objects_reply.errorMessage())
        elif managed_objects_reply.arguments():
             objects_dict = managed_objects_reply.arguments()[0]
             print(f"DEBUG: BluetoothManager.run - Processing {len(objects_dict)} initial objects...") # DEBUG
             for path, interfaces in objects_dict.items():
                 if DEVICE_IFACE in interfaces:
                      dev_props = qvariant_dict_to_python(interfaces.get(DEVICE_IFACE, {}))
                      self.process_device_properties(path, dev_props)
             print("DEBUG: BluetoothManager.run - Initial object processing done.") # DEBUG
             self.find_media_player(self.connected_device_path)
             print("DEBUG: BluetoothManager.run - Initial media player check done.") # DEBUG
        else:
             print("BT Manager: Got reply for initial GetManagedObjects, but no arguments.")


        # Connect signals
        print("DEBUG: BluetoothManager.run - Connecting D-Bus signals...") # DEBUG
        sig1_ok = self.bus.connect(BLUEZ_SERVICE, '/', DBUS_OM_IFACE, 'InterfacesAdded', self.on_interfaces_added)
        sig2_ok = self.bus.connect(BLUEZ_SERVICE, '/', DBUS_OM_IFACE, 'InterfacesRemoved', self.on_interfaces_removed)
        sig3_ok = self.bus.connect(BLUEZ_SERVICE, '', DBUS_PROP_IFACE, 'PropertiesChanged', self.on_device_properties_changed) # Generic device properties
        print(f"DEBUG: Signal connection status: InterfacesAdded={sig1_ok}, InterfacesRemoved={sig2_ok}, PropertiesChanged(Device)={sig3_ok}") # DEBUG

        if not sig1_ok or not sig3_ok:
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print("CRITICAL ERROR: Failed to connect essential D-Bus signals (InterfacesAdded or PropertiesChanged). Bluetooth monitoring will not work correctly.")
            print("Check slot signatures (@pyqtSlot) and D-Bus permissions.")
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            # Optionally, set self._is_running = False here if this is fatal

        print("BT Manager: D-Bus signals connected. Entering wait loop.")
        loop_count = 0
        while self._is_running:
            # DEBUG: Print loop status occasionally
            # if loop_count % 30 == 0: # Print every 30 seconds
            #     print(f"DEBUG: BluetoothManager running... Loop {loop_count}")
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
