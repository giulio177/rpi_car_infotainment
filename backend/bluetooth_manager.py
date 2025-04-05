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
        if isinstance(variant_value, dict):
            py_dict = {}
            for k, v in variant_value.items():
                py_dict[k] = qvariant_dict_to_python(v) # Recurse on values
            return py_dict
        elif isinstance(variant_value, list):
            return [qvariant_dict_to_python(item) for item in variant_value]
        else:
            return variant_value # Return as is

    value = variant_value.value()

    if isinstance(value, dict):
        py_dict = {}
        for k, v in value.items():
            py_dict[k] = qvariant_dict_to_python(v) # Recurse on values
        return py_dict
    elif isinstance(value, list):
        return [qvariant_dict_to_python(item) for item in value]
    else:
        return value


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

        objects_dict_variant = reply_message.arguments()[0]
        objects_dict = qvariant_dict_to_python(objects_dict_variant)

        print(f"DEBUG: BluetoothManager.find_adapter - Processing {len(objects_dict)} managed objects...")
        for path, interfaces in objects_dict.items():
            if 'org.bluez.Adapter1' in interfaces:
                print(f"BT Manager: Found adapter at {path}")
                return path
        print("BT Manager: No Bluetooth adapter found.")
        return None

    def process_device_properties(self, path, properties):
        """Checks device properties for connection and battery. Assumes 'properties' is a Python dict."""
        try:
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
                    self.find_media_player(path) # Check for player when device connects
                elif battery != self.current_battery:
                     print(f"BT Manager: Battery updated for {alias} to {battery}")
                     self.current_battery = battery
                     print(f"DEBUG: Emitting battery_updated({self.current_battery})")
                     self.battery_updated.emit(self.current_battery)

            elif self.connected_device_path == path:
                 print(f"BT Manager: Device disconnected - {alias} ({path})")
                 if self.media_player_path and self.media_player_path.startswith(path):
                      print(f"DEBUG: Disconnecting media properties signal for {self.media_player_path} due to device disconnect")
                      if self.bus.isConnected():
                          # Try disconnecting even if connection failed initially
                          self.bus.disconnect(BLUEZ_SERVICE, self.media_player_path, DBUS_PROP_IFACE, 'PropertiesChanged', self.on_media_properties_changed)
                      self.media_player_path = None

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
        objects_dict = qvariant_dict_to_python(objects_dict_variant)
        found_player_path = None
        print(f"DEBUG: BluetoothManager.find_media_player - Processing {len(objects_dict)} objects for media player...")

        for path, interfaces in objects_dict.items():
            if MEDIA_PLAYER_IFACE in interfaces:
                 player_props = interfaces.get(MEDIA_PLAYER_IFACE, {})
                 player_device = player_props.get('Device', "")

                 if device_path_hint and player_device == device_path_hint:
                     found_player_path = path
                     print(f"BT Manager: Found media player for connected device at {path}")
                     break
                 elif not device_path_hint and not found_player_path:
                      if player_device and player_device.startswith("/org/bluez/hci"):
                           found_player_path = path
                           print(f"BT Manager: Found media player (generic, attached to a device) at {path}")

        if found_player_path and found_player_path != self.media_player_path:
            print(f"BT Manager: Media player activated at {found_player_path}")
            if self.media_player_path and self.bus.isConnected():
                 print(f"DEBUG: Disconnecting OLD media properties signal for {self.media_player_path}")
                 self.bus.disconnect(BLUEZ_SERVICE, self.media_player_path, DBUS_PROP_IFACE, 'PropertiesChanged', self.on_media_properties_changed)
            self.media_player_path = found_player_path
            self.monitor_media_player(found_player_path) # Gets initial state
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

        # Removed signal connection attempt as it failed

        # Get initial properties using the correct Properties interface
        print("DEBUG: BluetoothManager.monitor_media_player - Getting initial props...")
        props_iface = QDBusInterface(BLUEZ_SERVICE, player_path, DBUS_PROP_IFACE, self.bus)
        reply_message = props_iface.call("GetAll", MEDIA_PLAYER_IFACE)
        print(f"DEBUG: BluetoothManager.monitor_media_player - GetAll returned type: {reply_message.type()}")
        if reply_message.type() != QDBusMessage.MessageType.ErrorMessage and reply_message.arguments():
             initial_props_variant = reply_message.arguments()[0]
             initial_props = qvariant_dict_to_python(initial_props_variant)
             print(f"DEBUG: Initial media props: {initial_props}")
             self.update_media_state(initial_props) # Update state based on initial props
        else:
             print(f"BT Manager: Failed to get initial media props from {player_path}: {reply_message.errorMessage() if reply_message.type() == QDBusMessage.MessageType.ErrorMessage else 'No arguments'}")

    # --- Slots (Decorators removed or adjusted for working signals) ---

    # Method kept, but not connected to failing signal
    # @pyqtSlot(str, object, "QStringList")
    def on_media_properties_changed(self, interface_name, changed_properties_obj, invalidated_properties):
        print("!!! on_media_properties_changed called unexpectedly !!!")
        pass

    # This method IS called by polling loop and initial setup
    def update_media_state(self, properties):
        """Updates internal state and emits signals based on media properties. Assumes 'properties' is Python dict."""
        track_changed = False
        status_changed = False
        position_changed = False
        position_value = properties.get('Position', -1)

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

        if 'Position' in properties:
            if position_value >= 0 and position_value != self.media_properties.get('Position', -1):
                 position_changed = True
            if 'Track' in self.media_properties or track_changed:
                 self.media_properties['Position'] = position_value

        # Emit signals based on detected changes
        if status_changed:
             print(f"DEBUG: Emitting playback_status_changed({self.playback_status})")
             self.playback_status_changed.emit(self.playback_status)

        if track_changed or (position_changed and self.playback_status == 'playing'):
             if 'Position' in properties: self.media_properties['Position'] = position_value
             print(f"DEBUG: Emitting media_properties_changed({self.media_properties})")
             self.media_properties_changed.emit(self.media_properties)


    # Method kept, but not connected to failing signal
    # @pyqtSlot(str, object)
    def on_interfaces_added(self, path, interfaces_and_properties_obj):
        print("!!! on_interfaces_added called unexpectedly !!!")
        pass

    # Keep working slot
    @pyqtSlot(str, "QStringList")
    def on_interfaces_removed(self, path, interfaces):
        """Handles D-Bus InterfacesRemoved signal."""
        try:
            print(f"DEBUG: on_interfaces_removed triggered for path: {path}, Interfaces: {interfaces}")
            if DEVICE_IFACE in interfaces:
                 print(f"BT Manager: Interface removed for Device: {path}")
                 if path == self.connected_device_path:
                     self.process_device_properties(path, {'Connected': False})
            elif MEDIA_PLAYER_IFACE in interfaces:
                 print(f"BT Manager: Interface removed for Media Player: {path}")
                 if path == self.media_player_path:
                     print("DEBUG: Clearing media player state due to InterfacesRemoved")
                     self.media_player_path = None
                     self.media_properties = {}
                     self.playback_status = "stopped"
                     self.media_properties_changed.emit({})
                     self.playback_status_changed.emit("stopped")

        except Exception as e:
            print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print(f"ERROR in on_interfaces_removed for path {path}: {e}")
            traceback.print_exc()
            print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")


    # Method kept, but not connected to failing signal
    # @pyqtSlot(str, object, "QStringList")
    def on_device_properties_changed(self, interface_name, changed_properties_obj, invalidated_properties):
        print("!!! on_device_properties_changed called unexpectedly !!!")
        pass


    # --- run Method (Polling Implementation) ---
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

        # Get initial state via method calls
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
                      self.process_device_properties(path, dev_props) # Finds initial device/player
             print("DEBUG: BluetoothManager.run - Initial object processing done.")
             print("DEBUG: BluetoothManager.run - Initial media player check done (implicitly).")
        else:
             print(f"BT Manager: Failed to get initial managed objects: {managed_objects_reply.errorMessage() if managed_objects_reply.type() == QDBusMessage.MessageType.ErrorMessage else 'No arguments'}")


        # Connect ONLY working signals
        print("DEBUG: BluetoothManager.run - Connecting D-Bus signals (Polling approach)...")
        sig2_ok = self.bus.connect(BLUEZ_SERVICE, '/', DBUS_OM_IFACE, 'InterfacesRemoved', self.on_interfaces_removed)
        print(f"DEBUG: Signal connection status: InterfacesRemoved={sig2_ok}")


        print("BT Manager: Entering polling loop.")
        poll_interval_ms = 2000 # Poll every 2 seconds
        loop_count = 0
        om_iface = QDBusInterface(BLUEZ_SERVICE, '/', DBUS_OM_IFACE, self.bus) # Reuse interface object

        while self._is_running:
            # --- POLLING LOGIC ---
            try:
                # 1. Poll Connected Device Properties
                current_connected_path = self.connected_device_path
                if current_connected_path:
                    dev_props_iface = QDBusInterface(BLUEZ_SERVICE, current_connected_path, DBUS_PROP_IFACE, self.bus)
                    dev_reply = dev_props_iface.call("GetAll", DEVICE_IFACE)
                    if dev_reply.type() != QDBusMessage.MessageType.ErrorMessage and dev_reply.arguments():
                        dev_props_all = qvariant_dict_to_python(dev_reply.arguments()[0])
                        if not dev_props_all.get('Connected', False):
                             print("DEBUG: Device disconnected detected via polling.")
                             self.process_device_properties(current_connected_path, {'Connected': False})
                             continue
                        elif dev_props_all.get('Battery', None) != self.current_battery:
                             print("DEBUG: Battery change detected via polling.")
                             self.current_battery = dev_props_all.get('Battery', None)
                             self.battery_updated.emit(self.current_battery)
                    else:
                         print(f"DEBUG: Failed to poll device {current_connected_path}, assuming disconnect.")
                         self.process_device_properties(current_connected_path, {'Connected': False})
                         continue

                # 2. Poll Media Player Properties
                current_media_path = self.media_player_path
                if current_media_path:
                     media_props_iface = QDBusInterface(BLUEZ_SERVICE, current_media_path, DBUS_PROP_IFACE, self.bus)
                     media_reply = media_props_iface.call("GetAll", MEDIA_PLAYER_IFACE)
                     if media_reply.type() != QDBusMessage.MessageType.ErrorMessage and media_reply.arguments():
                          media_props_all = qvariant_dict_to_python(media_reply.arguments()[0])
                          self.update_media_state(media_props_all) # Let update_media_state compare and emit
                     # else: # Optionally log media poll failure
                     #    print(f"DEBUG: Failed to poll media player {current_media_path}")

                # 3. Poll for NEW devices/players (less frequent?)
                if loop_count % 5 == 0: # Check every ~10 seconds
                    om_reply = om_iface.call('GetManagedObjects')
                    if om_reply.type() != QDBusMessage.MessageType.ErrorMessage and om_reply.arguments():
                        obj_dict = qvariant_dict_to_python(om_reply.arguments()[0])
                        # Find newly connected device
                        if not self.connected_device_path:
                             for path, interfaces in obj_dict.items():
                                 if DEVICE_IFACE in interfaces:
                                      dev_props = interfaces.get(DEVICE_IFACE, {})
                                      if dev_props.get('Connected', False):
                                           print("DEBUG: New device connection detected via polling.")
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
            self.msleep(poll_interval_ms) # Wait before next poll


        # Disconnect signals on exit
        print("BT Manager: Disconnecting D-Bus signals.")
        if self.bus.isConnected():
             self.bus.disconnect(BLUEZ_SERVICE, '/', DBUS_OM_IFACE, 'InterfacesRemoved', self.on_interfaces_removed)

        print("BluetoothManager thread finished.")


    def stop(self):
        print("BluetoothManager: Stop requested.")
        self._is_running = False

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
            player_iface = QDBusInterface(BLUEZ_SERVICE, self.media_player_path, MEDIA_PLAYER_IFACE, self.bus)
            reply_message = player_iface.call(command)

            if reply_message.type() == QDBusMessage.MessageType.ErrorMessage:
                 print(f"BT Manager: Error sending command '{command}': {reply_message.errorMessage()}")
                 return False
            else:
                 print(f"BT Manager: Command '{command}' sent successfully.")
                 # Status update will come via polling shortly after
                 return True
        except Exception as e:
            print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print(f"ERROR sending command '{command}': {e}")
            traceback.print_exc()
            print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            return False

    def send_play(self):
        return self._send_media_command("Play")

    def send_pause(self):
        return self._send_media_command("Pause")

    def send_next(self):
        return self._send_media_command("Next")

    def send_previous(self):
        return self._send_media_command("Previous")

    def send_stop(self):
        return self._send_media_command("Stop")
