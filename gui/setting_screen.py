# gui/setting_screen.py

import subprocess
import threading # Importato per le operazioni in background
import psutil
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QLineEdit,
    QFormLayout,
    QGroupBox,
    QSpacerItem,
    QSizePolicy,
    QScrollArea,
    QCheckBox,
)
from PyQt6.QtCore import QTimer, QDateTime, pyqtSlot, Qt, pyqtSignal
from .symbol_manager import symbol_manager

from .styling import scale_value


class SettingsScreen(QWidget):
    screen_title = "Settings"

    info_updated = pyqtSignal(dict)

    def __init__(self, settings_manager, main_window_ref, parent=None):
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.main_window = main_window_ref

        # --- Base sizes ---
        self.base_margin = 10
        self.base_spacing = 15
        self.base_scroll_content_spacing = 10
        self.base_form_h_spacing = 8
        self.base_form_v_spacing = 8
        self.base_button_layout_spacing = 10

        # --- Main Layout ---
        self.main_layout = QVBoxLayout(self)
        # Margins/Spacing set by update_scaling

        # --- SCROLL AREA SETUP ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("settingsScrollArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        self.scroll_content_widget = QWidget()
        self.scroll_content_widget.setObjectName("settingsScrollContent")
        self.scroll_layout = QVBoxLayout(self.scroll_content_widget)
        # Spacing set by update_scaling

        # ## NUOVO: Raspberry Pi Info Group (stabile) ##
        self.pi_info_group = QGroupBox("Raspberry Pi Info")
        self.pi_info_group.setObjectName("settingsPiInfoGroup")
        self.pi_info_layout = QFormLayout()
        self.pi_info_group.setLayout(self.pi_info_layout)

        # Etichette per le informazioni
        self.cpu_temp_label = QLabel("Loading...")
        self.cpu_usage_label = QLabel("Loading...")
        self.ram_usage_label = QLabel("Loading...")
        self.uptime_label = QLabel("Loading...")

        self.pi_info_layout.addRow("CPU Temperature:", self.cpu_temp_label)
        self.pi_info_layout.addRow("CPU Usage:", self.cpu_usage_label)
        self.pi_info_layout.addRow("RAM Usage:", self.ram_usage_label)
        self.pi_info_layout.addRow("System Uptime:", self.uptime_label)
        
        # Aggiunto il nuovo gruppo al layout dello scroll
        self.scroll_layout.addWidget(self.pi_info_group)

        # --- General Settings Group ---
        self.general_group = QGroupBox("General")
        self.general_group.setObjectName("settingsGeneralGroup")
        self.general_layout = QFormLayout()
        # Spacing set by update_scaling
        self.general_group.setLayout(self.general_layout)

        self.theme_combo = QComboBox()
        self.theme_combo.setObjectName("themeCombo")
        self.theme_combo.addItems(["light", "dark"])
        self.theme_combo.setCurrentText(self.settings_manager.get("theme"))
        self.general_layout.addRow("UI Theme:", self.theme_combo)

        # --- Resolution Setting ---
        self.resolution_combo = QComboBox()
        self.resolution_combo.setObjectName("resolutionCombo")
        self.resolution_combo.addItems(["1024x600", "1280x720", "1920x1080"])
        current_res = self.settings_manager.get("window_resolution")
        current_res_str = (
            f"{current_res[0]}x{current_res[1]}" if current_res else "1024x600"
        )
        self.resolution_combo.setCurrentText(current_res_str)
        self.general_layout.addRow("Resolution:", self.resolution_combo)

        # --- UI Scale Mode Setting ---
        self.ui_scale_combo = QComboBox()
        self.ui_scale_combo.setObjectName("uiScaleCombo")
        self.ui_scale_combo.addItems(
            [
                "Auto (Scale with Resolution)",
                "Small UI (Fixed Style)",
                "Medium UI (Fixed Style)",
                "Large UI (Fixed Style)",
            ]
        )

        # Map the stored value to the display text
        scale_mode_map = {
            "auto": "Auto (Scale with Resolution)",
            "fixed_small": "Small UI (Fixed Style)",
            "fixed_medium": "Medium UI (Fixed Style)",
            "fixed_large": "Large UI (Fixed Style)",
        }
        current_scale_mode = self.settings_manager.get("ui_scale_mode")
        if current_scale_mode in scale_mode_map:
            self.ui_scale_combo.setCurrentText(scale_mode_map[current_scale_mode])

        self.general_layout.addRow("UI Scale Mode:", self.ui_scale_combo)

        # --- Cursor Visibility Setting ---
        self.cursor_checkbox = QCheckBox("Show Cursor")
        self.cursor_checkbox.setObjectName("cursorCheckbox")
        self.cursor_checkbox.setChecked(self.settings_manager.get("show_cursor"))
        self.general_layout.addRow(self.cursor_checkbox)

        # --- Bottom-Right Corner Setting ---
        self.position_checkbox = QCheckBox("Fix Bottom-Right Corner")
        self.position_checkbox.setObjectName("positionCheckbox")
        self.position_checkbox.setChecked(
            self.settings_manager.get("position_bottom_right")
        )
        self.general_layout.addRow(self.position_checkbox)

        # --- Developer Mode Setting ---
        self.developer_mode_checkbox = QCheckBox("Developer Mode (Testing Features)")
        self.developer_mode_checkbox.setObjectName("developerModeCheckbox")
        self.developer_mode_checkbox.setChecked(
            self.settings_manager.get("developer_mode")
        )
        self.general_layout.addRow(self.developer_mode_checkbox)

        self.scroll_layout.addWidget(self.general_group)  # Add group to scroll area

        # --- OBD Settings Group ---
        self.obd_group = QGroupBox("OBD-II")
        self.obd_group.setObjectName("settingsObdGroup")
        self.obd_layout = QFormLayout()
        # Spacing set by update_scaling
        self.obd_group.setLayout(self.obd_layout)
        # --- OBD Enable Checkbox ---
        self.obd_enable_checkbox = QCheckBox("Enable OBD Features")
        self.obd_enable_checkbox.setObjectName("obdEnableCheckbox")
        self.obd_enable_checkbox.setChecked(self.settings_manager.get("obd_enabled"))
        # Add checkbox spanning both columns for prominence
        self.obd_layout.addRow(self.obd_enable_checkbox)
        # --- OBD Port/Baud setup ---
        self.obd_port_edit = QLineEdit()
        self.obd_port_edit.setObjectName("obdPortEdit")
        self.obd_port_edit.setPlaceholderText(
            "e.g., /dev/rfcomm0 or /dev/ttyUSB0 (leave blank for auto)"
        )
        self.obd_port_edit.setText(self.settings_manager.get("obd_port") or "")
        self.obd_layout.addRow("OBD Port:", self.obd_port_edit)

        self.obd_baud_edit = QLineEdit()
        self.obd_baud_edit.setObjectName("obdBaudEdit")
        self.obd_baud_edit.setPlaceholderText("e.g., 38400 (leave blank for auto)")
        obd_baud = self.settings_manager.get("obd_baudrate")
        self.obd_baud_edit.setText(str(obd_baud) if obd_baud else "")
        self.obd_layout.addRow("Baudrate:", self.obd_baud_edit)
        # ---
        self.scroll_layout.addWidget(self.obd_group)  # Add group to scroll area

        # --- Radio Settings Group ---
        self.radio_group = QGroupBox("Radio")
        self.radio_group.setObjectName("settingsRadioGroup")
        self.radio_layout = QFormLayout()
        # Spacing set by update_scaling
        self.radio_group.setLayout(self.radio_layout)
        # --- Radio Enable Checkbox ---
        self.radio_enable_checkbox = QCheckBox("Enable Radio Features")
        self.radio_enable_checkbox.setObjectName("radioEnableCheckbox")
        self.radio_enable_checkbox.setChecked(
            self.settings_manager.get("radio_enabled")
        )
        # Add checkbox spanning both columns
        self.radio_layout.addRow(self.radio_enable_checkbox)
        # --- Radio Type/Address setup ---
        self.radio_type_combo = QComboBox()
        self.radio_type_combo.setObjectName("radioTypeCombo")
        self.radio_type_combo.addItems(["none", "sdr", "si4703", "si4735"])
        self.radio_type_combo.setCurrentText(self.settings_manager.get("radio_type"))
        self.radio_layout.addRow("Radio Type:", self.radio_type_combo)

        self.radio_i2c_addr_edit = QLineEdit()
        self.radio_i2c_addr_edit.setObjectName("radioI2cAddrEdit")
        self.radio_i2c_addr_edit.setPlaceholderText("e.g., 0x10 (for I2C type)")
        i2c_addr = self.settings_manager.get("radio_i2c_address")
        self.radio_i2c_addr_edit.setText(hex(i2c_addr) if i2c_addr is not None else "")
        self.radio_layout.addRow("I2C Address:", self.radio_i2c_addr_edit)
        # ---
        self.scroll_layout.addWidget(self.radio_group)  # Add group to scroll area

        # --- Floating Icon Buttons (positioned absolutely, not taking scroll space) ---
        # Create compact square icon buttons that will float over the content
        self.save_button = QPushButton()
        self.save_button.setObjectName("tinyFloatingButton")  # Special object name for styling
        self.save_button.clicked.connect(self.apply_settings)
        self.save_button.setFixedSize(50, 50)  # Slightly bigger square
        self.save_button.setMinimumSize(50, 50)  # Override global minimum
        self.save_button.setMaximumSize(50, 50)  # Force exact size

        # Setup symbols using centralized symbol manager
        symbol_manager.setup_button_symbol(self.save_button, "save", 20)
        self.save_button.setToolTip("Apply Settings")
        self.save_button.setParent(self.scroll_area)  # Parent to scroll area for positioning

        self.restart_button = QPushButton()
        self.restart_button.setObjectName("tinyFloatingButton")  # Special object name for styling
        self.restart_button.clicked.connect(self.apply_and_restart)
        self.restart_button.setFixedSize(50, 50)  # Slightly bigger square
        self.restart_button.setMinimumSize(50, 50)  # Override global minimum
        self.restart_button.setMaximumSize(50, 50)  # Force exact size
        symbol_manager.setup_button_symbol(self.restart_button, "restart", 20)
        self.restart_button.setToolTip("Apply Settings and Restart")
        self.restart_button.setParent(self.scroll_area)  # Parent to scroll area for positioning

        # Add stretch at the end of the scroll content to push everything up
        self.scroll_layout.addStretch(1)

        # Set the content widget for the scroll area
        self.scroll_area.setWidget(self.scroll_content_widget)

        # Add scroll area to the main layout with maximum stretch to occupy most space
        self.main_layout.addWidget(self.scroll_area, 1)

        # Position the floating buttons (will be called after the widget is shown)
        QTimer.singleShot(100, self._position_floating_buttons)

        # ## MODIFICATO: Collegamento del segnale e avvio del timer stabile ##
        self.info_updated.connect(self.update_info_labels)
        self.info_update_timer = QTimer(self)
        self.info_update_timer.timeout.connect(self.start_info_update_thread)
        self.info_update_timer.start(10000) # Aggiorna ogni 10 secondi per ridurre il carico
        self.start_info_update_thread() # Chiamata iniziale

    def _position_floating_buttons(self):
        """Position the floating buttons in the top-right corner of the scroll area, avoiding the scrollbar."""
        try:
            # Debug: Print all available fonts using static method
            available_families = QFontDatabase.families()

            print("=== Available Font Families ===")
            emoji_related = [f for f in available_families if any(keyword in f.lower() for keyword in ['emoji', 'symbol', 'noto'])]
            if emoji_related:
                print("Emoji/Symbol fonts found:")
                for font in emoji_related:
                    print(f"  - {font}")
            else:
                print("No emoji fonts found in system")

            # List of emoji fonts to try (in order of preference)
            emoji_fonts = [
                "Noto Color Emoji",
                "Noto Emoji",
                "Apple Color Emoji",
                "Segoe UI Emoji",
                "EmojiOne",
                "Symbola",
                "DejaVu Sans"
            ]

            emoji_font = None
            for font_name in emoji_fonts:
                if font_name in available_families:
                    emoji_font = QFont(font_name, 20)  # 20pt for good visibility
                    print(f"Using font: {font_name}")
                    break

            if emoji_font is None:
                # Fallback: use a standard font with larger size
                emoji_font = QFont("Arial", 18)
                print("Using Arial fallback font")

            # Apply the font to both buttons
            if hasattr(self, 'save_button'):
                self.save_button.setFont(emoji_font)
            if hasattr(self, 'restart_button'):
                self.restart_button.setFont(emoji_font)

        except Exception as e:
            print(f"Error setting up button fonts: {e}")
            # Simple fallback without font detection
            fallback_font = QFont("Arial", 18)
            if hasattr(self, 'save_button'):
                self.save_button.setFont(fallback_font)
            if hasattr(self, 'restart_button'):
                self.restart_button.setFont(fallback_font)

    def _set_button_symbol(self, button, symbol_type):
        """Set button symbol with fallback options."""
        # Check if we have emoji fonts available
        available_families = QFontDatabase.families()
        has_emoji_fonts = any(font in available_families for font in ["Noto Color Emoji", "Noto Emoji"])

        if has_emoji_fonts:
            # Use emoji if available
            symbols = {
                "save": "�",     # Floppy disk emoji
                "restart": "🔄",  # Refresh emoji
                "success": "✅",  # Green checkmark emoji
                "none": "➖"      # Minus emoji
            }
        else:
            # Use Unicode symbols that render reliably
            symbols = {
                "save": "⬇",      # Down arrow (save/download)
                "restart": "↻",   # Refresh symbol
                "success": "✓",   # Checkmark
                "none": "−"       # Minus sign
            }

        if symbol_type in symbols:
            button.setText(symbols[symbol_type])
            print(f"Set {symbol_type} button to: {symbols[symbol_type]}")
            button.update()

    def _position_floating_buttons(self):
        """Position the floating buttons in the top-right corner of the scroll area, avoiding the scrollbar."""
        if not self.scroll_area or not self.save_button or not self.restart_button:
            return

        # Get scroll area dimensions
        scroll_width = self.scroll_area.width()
        scroll_height = self.scroll_area.height()

        # Position buttons in top-right corner with margin to avoid scrollbar
        margin = 10
        scrollbar_width = 20  # Approximate scrollbar width
        button_spacing = 5

        # Position restart button (rightmost, but left of scrollbar)
        restart_x = scroll_width - self.restart_button.width() - margin - scrollbar_width
        restart_y = margin
        self.restart_button.move(restart_x, restart_y)

        # Position save button (left of restart button)
        save_x = restart_x - self.save_button.width() - button_spacing
        save_y = margin
        self.save_button.move(save_x, save_y)

        # Ensure buttons are visible and on top
        self.save_button.raise_()
        self.restart_button.raise_()
        self.save_button.show()
        self.restart_button.show()

    def resizeEvent(self, event):
        """Handle resize events to reposition floating buttons."""
        super().resizeEvent(event)
        # Reposition buttons when the widget is resized
        QTimer.singleShot(10, self._position_floating_buttons)

    def showEvent(self, event):
        """Handle show events to position floating buttons."""
        super().showEvent(event)
        # Position buttons when the widget is shown
        QTimer.singleShot(50, self._position_floating_buttons)

    # ## NUOVO: Funzione per avviare il thread ##
    def start_info_update_thread(self):
        """Starts a background thread to fetch system info non-blockingly."""
        update_thread = threading.Thread(target=self._get_system_info_worker)
        update_thread.daemon = True # Il thread si chiuderà con l'app
        update_thread.start()

    # ## NUOVO: Funzione "Worker" che viene eseguita nel thread ##
    def _get_system_info_worker(self):
        """Fetches system info in a background thread and emits a signal."""
        info = {}
        try:
            # Temperatura
            temp_cmd = "awk '{printf \"%.1f°C\", $1/1000}' /sys/class/thermal/thermal_zone0/temp"
            info['temp'] = subprocess.check_output(temp_cmd, shell=True, text=True).strip()
        except Exception:
            info['temp'] = "N/A"
        
        try:
            # Utilizzo CPU (più affidabile con psutil)
            cpu_percent = psutil.cpu_percent(interval=1)
            info['cpu'] = f"{cpu_percent}%"
        except Exception:
            info['cpu'] = "N/A"
            
        try:
            # Utilizzo RAM
            ram_cmd = "free -m | grep Mem | awk '{print $3\" MB / \"$2\" MB\"}'"
            info['ram'] = subprocess.check_output(ram_cmd, shell=True, text=True).strip()
        except Exception:
            info['ram'] = "N/A"
            
        try:
            # Uptime
            uptime_cmd = ["uptime", "-p"]
            result = subprocess.run(uptime_cmd, capture_output=True, text=True)
            info['uptime'] = result.stdout.strip().replace("up ", "")
        except Exception:
            info['uptime'] = "N/A"
        
        # Emette il segnale con i dati raccolti
        self.info_updated.emit(info)

    # ## NUOVO: Slot per aggiornare la UI in modo sicuro ##
    @pyqtSlot(dict)
    def update_info_labels(self, info):
        """Updates the UI labels with data from the background thread."""
        self.cpu_temp_label.setText(info.get('temp', 'Error'))
        self.cpu_usage_label.setText(info.get('cpu', 'Error'))
        self.ram_usage_label.setText(info.get('ram', 'Error'))
        self.uptime_label.setText(info.get('uptime', 'Error'))


    def update_scaling(self, scale_factor, scaled_main_margin):
        """Applies scaling to internal layouts."""
        scaled_spacing = scale_value(self.base_spacing, scale_factor)
        scaled_scroll_content_spacing = scale_value(
            self.base_scroll_content_spacing, scale_factor
        )
        scaled_form_h_spacing = scale_value(self.base_form_h_spacing, scale_factor)
        scaled_form_v_spacing = scale_value(self.base_form_v_spacing, scale_factor)
        scaled_button_layout_spacing = scale_value(
            self.base_button_layout_spacing, scale_factor
        )

        # Apply to MAIN layouts
        self.main_layout.setContentsMargins(
            scaled_main_margin,
            scaled_main_margin,
            scaled_main_margin,
            scaled_main_margin,
        )
        self.main_layout.setSpacing(scaled_spacing)

        # Reposition floating buttons after scaling changes
        QTimer.singleShot(50, self._position_floating_buttons)

        # Apply to the layout INSIDE the scroll area
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(scaled_scroll_content_spacing)

        # Apply spacing to form layouts
        self.general_layout.setHorizontalSpacing(scaled_form_h_spacing)
        self.general_layout.setVerticalSpacing(scaled_form_v_spacing)
        self.obd_layout.setHorizontalSpacing(scaled_form_h_spacing)
        self.obd_layout.setVerticalSpacing(scaled_form_v_spacing)
        self.radio_layout.setHorizontalSpacing(scaled_form_h_spacing)
        self.radio_layout.setVerticalSpacing(scaled_form_v_spacing)

        # REMOVED scaling for resolution_layout as it no longer exists

    def apply_settings(self, show_feedback=True):
        """Apply and save all settings. Returns True if a restart-requiring change was made."""
        print("Applying settings...")
        settings_changed = False
        restart_required = False  # Assume no restart needed unless resolution changes (which it can't now)

        # Apply General Settings
        new_theme = self.theme_combo.currentText()
        if new_theme != self.settings_manager.get("theme"):
            if self.main_window is not None and hasattr(
                self.main_window, "switch_theme"
            ):
                self.main_window.switch_theme(new_theme)
                settings_changed = True

        # Resolution Setting Logic
        selected_res_str = self.resolution_combo.currentText()
        try:
            width, height = map(int, selected_res_str.split("x"))
            new_resolution = [width, height]
            if new_resolution != self.settings_manager.get("window_resolution"):
                self.settings_manager.set("window_resolution", new_resolution)
                settings_changed = True
                restart_required = True
        except Exception as e:
            print(f"Error parsing resolution: {e}")

        # Cursor Visibility Setting
        new_show_cursor = self.cursor_checkbox.isChecked()
        if new_show_cursor != self.settings_manager.get("show_cursor"):
            self.settings_manager.set("show_cursor", new_show_cursor)
            settings_changed = True
            restart_required = True

        # Bottom-Right Corner Setting
        new_position_bottom_right = self.position_checkbox.isChecked()
        if new_position_bottom_right != self.settings_manager.get(
            "position_bottom_right"
        ):
            self.settings_manager.set(
                "position_bottom_right", new_position_bottom_right
            )
            settings_changed = True
            restart_required = True

        # UI Scale Mode Setting
        scale_mode_display = self.ui_scale_combo.currentText()
        # Reverse map from display text to stored value
        reverse_scale_map = {
            "Auto (Scale with Resolution)": "auto",
            "Small UI (Fixed Style)": "fixed_small",
            "Medium UI (Fixed Style)": "fixed_medium",
            "Large UI (Fixed Style)": "fixed_large",
        }

        if scale_mode_display in reverse_scale_map:
            new_scale_mode = reverse_scale_map[scale_mode_display]
            if new_scale_mode != self.settings_manager.get("ui_scale_mode"):
                self.settings_manager.set("ui_scale_mode", new_scale_mode)
                settings_changed = True
                restart_required = True

        # Developer Mode Setting
        new_developer_mode = self.developer_mode_checkbox.isChecked()
        if new_developer_mode != self.settings_manager.get("developer_mode"):
            self.settings_manager.set("developer_mode", new_developer_mode)
            settings_changed = True
            restart_required = True

        # Apply OBD Settings
        new_obd_enabled = self.obd_enable_checkbox.isChecked()
        if new_obd_enabled != self.settings_manager.get("obd_enabled"):
            print(f"OBD Enabled state changed to: {new_obd_enabled}")
            self.settings_manager.set("obd_enabled", new_obd_enabled)
            settings_changed = True
            # Notify MainWindow to start/stop the manager
            if self.main_window and hasattr(self.main_window, "toggle_obd_manager"):
                self.main_window.toggle_obd_manager(new_obd_enabled)
            else:
                print(
                    "ERROR: Cannot toggle OBD manager - MainWindow reference invalid."
                )
        obd_port = self.obd_port_edit.text().strip() or None
        obd_baud_str = self.obd_baud_edit.text().strip()
        obd_baud = None
        try:
            if obd_baud_str:
                obd_baud = int(obd_baud_str)
        except ValueError:
            pass
        obd_conn_changed = (
            self.settings_manager.get("obd_port") != obd_port
            or self.settings_manager.get("obd_baudrate") != obd_baud
        )
        if obd_conn_changed:
            self.settings_manager.set("obd_port", obd_port)
            self.settings_manager.set("obd_baudrate", obd_baud)
            settings_changed = True
            # Notify MainWindow ONLY if OBD is currently enabled
            if self.settings_manager.get("obd_enabled"):
                if self.main_window and hasattr(self.main_window, "update_obd_config"):
                    self.main_window.update_obd_config()
                else:
                    print(
                        "Warning: Could not update OBD config - main window reference invalid."
                    )
            else:
                print("OBD connection settings saved, but OBD is disabled.")

        # Apply Radio Settings
        new_radio_enabled = self.radio_enable_checkbox.isChecked()
        if new_radio_enabled != self.settings_manager.get("radio_enabled"):
            print(f"Radio Enabled state changed to: {new_radio_enabled}")
            self.settings_manager.set("radio_enabled", new_radio_enabled)
            settings_changed = True
            # Notify MainWindow to start/stop the manager
            if self.main_window and hasattr(self.main_window, "toggle_radio_manager"):
                self.main_window.toggle_radio_manager(new_radio_enabled)
            else:
                print(
                    "ERROR: Cannot toggle Radio manager - MainWindow reference invalid."
                )
        radio_type = self.radio_type_combo.currentText()
        i2c_addr_str = self.radio_i2c_addr_edit.text().strip()
        i2c_addr = None
        try:
            if i2c_addr_str:
                i2c_addr = int(i2c_addr_str, 0)
        except ValueError:
            pass
        radio_conn_changed = (
            self.settings_manager.get("radio_type") != radio_type
            or self.settings_manager.get("radio_i2c_address") != i2c_addr
        )
        if radio_conn_changed:
            self.settings_manager.set("radio_type", radio_type)
            self.settings_manager.set("radio_i2c_address", i2c_addr)
            settings_changed = True
            # Notify MainWindow ONLY if Radio is currently enabled
            if self.settings_manager.get("radio_enabled"):
                if self.main_window and hasattr(
                    self.main_window, "update_radio_config"
                ):
                    self.main_window.update_radio_config()
                else:
                    print(
                        "Warning: Could not update Radio config - main window reference invalid."
                    )
            else:
                print("Radio connection settings saved, but Radio is disabled.")

        # Feedback logic
        if show_feedback:
            if settings_changed:
                status_message = "Settings applied."
                if restart_required:
                    status_message += (
                        " Restart required for resolution, cursor, or position changes."
                    )
                print(status_message)
                # Change symbols to show success
                symbol_manager.update_button_symbol(self.save_button, "success")
                symbol_manager.update_button_symbol(self.restart_button, "success")
                self.save_button.setEnabled(False)
                self.restart_button.setEnabled(False)
                QTimer.singleShot(
                    2000,
                    lambda: (
                        symbol_manager.update_button_symbol(self.save_button, "save"),
                        symbol_manager.update_button_symbol(self.restart_button, "restart"),
                        self.save_button.setEnabled(True),
                        self.restart_button.setEnabled(True),
                    ),
                )
            else:
                print("Settings applied (No changes detected).")
                # Change symbols to show no changes
                symbol_manager.update_button_symbol(self.save_button, "none")
                symbol_manager.update_button_symbol(self.restart_button, "none")
                self.save_button.setEnabled(False)
                self.restart_button.setEnabled(False)
                QTimer.singleShot(
                    1500,
                    lambda: (
                        symbol_manager.update_button_symbol(self.save_button, "save"),
                        symbol_manager.update_button_symbol(self.restart_button, "restart"),
                        self.save_button.setEnabled(True),
                        self.restart_button.setEnabled(True),
                    ),
                )

        return restart_required

    def apply_and_restart(self):
        """Applies settings and then initiates the application restart sequence."""
        print("Apply and Restart requested.")
        # Apply settings first (suppress the normal feedback message)
        self.apply_settings(show_feedback=False)
        # Trigger restart (always happens now, even if no settings changed)
        if self.main_window and hasattr(self.main_window, "restart_application"):
            self.main_window.restart_application()
        else:
            print(
                "ERROR: Cannot restart. MainWindow reference is invalid or missing 'restart_application' method."
            )

    # AirPlay info popup method moved to AirPlay screen
