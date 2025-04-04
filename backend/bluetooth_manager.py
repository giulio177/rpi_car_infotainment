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
            py_dict = {}
            for k, v in variant_value.items():
                py_dict[k] = qvariant_dict_to_python(v) # Recurse on values
            return py_dict
        elif isinstance(variant_value, list):
            return [qvariant_dict_to_python(item) for item in variant_value]
        else:
            return variant_value # Return as is

    # If it IS a QVariant, unwrap it first
    value = variant_value.value()

    if isinstance(value, dict):
        py_dict = {}
        for k, v in value.items():
            py_dict[k] = qvariant_dict_to_python(v) # Recurse on values
        return py_dict
    elif isinstance(value, list):
        return [qvariant_dict_to_python(item) for item in value]
    else:
        return value # Return the unwrapped primitive value


class BluetoothManager(QThread):
    # Signals
    connection_changed = pyqtSignal(bool, str)
    battery_updated = pyqtSignal(object) # Use object for None support
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
        try:
            is_connected = properties.get('Connected', False)
            device_name = properties.get('Name', "Unknown Device")
            alias = properties.get('Alias', device_name)
            battery = properties.get('Battery', None) # Battery often None

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
                      print(f"DEBUG: Disconnecting media properties signal for {self.media_player_path} due to device disconnect")
                      # Check if connection exists before disconnecting
                      if self.bus.isConnected():
                          self.bus.disconnect(BLUEZ_SERVICE, self.media_player_path, DBUS_PROP_IFACE, 'PropertiesChanged', self.on_media_properties_changed)
                      self.media_player_path = None # Clear media player path

                 self.connected_device_path = None
                 self.connected_device_name = "Disconnected"
                 self.current_battery = None
                 self.media_properties = {}
                 self.playback_status = "stopped"
                 print(f"DEBUG: Emitting connection_changed(False, ...)")
                 self.connection_changed.emit(False, "Disconnected")
                 print(f"DEBUG: Emitting battery_updated(None)")
                 self.battery_updated.emit(None)
                 print(f"DEBUG: Emitting media_properties_changed({{}})")
                 self.media_properties_changed.emit({})
                 print(f"DEBUG: Emitting playback_status_changed('stopped')")
                 self.playback_status_changed.emit("stopped")
        except Exception as e:
             print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
             print(f"ERROR in process_device_properties for path {path}: {e}")
             traceback.print_exc()
             print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

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
        objects_dict = qvariant_dict_to_python(objects_dict_variant) # Convert here
        found_player_path = None
        print(f"DEBUG: BluetoothManager.find_media_player - Processing {len(objects_dict)} objects for media player...")

        for path, interfaces in objects_dict.items():
            # interfaces is Dict[str, Dict[str, Any]]
            if MEDIA_PLAYER_IFACE in interfaces:
                 player_props = interfaces.get(MEDIA_PLAYER_IFACE, {}) # Already Python dict
                 player_device = player_props.get('Device', "")

                 if device_path_hint and player_device == device_path_hint:
                     found_player_path = path
                     print(f"BT Manager: Found media player for connected device at {path}")
                     break
                 elif not device_path_hint and not found_player_path:
                      if player_device and player_device.startswith("/org/bluez/hci"):
                           found_player_path = path
                           print(f"BT Manager: Found media player (generic, attached to a device) at {path}")
                      # else: print(f"DEBUG: Skipping player {path} with no device property: {player_props}")


        if found_player_path and found_player_path != self.media_player_path:
            print(f"BT Manager: Media player activated at {found_player_path}")
            if self.media_player_path and self.bus.isConnected():
                 print(f"DEBUG: Disconnecting OLD media properties signal for {self.media_player_path}")
                 self.bus.disconnect(BLUEZ_SERVICE, self.media_player_path, DBUS_PROP_IFACE, 'PropertiesChanged', self.on_media_properties_changed)
            self.media_player_path = found_player_path
            self.monitor_media_player(found_player_path) # Connect new listener
            return True
        elif not found_player_path and self.media_player_path:
             print("BT Manager: Active media player seems to be gone.")
             if self.media_player_path and self.bus.isConnected():
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
        """Gets initial state for a specific media player."""
        if not player_path: return

        # REMOVED signal connection attempt:
        # connection_success = self.bus.connect(...)
        # print(f"DEBUG: Connection status for media properties: {connection_success}") # REMOVED

        # Get initial properties using the CORRECT interface
        print("DEBUG: BluetoothManager.monitor_media_player - Getting initial props...")
        props_iface = QDBusInterface(BLUEZ_SERVICE, player_path, DBUS_PROP_IFACE, self.bus)
        reply_message = props_iface.call("GetAll", MEDIA_PLAYER_IFACE)
        print(f"DEBUG: BluetoothManager.monitor_media_player - GetAll returned type: {reply_message.type()}")
        if reply_message.type() != QDBusMessage.MessageType.ErrorMessage and reply_message.arguments():
             initial_props_variant = reply_message.arguments()[0]
             initial_props = qvariant_dict_to_python(initial_props_variant)
             print(f"DEBUG: Initial media props: {initial_props}")
             self.update_media_state(initial_props)
        else:
             print(f"BT Manager: Failed to get initial media props from {player_path}: {reply_message.errorMessage() if reply_message.type() == QDBusMessage.MessageType.ErrorMessage else 'No arguments'}")


    # --- Slots with @pyqtSlot decorator and 'object' hint for dictionaries ---

    # PropertiesChanged D-Bus signature: (string interface_name, a{sv} changed_properties, as invalidated_properties)
    # @pyqtSlot(str, object, "QStringList") # Use object for a{sv}
    def on_media_properties_changed(self, interface_name, changed_properties_obj, invalidated_properties):
       # This slot will not be called if connection failed
       print("!!! on_media_properties_changed called unexpectedly !!!")
       pass # Keep method for potential future use? Or remove entirely


    def update_media_state(self, properties):
        # print(f"DEBUG: BluetoothManager.update_media_state - Python props: {properties}")
        """Updates internal state and emits signals based on media properties. Assumes 'properties' is Python dict."""
        track_changed = False
        status_changed = False
        position_changed = False # ADDED flag
        position_value = properties.get('Position', -1) # Get current position value early

        if 'Track' in properties:
            track_info = properties.get('Track', {})
            if isinstance(track_info, dict) and track_info != self.media_properties.get('Track', {}):
                track_changed = True
                print(f"BT Manager: Track Info Updated (Poll): {track_info}")
                self.media_properties['Track'] = track_info
            elif not isinstance(track_info, dict):
                 print(f"DEBUG: Unexpected type for Track property in update_media_state: {type(track_info)}")

        if 'Status' in properties:
            status = properties.get('Status', 'stopped')
            if status != self.playback_status:
                status_changed = True
                print(f"BT Manager: Playback Status Updated (Poll): {status}")
                self.playback_status = status # Update internal status FIRST

        # Check position change *after* potentially updating track or status
        if 'Position' in properties:
            # Compare with OLD stored position BEFORE overwriting it below
            if position_value >= 0 and position_value != self.media_properties.get('Position', -1):
                 position_changed = True
                 # print(f"DEBUG: Position changed: {self.media_properties.get('Position', -1)} -> {position_value}") # Verbose debug
            # Always store the LATEST position if track info exists or track just changed
            if 'Track' in self.media_properties or track_changed:
                 self.media_properties['Position'] = position_value

        # --- Emit signals based on detected changes ---
        if status_changed:
             print(f"DEBUG: Emitting playback_status_changed({self.playback_status})")
             self.playback_status_changed.emit(self.playback_status)

        # Emit media properties if track changed OR if position changed WHILE playing
        # Use the LATEST known status (self.playback_status) for the check
        if track_changed or (position_changed and self.playback_status == 'playing'):
             # Ensure position is up-to-date in the dict being emitted
             if 'Position' in properties: self.media_properties['Position'] = position_value
             print(f"DEBUG: Emitting media_properties_changed({self.media_properties})")
             self.media_properties_changed.emit(self.media_properties)


    # InterfacesAdded D-Bus signature: (ObjectPath object_path, a{sa{sv}} interfaces_and_properties)
    # @pyqtSlot(str, object) # Use object for the complex dict a{sa{sv}}
    def on_interfaces_added(self, path, interfaces_and_properties_obj):
        # This slot will not be called if connection failed
        print("!!! on_interfaces_added called unexpectedly !!!")
        pass # Keep method for potential future use? Or remove entirely

    # InterfacesRemoved D-Bus signature: (ObjectPath object_path, as interfaces_removed)
    @pyqtSlot(str, "QStringList") # Keep this as it worked
    def on_interfaces_removed(self, path, interfaces):
        """Handles D-Bus InterfacesRemoved signal."""
        try:
            print(f"DEBUG: on_interfaces_removed triggered for path: {path}, Interfaces: {interfaces}")
            if DEVICE_IFACE in interfaces:
                 print(f"BT Manager: Interface removed for Device: {path}")
                 if path == self.connected_device_path:
                     # Trigger disconnect logic
                     self.process_device_properties(path, {'Connected': False})
            elif MEDIA_PLAYER_IFACE in interfaces:
                 print(f"BT Manager: Interface removed for Media Player: {path}")
                 if path == self.media_player_path:
                     # Clear media player state manually since PropertiesChanged signal isn't working
                     print("DEBUG: Clearing media player state due to InterfacesRemoved")
                     self.media_player_path = None
                     self.media_properties = {}
                     self.playback_status = "stopped"
                     self.media_properties_changed.emit({})
                     self.playback_status_changed.emit("stopped")
                     # Optionally call find_media_player() again if another might exist?

        except Exception as e:
            print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print(f"ERROR in on_interfaces_removed for path {path}: {e}")
            traceback.print_exc()
            print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")


    # PropertiesChanged D-Bus signature: (string interface_name, a{sv} changed_properties, as invalidated_properties)
    # @pyqtSlot(str, object, "QStringList") # DECORATOR REMOVED / METHOD NOT CALLED BY SIGNAL
    def on_device_properties_changed(self, interface_name, changed_properties_obj, invalidated_properties):
        # This slot will not be called if connection failed
        print("!!! on_device_properties_changed called unexpectedly !!!")
        pass # Keep method for potential future use? Or remove entirely


    # --- run Method ---
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

        # --- Get initial state (remains the same) ---
        om = QDBusInterface(BLUEZ_SERVICE, '/', DBUS_OM_IFACE, self.bus)
        print("DEBUG: BluetoothManager.run - Calling initial GetManagedObjects...")
        managed_objects_reply = om.call('GetManagedObjects')
        print(f"DEBUG: BluetoothManager.run - Initial GetManagedObjects type: {managed_objects_reply.type()}")
        if managed_objects_reply.type() != QDBusMessage.MessageType.ErrorMessage and managed_objects_reply.arguments():
             objects_dict_variant = managed_objects_reply.arguments()[0]
             objects_dict = qvariant_dict_to_python(objects_dict_variant)
             print(f"DEBUG: BluetoothManager.run - Processing {len(objects_dict)} initial objects...")
             for path, interfaces in objects_dict.items():
                 if DEVICE_IFACE in interfaces:
                      dev_props = interfaces.get(DEVICE_IFACE, {})
                      self.process_device_properties(path, dev_props) # Finds initial connected device
             print("DEBUG: BluetoothManager.run - Initial object processing done.")
             # find_media_player is called inside process_device_properties if device connects
             print("DEBUG: BluetoothManager.run - Initial media player check done (implicitly).")
        else:
             print(f"BT Manager: Failed to get initial managed objects: {managed_objects_reply.errorMessage() if managed_objects_reply.type() == QDBusMessage.MessageType.ErrorMessage else 'No arguments'}")


        # --- Connect ONLY working/needed signals ---
        print("DEBUG: BluetoothManager.run - Connecting D-Bus signals (Polling approach)...")
        # REMOVED: sig1_ok = self.bus.connect(..., self.on_interfaces_added)
        sig2_ok = self.bus.connect(BLUEZ_SERVICE, '/', DBUS_OM_IFACE, 'InterfacesRemoved', self.on_interfaces_removed) # Keep working one
        # REMOVED: sig3_ok = self.bus.connect(..., self.on_device_properties_changed)

        print(f"DEBUG: Signal connection status: InterfacesRemoved={sig2_ok}") # Report only connected one


        print("BT Manager: Entering polling loop.")
        poll_interval_ms = 1000 # Poll every 2 seconds (adjust as needed)
        loop_count = 0

        while self._is_running:
            # --- POLLING LOGIC ---
            try:
                # 1. Poll Connected Device Properties (if connected)
                current_connected_path = self.connected_device_path
                if current_connected_path:
                    dev_props_iface = QDBusInterface(BLUEZ_SERVICE, current_connected_path, DBUS_PROP_IFACE, self.bus)
                    dev_reply = dev_props_iface.call("GetAll", DEVICE_IFACE)
                    if dev_reply.type() != QDBusMessage.MessageType.ErrorMessage and dev_reply.arguments():
                        dev_props_all = qvariant_dict_to_python(dev_reply.arguments()[0])
                        if not dev_props_all.get('Connected', False):
                             print("DEBUG: Device disconnected detected via polling.")
                             self.process_device_properties(current_connected_path, {'Connected': False})
                             continue # Skip media poll if disconnected
                        elif dev_props_all.get('Battery', None) != self.current_battery:
                             print("DEBUG: Battery change detected via polling.")
                             self.current_battery = dev_props_all.get('Battery', None)
                             self.battery_updated.emit(self.current_battery)
                    else:
                         print(f"DEBUG: Failed to poll device {current_connected_path}, assuming disconnect.")
                         self.process_device_properties(current_connected_path, {'Connected': False})
                         continue

                # 2. Poll Media Player Properties (if active)
                current_media_path = self.media_player_path
                if current_media_path:
                     media_props_iface = QDBusInterface(BLUEZ_SERVICE, current_media_path, DBUS_PROP_IFACE, self.bus)
                     media_reply = media_props_iface.call("GetAll", MEDIA_PLAYER_IFACE)
                     if media_reply.type() != QDBusMessage.MessageType.ErrorMessage and media_reply.arguments():
                          media_props_all = qvariant_dict_to_python(media_reply.arguments()[0])
                          # --- MODIFIED: Always call update_media_state ---
                          # Let the method handle comparisons and signal emission
                          self.update_media_state(media_props_all)
                          # --- END MODIFICATION ---
                     # else: # Log error if needed but don't assume disconnect based only on this
                     #    print(f"DEBUG: Failed to poll media player {current_media_path}")


                # 3. Poll for NEW devices/players (less frequent?)
                if loop_count % 5 == 0: # Check every 10 seconds
                    # Use the om_iface reference created before the loop
                    om_reply = om_iface.call('GetManagedObjects') # Reuse interface object
                    if om_reply.type() != QDBusMessage.MessageType.ErrorMessage and om_reply.arguments():
                        obj_dict = qvariant_dict_to_python(om_reply.arguments()[0])
                        # Find newly connected device (if none currently connected)
                        if not self.connected_device_path:
                             for path, interfaces in obj_dict.items():
                                 if DEVICE_IFACE in interfaces:
                                      dev_props = interfaces.get(DEVICE_IFACE, {})
                                      if dev_props.get('Connected', False):
                                           print("DEBUG: New device connection detected via polling.")
                                           self.process_device_properties(path, dev_props)
                                           break # Process first found
                        # Find newly appeared media player (if none currently active but device is connected)
                        elif not self.media_player_path and self.connected_device_path:
                             self.find_media_player(self.connected_device_path) # Check if player appeared


            except Exception as e:
                 print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                 print(f"ERROR in BluetoothManager polling loop: {e}")
                 traceback.print_exc()
                 print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

            # --- End Polling Logic ---

            loop_count += 1
            self.msleep(poll_interval_ms) # Wait before next poll


        # Disconnect signals on exit
        print("BT Manager: Disconnecting D-Bus signals.")
        if self.bus.isConnected():
             # Only disconnect the one we successfully connected
             self.bus.disconnect(BLUEZ_SERVICE, '/', DBUS_OM_IFACE, 'InterfacesRemoved', self.on_interfaces_removed)
             # REMOVED disconnect calls for signals we didn't connect

        print("BluetoothManager thread finished.")


    def stop(self):
        print("BluetoothManager: Stop requested.")
        self._is_running = False
