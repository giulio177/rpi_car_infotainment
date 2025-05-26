# backend/bluetooth_manager.py

import traceback
from PyQt6.QtCore import QThread, pyqtSignal, QVariant, QObject, pyqtSlot
from PyQt6.QtDBus import QDBusConnection, QDBusInterface, QDBusMessage, QDBusVariant

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
        self.dbus_receiver = QObject()  # Potentially needed if sender context required

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

    def process_device_properties(self, path, properties):
        """Checks device properties. Tries UPower for battery if BlueZ property is missing."""
        try:
            is_connected = properties.get("Connected", False)
            device_name = properties.get("Name", "Unknown Device")
            alias = properties.get("Alias", device_name)
            battery = properties.get("Battery", None)  # BlueZ property
            # print(f"DEBUG: process_device_properties - BlueZ Battery prop: {battery}")

            upower_battery = None
            if is_connected:
                upower_path = self._get_upower_device_path(path)
                if upower_path:
                    upower_battery = self._get_battery_from_upower(upower_path)

            # Use UPower battery if BlueZ one is None, otherwise prefer BlueZ
            final_battery = upower_battery if battery is None else battery
            print(
                f"DEBUG: process_device_properties - Final Battery for {alias}: {final_battery}"
            )

            if is_connected:
                battery_changed = final_battery != self.current_battery
                newly_connected = self.connected_device_path != path

                if newly_connected:
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
                elif battery_changed:
                    print(f"BT Manager: Battery updated for {alias} to {final_battery}")
                    self.current_battery = final_battery
                    print(f"DEBUG: Emitting battery_updated('{self.current_battery}')")
                    self.battery_updated.emit(self.current_battery)

            elif self.connected_device_path == path:  # Device disconnected
                print(f"BT Manager: Device disconnected - {alias} ({path})")
                if self.media_player_path and self.media_player_path.startswith(path):
                    if self.bus.isConnected():
                        self.bus.disconnect(
                            BLUEZ_SERVICE,
                            self.media_player_path,
                            DBUS_PROP_IFACE,
                            "PropertiesChanged",
                            self.on_media_properties_changed,
                        )
                    self.media_player_path = None

                self.connected_device_path = None
                self.connected_device_name = "Disconnected"
                self.current_battery = None
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

    # --- run Method (Polling Implementation) ---
    def run(self):
        print("BluetoothManager thread started.")
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
    def is_discoverable(self):
        """Check if the adapter is discoverable."""
        if not self.adapter_path or not self.bus.isConnected():
            return False

        try:
            adapter_iface = QDBusInterface(
                BLUEZ_SERVICE, self.adapter_path, ADAPTER_IFACE, self.bus
            )
            reply = adapter_iface.call("GetAll", ADAPTER_IFACE)
            if reply.type() == QDBusMessage.MessageType.ErrorMessage:
                return False

            properties = qvariant_dict_to_python(reply.arguments()[0])
            return properties.get("Discoverable", False)

        except Exception as e:
            print(f"Error checking discoverability: {e}")
            return False

    def set_discoverable(self, discoverable):
        """Set adapter discoverability."""
        if not self.adapter_path or not self.bus.isConnected():
            return False

        try:
            adapter_iface = QDBusInterface(
                BLUEZ_SERVICE, self.adapter_path, ADAPTER_IFACE, self.bus
            )
            reply = adapter_iface.call("Set", ADAPTER_IFACE, "Discoverable", QDBusVariant(discoverable))
            return reply.type() != QDBusMessage.MessageType.ErrorMessage

        except Exception as e:
            print(f"Error setting discoverability: {e}")
            return False

    def set_pairable(self, pairable):
        """Set adapter pairability."""
        if not self.adapter_path or not self.bus.isConnected():
            return False

        try:
            adapter_iface = QDBusInterface(
                BLUEZ_SERVICE, self.adapter_path, ADAPTER_IFACE, self.bus
            )
            reply = adapter_iface.call("Set", ADAPTER_IFACE, "Pairable", QDBusVariant(pairable))
            return reply.type() != QDBusMessage.MessageType.ErrorMessage

        except Exception as e:
            print(f"Error setting pairability: {e}")
            return False

    def send_stop(self):
        return self._send_media_command("Stop")
