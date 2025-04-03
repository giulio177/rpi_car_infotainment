# backend/bluetooth_manager.py

import time
from PyQt6.QtCore import QThread, pyqtSignal, QVariant, QObject, pyqtSlot
from PyQt6.QtDBus import QDBusConnection, QDBusInterface, QDBusMessage

# Constants for BlueZ D-Bus
BLUEZ_SERVICE = 'org.bluez'
DBUS_OM_IFACE = 'org.freedesktop.DBus.ObjectManager'
DBUS_PROP_IFACE = 'org.freedesktop.DBus.Properties'

DEVICE_IFACE = 'org.bluez.Device1'
MEDIA_PLAYER_IFACE = 'org.bluez.MediaPlayer1'
MEDIA_CONTROL_IFACE = 'org.bluez.MediaControl1' # Might be needed for play/pause actions

# --- Important Note on Battery ---
# Standard Bluetooth battery reporting (Bluetooth SIG Battery Service / GATT)
# is often NOT exposed directly via the BlueZ D-Bus Device1 interface.
# Some devices might expose it via vendor-specific AT commands (HFP profile) or
# sometimes via non-standard properties. This implementation checks the standard
# 'Battery' property on Device1, but it might often be missing or None.


# Helper to convert QVariant dictionary to Python dict
def qvariant_dict_to_python(qvariant_dict):
    py_dict = {}
    if isinstance(qvariant_dict, QVariant):
        # Unwrap the QVariant first if necessary
        qvariant_dict = qvariant_dict.value()

    if isinstance(qvariant_dict, dict):
         # QDBus sends dicts as QVariantMap which behaves like python dict
        for key, value in qvariant_dict.items():
            if isinstance(value, QVariant):
                py_dict[key] = value.value() # Extract value from QVariant
            else:
                py_dict[key] = value # Assume basic type if not QVariant
    return py_dict


class BluetoothManager(QThread):
    # Signals
    # connection_changed(connected: bool, device_name: str)
    connection_changed = pyqtSignal(bool, str)
    # battery_updated(level: int | None) # None if not available/disconnected
    battery_updated = pyqtSignal(object) # Use object type hint for None support
    # media_properties_changed(properties: dict)
    media_properties_changed = pyqtSignal(dict)
    # playback_status_changed(status: str) e.g., "playing", "paused", "stopped"
    playback_status_changed = pyqtSignal(str)


    def __init__(self):
        super().__init__()
        self._is_running = True
        self.bus = QDBusConnection.systemBus() # Connect to system D-Bus

        # State variables
        self.adapter_path = None
        self.connected_device_path = None
        self.connected_device_name = "Disconnected"
        self.current_battery = None
        self.media_player_path = None
        self.media_properties = {}
        self.playback_status = "stopped"

        # Register custom types if needed (often automatic with PyQt >= 6.3)
        # QDBusMetaType.registerStructure( ... ) # If complex structures are used

    def find_adapter(self):
        """Finds the first available Bluetooth adapter."""
        om = QDBusInterface(BLUEZ_SERVICE, '/', DBUS_OM_IFACE, self.bus)
        managed_objects = om.call('GetManagedObjects')
        if not managed_objects.isValid():
            print("BT Manager: Error getting managed objects:", managed_objects.error().message())
            return None

        # QDBusMessage returns arguments as a list, GetManagedObjects returns one dict arg
        objects_dict = managed_objects.arguments()[0]

        for path, interfaces in objects_dict.items():
            if 'org.bluez.Adapter1' in interfaces:
                print(f"BT Manager: Found adapter at {path}")
                return path
        print("BT Manager: No Bluetooth adapter found.")
        return None

    def process_device_properties(self, path, properties):
        """Checks device properties for connection and battery."""
        is_connected = properties.get('Connected', QVariant(False)).value()
        device_name = properties.get('Name', QVariant("Unknown Device")).value()
        alias = properties.get('Alias', QVariant(device_name)).value() # Prefer Alias if set
        # Battery property is often missing or unreliable via Device1
        battery = properties.get('Battery', QVariant(None)).value() # Default to None QVariant

        if is_connected:
            if self.connected_device_path != path:
                print(f"BT Manager: Device connected - {alias} ({path})")
                self.connected_device_path = path
                self.connected_device_name = alias
                self.current_battery = battery # Might be None
                self.connection_changed.emit(True, self.connected_device_name)
                self.battery_updated.emit(self.current_battery) # Emit initial battery
                self.find_media_player(path) # Check if it has a media player now
            # Check if battery updated for already connected device
            elif battery != self.current_battery:
                 print(f"BT Manager: Battery updated for {alias} to {battery}")
                 self.current_battery = battery
                 self.battery_updated.emit(self.current_battery)

        elif self.connected_device_path == path: # Was connected, now disconnected
             print(f"BT Manager: Device disconnected - {alias} ({path})")
             self.connected_device_path = None
             self.connected_device_name = "Disconnected"
             self.current_battery = None
             self.media_player_path = None # Media player gone if device disconnected
             self.media_properties = {}
             self.playback_status = "stopped"
             self.connection_changed.emit(False, self.connected_device_name)
             self.battery_updated.emit(None)
             self.media_properties_changed.emit({}) # Clear media info
             self.playback_status_changed.emit("stopped")

    def find_media_player(self, device_path_hint=None):
        """Finds the active media player, optionally prioritizing one on a specific device."""
        # MediaPlayer1 interface might be directly under the device or elsewhere
        om = QDBusInterface(BLUEZ_SERVICE, '/', DBUS_OM_IFACE, self.bus)
        managed_objects = om.call('GetManagedObjects')
        if not managed_objects.isValid():
            print("BT Manager: Error getting managed objects for media player:", managed_objects.error().message())
            return False

        objects_dict = managed_objects.arguments()[0]
        found_player_path = None

        for path, interfaces in objects_dict.items():
            if MEDIA_PLAYER_IFACE in interfaces:
                 # Check if this player belongs to our connected device (if known)
                player_props = interfaces.get(MEDIA_PLAYER_IFACE, {})
                player_device = player_props.get('Device', QVariant("")).value()

                if device_path_hint and player_device == device_path_hint:
                    found_player_path = path
                    print(f"BT Manager: Found media player for connected device at {path}")
                    break # Found the specific one
                elif not device_path_hint and not found_player_path:
                     # If no hint, take the first one found (may not be right if multiple)
                     found_player_path = path
                     print(f"BT Manager: Found media player (generic) at {path}")
                     # Don't break, keep looking for hinted one if applicable

        if found_player_path and found_player_path != self.media_player_path:
            print(f"BT Manager: Media player activated at {found_player_path}")
            self.media_player_path = found_player_path
            self.monitor_media_player(found_player_path)
            return True
        elif not found_player_path and self.media_player_path:
             print("BT Manager: Active media player seems to be gone.")
             self.media_player_path = None
             self.media_properties = {}
             self.playback_status = "stopped"
             self.media_properties_changed.emit({})
             self.playback_status_changed.emit("stopped")
             return False
        return found_player_path is not None


    def monitor_media_player(self, player_path):
        """Connects signals for a specific media player."""
        if not player_path: return

        # Monitor PropertiesChanged for the media player
        prop_iface_mp = QDBusInterface(BLUEZ_SERVICE, player_path, DBUS_PROP_IFACE, self.bus)
        self.bus.connect(
            BLUEZ_SERVICE, player_path, DBUS_PROP_IFACE, 'PropertiesChanged',
            self.on_media_properties_changed
        )

        # Get initial properties
        media_player_iface = QDBusInterface(BLUEZ_SERVICE, player_path, MEDIA_PLAYER_IFACE, self.bus)
        reply = media_player_iface.call("GetAll", MEDIA_PLAYER_IFACE) # Correct way to get all props for an iface
        if reply.isValid():
             initial_props = reply.arguments()[0] # It returns a dict[str, QVariant]
             self.update_media_state(initial_props)
        else:
            print(f"BT Manager: Failed to get initial media props from {player_path}: {reply.error().message()}")


    @pyqtSlot(str, dict, "QStringList")
    def on_media_properties_changed(self, interface_name, changed_properties, invalidated_properties):
        """Handles D-Bus PropertiesChanged signal for MediaPlayer1."""
        if interface_name == MEDIA_PLAYER_IFACE:
            print("BT Manager: Media properties changed:", changed_properties)
            self.update_media_state(changed_properties)

    def update_media_state(self, properties_variant_map):
        """Updates internal state and emits signals based on media properties."""
        # Convert QVariantMap to Python dict for easier handling
        properties = qvariant_dict_to_python(properties_variant_map)

        new_track_info = None
        new_status = None

        if 'Track' in properties:
            track_info_variant = properties['Track']
            track_info = qvariant_dict_to_python(track_info_variant)
            if track_info != self.media_properties.get('Track', {}):
                new_track_info = track_info
                print(f"BT Manager: Track Info Updated: {new_track_info}")
                self.media_properties['Track'] = new_track_info
                self.media_properties_changed.emit(self.media_properties) # Emit full properties dict

        if 'Status' in properties:
            status = properties['Status']
            if status != self.playback_status:
                new_status = status
                print(f"BT Manager: Playback Status Updated: {new_status}")
                self.playback_status = new_status
                self.playback_status_changed.emit(new_status)

        # Update position if needed (example)
        if 'Position' in properties:
             position = properties['Position']
             self.media_properties['Position'] = position # Store position if you need it

    @pyqtSlot(QDBusMessage)
    def on_interfaces_added(self, path, interfaces_and_properties):
        """Handles D-Bus InterfacesAdded signal."""
        if DEVICE_IFACE in interfaces_and_properties:
            # A new device appeared, check its initial properties
            print(f"BT Manager: Interface added for Device: {path}")
            props = qvariant_dict_to_python(interfaces_and_properties.get(DEVICE_IFACE, {}))
            self.process_device_properties(path, props)
        elif MEDIA_PLAYER_IFACE in interfaces_and_properties:
             # A media player appeared
             print(f"BT Manager: Interface added for Media Player: {path}")
             self.find_media_player() # Re-evaluate active player

    @pyqtSlot(QDBusMessage)
    def on_interfaces_removed(self, path, interfaces):
        """Handles D-Bus InterfacesRemoved signal."""
        if DEVICE_IFACE in interfaces:
             print(f"BT Manager: Interface removed for Device: {path}")
             if path == self.connected_device_path:
                 # Our connected device was removed/disconnected
                 self.process_device_properties(path, {'Connected': QVariant(False)}) # Trigger disconnect logic
        elif MEDIA_PLAYER_IFACE in interfaces:
             print(f"BT Manager: Interface removed for Media Player: {path}")
             if path == self.media_player_path:
                 self.find_media_player() # Re-evaluate active player (likely gone)


    @pyqtSlot(str, dict, "QStringList")
    def on_device_properties_changed(self, interface_name, changed_properties, invalidated_properties):
        """Handles D-Bus PropertiesChanged signal for Device1."""
        # This slot needs context (the object path) which isn't provided by the signal directly.
        # We need to get the sender's path.
        sender_path = self.sender().path() # Get path from the QDBusAbstractInterface sender
        if not sender_path:
            # Fallback: try getting path from message (less reliable)
            message = self.sender().message()
            sender_path = message.path() if message else None

        if interface_name == DEVICE_IFACE and sender_path:
             print(f"BT Manager: Device properties changed for {sender_path}: {changed_properties}")
             props = qvariant_dict_to_python(changed_properties)
             # We need the full properties to correctly determine connection status/name
             # Let's re-fetch all properties for the device when something changes
             device_iface = QDBusInterface(BLUEZ_SERVICE, sender_path, DEVICE_IFACE, self.bus)
             reply = device_iface.call("GetAll", DEVICE_IFACE)
             if reply.isValid():
                  all_props = qvariant_dict_to_python(reply.arguments()[0])
                  self.process_device_properties(sender_path, all_props)
             else:
                 print(f"BT Manager: Failed to get all props for {sender_path} on change.")
                 # Fallback: try using only changed props (might miss context)
                 # self.process_device_properties(sender_path, props)
        else:
            # print(f"Ignoring property change for {interface_name} on {sender_path}")
            pass


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

        # Use ObjectManager to get initial state and monitor added/removed interfaces
        om = QDBusInterface(BLUEZ_SERVICE, '/', DBUS_OM_IFACE, self.bus)
        managed_objects_reply = om.call('GetManagedObjects')
        if managed_objects_reply.isValid():
             objects_dict = managed_objects_reply.arguments()[0]
             # Process initial devices
             for path, interfaces in objects_dict.items():
                 if DEVICE_IFACE in interfaces:
                      # Get initial props for devices
                      dev_props = qvariant_dict_to_python(interfaces.get(DEVICE_IFACE, {}))
                      self.process_device_properties(path, dev_props)
             # Check for initially active media player
             self.find_media_player(self.connected_device_path)
        else:
            print("BT Manager: Failed to get initial managed objects.")


        # Connect signals using ObjectManager (preferred over connecting for each device)
        self.bus.connect(BLUEZ_SERVICE, '/', DBUS_OM_IFACE, 'InterfacesAdded', self.on_interfaces_added)
        self.bus.connect(BLUEZ_SERVICE, '/', DBUS_OM_IFACE, 'InterfacesRemoved', self.on_interfaces_removed)

        # We still need PropertiesChanged for devices and media player.
        # Connecting for *every* device path might be too much.
        # Let's try connecting only when a device becomes connected? -> Risk missing updates before connect.
        # Alternative: Connect only for the *currently* connected device/player? -> Need to manage connections.

        # Let's connect to PropertiesChanged generically and filter by interface inside the slot.
        # NOTE: This might be less efficient if there are many BT devices/interfaces.
        # We will need to get the object path within the slot.
        # We need a QObject receiver for this type of connection to get sender info.
        self.dbus_receiver = QObject() # Create a QObject to connect signals to

        self.bus.connect(
            BLUEZ_SERVICE, '', DBUS_PROP_IFACE, 'PropertiesChanged', # Watch all paths
            self.on_device_properties_changed # Slot to handle Device1 changes
        )
        # Note: on_media_properties_changed is connected specifically when a player is found


        print("BT Manager: D-Bus signals connected. Entering wait loop.")
        while self._is_running:
            # Keep thread alive, D-Bus signals are processed by Qt's event loop
            self.msleep(1000) # Sleep for 1 second

        # Disconnect signals on exit
        print("BT Manager: Disconnecting D-Bus signals.")
        self.bus.disconnect(BLUEZ_SERVICE, '/', DBUS_OM_IFACE, 'InterfacesAdded', self.on_interfaces_added)
        self.bus.disconnect(BLUEZ_SERVICE, '/', DBUS_OM_IFACE, 'InterfacesRemoved', self.on_interfaces_removed)
        self.bus.disconnect(BLUEZ_SERVICE, '', DBUS_PROP_IFACE, 'PropertiesChanged', self.on_device_properties_changed)
        # Disconnect specific media player signal if active
        if self.media_player_path:
             self.bus.disconnect(BLUEZ_SERVICE, self.media_player_path, DBUS_PROP_IFACE, 'PropertiesChanged', self.on_media_properties_changed)

        print("BluetoothManager thread finished.")


    def stop(self):
        print("BluetoothManager: Stop requested.")
        self._is_running = False
