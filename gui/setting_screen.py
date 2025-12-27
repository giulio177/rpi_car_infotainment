# gui/setting_screen.py

import socket # <--- AGGIUNGI QUESTO
import os     # <--- AGGIUNGI QUESTO
import subprocess
import threading # Importato per le operazioni in background
import psutil
import time
from PyQt6.QtWidgets import (
    QWidget,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QLineEdit,
    QListWidget,
    QFormLayout,
    QGroupBox,
    QSpacerItem,
    QSizePolicy,
    QScrollArea,
    QCheckBox,
    QAbstractItemView, # <--- Aggiungi questo
    QScroller,
    QMessageBox,
    QGroupBox, 
    QFormLayout,
)
try:
    from gpiozero import OutputDevice
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("GPIO library not found. GPIO features will be disabled.")
from PyQt6.QtCore import QTimer, QDateTime, pyqtSlot, Qt, pyqtSignal

from .styling import scale_value

class TouchComboBox(QComboBox):
    """
    Un QComboBox ottimizzato per touchscreen:
    - Elementi della lista più grandi.
    - Scorrimento cinetico all'interno della lista.
    - Forza l'apertura del popup al tocco (ignora il jitter).
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(40)  # Altezza minima per facilitare il tocco
        
        # Stile CSS per ingrandire il menu a tendina e gli elementi interni
        self.setStyleSheet("""
            QComboBox::drop-down {
                width: 40px;
                border-left: 1px solid gray;
            }
            QComboBox QAbstractItemView {
                min-height: 40px;
                border: 1px solid gray;
            }
            QComboBox QAbstractItemView::item {
                min-height: 40px; /* Altezza righe menu */
                padding: 5px;
            }
        """)

        # Abilita lo scorrimento cinetico (smartphone style) dentro la tendina
        self.view().setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        QScroller.grabGesture(self.view().viewport(), QScroller.ScrollerGestureType.TouchGesture)

    def showPopup(self):
        super().showPopup()
        # Opzionale: qui potresti forzare dimensioni specifiche del popup se necessario
        
    def mousePressEvent(self, e):
        # Accetta subito l'evento per evitare che la QScrollArea padre lo rubi
        super().mousePressEvent(e)
        e.accept()
    
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
        QScroller.grabGesture(self.scroll_area.viewport(), QScroller.ScrollerGestureType.TouchGesture)

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

        self.theme_combo = TouchComboBox()
        self.theme_combo.setObjectName("themeCombo")
        self.theme_combo.addItems(["light", "dark"])
        self.theme_combo.setCurrentText(self.settings_manager.get("theme"))
        self.general_layout.addRow("UI Theme:", self.theme_combo)

        # --- UI Render Mode ---
        self.render_mode_combo = TouchComboBox()
        self.render_mode_combo.setObjectName("renderModeCombo")
        self.render_mode_combo.addItem("Native Widgets (Qt)", "native")
        try:
            from .html_renderer import HtmlView  # noqa: F401
            self.html_ui_available = True
        except Exception:
            self.html_ui_available = False
        self.render_mode_combo.addItem("Embedded HTML (WebEngine)", "html")
        html_index = self.render_mode_combo.findData("html")
        if html_index != -1 and not self.html_ui_available:
            item = self.render_mode_combo.model().item(html_index)
            if item is not None:
                item.setEnabled(False)
            self.render_mode_combo.setItemData(
                html_index,
                "Install PyQt6-WebEngine to enable this mode.",
                Qt.ItemDataRole.ToolTipRole,
            )
        current_render_mode = self.settings_manager.get("ui_render_mode") or "native"
        current_mode_index = self.render_mode_combo.findData(current_render_mode)
        if current_mode_index != -1:
            self.render_mode_combo.setCurrentIndex(current_mode_index)
        else:
            self.render_mode_combo.setCurrentIndex(
                self.render_mode_combo.findData("native")
            )
        self.general_layout.addRow("UI Render Mode:", self.render_mode_combo)
        if not self.html_ui_available:
            self.render_mode_hint = QLabel(
                "HTML mode requires PyQt6-WebEngine. Install it to enable this option."
            )
            self.render_mode_hint.setObjectName("renderModeHint")
            self.render_mode_hint.setWordWrap(True)
            self.render_mode_hint.setStyleSheet("color: #ffb5b5;")
            self.general_layout.addRow("", self.render_mode_hint)

        # --- Resolution Setting ---
        self.resolution_combo = TouchComboBox()
        self.resolution_combo.setObjectName("resolutionCombo")
        self.resolution_combo.addItems(["1024x600", "1280x720", "1920x1080"])
        current_res = self.settings_manager.get("window_resolution")
        current_res_str = (
            f"{current_res[0]}x{current_res[1]}" if current_res else "1024x600"
        )
        self.resolution_combo.setCurrentText(current_res_str)
        self.general_layout.addRow("Resolution:", self.resolution_combo)

        # --- UI Scale Mode Setting ---
        self.ui_scale_combo = TouchComboBox()
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
        self.obd_port_edit.mousePressEvent = lambda event: self.show_keyboard(self.obd_port_edit)
        self.obd_port_edit.setText(self.settings_manager.get("obd_port") or "")
        self.obd_layout.addRow("OBD Port:", self.obd_port_edit)

        self.obd_baud_edit = QLineEdit()
        self.obd_baud_edit.setObjectName("obdBaudEdit")
        self.obd_baud_edit.setPlaceholderText("e.g., 38400 (leave blank for auto)")
        self.obd_baud_edit.mousePressEvent = lambda event: self.show_keyboard(self.obd_baud_edit)
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
        self.radio_i2c_addr_edit.mousePressEvent = lambda event: self.show_keyboard(self.radio_i2c_addr_edit)
        i2c_addr = self.settings_manager.get("radio_i2c_address")
        self.radio_i2c_addr_edit.setText(hex(i2c_addr) if i2c_addr is not None else "")
        self.radio_layout.addRow("I2C Address:", self.radio_i2c_addr_edit)
        # ---
        self.scroll_layout.addWidget(self.radio_group)  # Add group to scroll area
        
        # --- POWER CONTROL GROUP (GPIO) ---
        self.power_group = QGroupBox("Power Management (GPIO)")
        self.power_group.setObjectName("settingsPowerGroup")
        self.power_layout = QVBoxLayout() # Usiamo Vertical per impilarli
        self.power_group.setLayout(self.power_layout)

        # 1. Configurazione Pin
        self.power_pin_number = 17  # <--- CAMBIA QUESTO NUMERO SE NECESSARIO
        self.power_device = None

        # 2. Checkbox "Abilita Keep-Alive"
        # Se attivato: Pin va HIGH. Se disattivato: Pin va LOW.
        self.power_toggle = QCheckBox(f"Enable Keep-Alive (GPIO {self.power_pin_number})")
        is_power_enabled = self.settings_manager.get("power_control_enabled") or False
        self.power_toggle.setChecked(is_power_enabled)
        
        # 3. Pulsante "Spegni Tutto"
        self.power_off_button = QPushButton("SHUTDOWN (Cut Power)")
        self.power_off_button.setMinimumHeight(50)
        self.power_off_button.setStyleSheet("background-color: #ff5555; color: white; font-weight: bold;")
        self.power_off_button.setEnabled(is_power_enabled) # Attivo solo se la funzione è abilitata

        # 4. Inizializzazione Hardware
        if GPIO_AVAILABLE:
            try:
                # Inizializziamo il pin. 
                # Se la spunta era attiva salvata nelle settings, partiamo subito HIGH.
                # Altrimenti partiamo LOW.
                initial_state = is_power_enabled
                self.power_device = OutputDevice(self.power_pin_number, active_high=True, initial_value=initial_state)
            except Exception as e:
                print(f"GPIO Error: {e}")
                self.power_toggle.setEnabled(False)
                self.power_toggle.setText("GPIO Error")

        # 5. Collegamento Segnali
        self.power_toggle.toggled.connect(self.on_power_toggle_changed)
        self.power_off_button.clicked.connect(self.perform_hardware_shutdown)

        # Aggiunta al layout
        self.power_layout.addWidget(self.power_toggle)
        self.power_layout.addWidget(self.power_off_button)
        
        self.scroll_layout.addWidget(self.power_group)

        
        
        # --- UPDATE SECTION (Software Update) ---
        self.update_group = QGroupBox("Software Update")
        self.update_group.setObjectName("settingsUpdateGroup")
        self.update_layout = QVBoxLayout()
        self.update_group.setLayout(self.update_layout)

        self.update_info_label = QLabel("Current Version: Main Branch")
        self.update_info_label.setStyleSheet("color: gray; font-size: 12px;")
        self.update_layout.addWidget(self.update_info_label)

        self.check_update_button = QPushButton("Check & Update from GitHub")
        self.check_update_button.setMinimumHeight(45) # Bello grande per il touch
        self.check_update_button.clicked.connect(self.perform_app_update)
        self.update_layout.addWidget(self.check_update_button)

        self.scroll_layout.addWidget(self.update_group)

        # Add stretch at the end of the scroll content
        self.scroll_layout.addStretch(1)
        # Set the content widget for the scroll area
        self.scroll_area.setWidget(self.scroll_content_widget)
        # Add scroll area to the main layout
        self.main_layout.addWidget(self.scroll_area, 1)

        # AirPlay info button moved to AirPlay screen settings section

        # --- Button Layout ---
        self.button_layout = QHBoxLayout()
        # Spacing set by update_scaling
        self.save_button = QPushButton("Apply Settings")
        self.save_button.setObjectName("settingsSaveButton")
        self.save_button.clicked.connect(self.apply_settings)
        self.restart_button = QPushButton("Apply and Restart")
        self.restart_button.setObjectName("settingsRestartButton")
        self.restart_button.clicked.connect(self.apply_and_restart)
        self.button_layout.addStretch(1)
        self.button_layout.addWidget(self.save_button)
        self.button_layout.addWidget(self.restart_button)
        self.button_layout.addStretch(1)
        self.main_layout.addLayout(self.button_layout)

        # ## MODIFICATO: Collegamento del segnale e avvio del timer stabile ##
        self.info_updated.connect(self.update_info_labels)
        self.info_update_timer = QTimer(self)
        self.info_update_timer.timeout.connect(self.start_info_update_thread)
        self.info_update_timer.start(10000) # Aggiorna ogni 10 secondi per ridurre il carico
        self.start_info_update_thread() # Chiamata iniziale

    def check_internet_connection(self):
        """Tenta di connettersi a GitHub per verificare l'internet."""
        try:
            # Prova a connettersi alla porta 443 (HTTPS) di github.com con timeout di 3 secondi
            socket.create_connection(("github.com", 443), timeout=3)
            return True
        except OSError:
            return False
    
    def show_keyboard(self, line_edit):
        """Show virtual keyboard for text input."""
        from .virtual_keyboard import VirtualKeyboard

        keyboard = VirtualKeyboard(line_edit.text(), self)
        if keyboard.exec() == QDialog.DialogCode.Accepted:
            line_edit.setText(keyboard.get_text())
    
    def on_power_toggle_changed(self, checked):
        """
        Gestisce il Toggle 'Master'.
        - Se Checked: Pin va HIGH (3.3V) -> Il sistema rimane acceso.
        - Se Unchecked: Pin va LOW (0V) -> Rilascia il controllo (come prima).
        """
        self.settings_manager.set("power_control_enabled", checked)
        self.power_off_button.setEnabled(checked)

        if not self.power_device:
            return

        if checked:
            print(f"Power Control ENABLED: GPIO {self.power_pin_number} -> HIGH")
            self.power_device.on() # Mette il pin a 3.3V
        else:
            print(f"Power Control DISABLED: GPIO {self.power_pin_number} -> LOW")
            self.power_device.off() # Mette il pin a 0V

    def perform_hardware_shutdown(self):
        """
        Taglia l'alimentazione portando il pin a LOW.
        Opzionale: Esegue prima lo shutdown software pulito del sistema.
        """
        if not self.power_device:
            return

        # Chiede conferma per evitare spegnimenti accidentali in auto
        reply = QMessageBox.question(
            self, 
            "Power Off", 
            "Are you sure you want to cut power?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            print("Cutting Power...")
            
            # OPZIONALE: Se vuoi che faccia anche lo shutdown pulito di Linux prima di tagliare:
            # subprocess.run(["shutdown", "now"]) 
            # (Ma se il tuo circuito è veloce, taglierà corrente prima che linux finisca)

            self.power_device.off() # GPIO -> LOW (Taglia corrente)
            
            # Disattiviamo il bottone visivamente
            self.power_off_button.setText("POWER CUT")
            self.power_off_button.setEnabled(False)

    def perform_app_update(self):
        """
        Tenta un aggiornamento standard. 
        Se fallisce per conflitti, offre all'utente l'opzione di forzare il reset.
        """
        print("Starting update process...")
        self.check_update_button.setText("Checking...")
        self.check_update_button.setEnabled(False)
        self.repaint() # Aggiorna la GUI subito

        # 1. Controllo Internet
        if not self.check_internet_connection():
            QMessageBox.warning(self, "Update Error", "No Internet Connection available.\nCheck your WiFi or hotspot.")
            self.check_update_button.setText("Check & Update from GitHub")
            self.check_update_button.setEnabled(True)
            return

        # 2. Conferma Iniziale (Gentile)
        reply = QMessageBox.question(
            self, 
            "Confirm Update", 
            "Do you want to pull the latest version from GitHub?\nThe application will restart.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.No:
            self.check_update_button.setText("Check & Update from GitHub")
            self.check_update_button.setEnabled(True)
            return

        # 3. Tentativo Standard (Git Pull)
        self.check_update_button.setText("Updating...")
        self.repaint()

        # Calcolo cartella progetto
        project_dir = os.path.dirname(os.path.abspath(__file__))
        if project_dir.endswith("gui"):
            project_dir = os.path.dirname(project_dir)

        try:
            # Esegue git pull standard
            result = subprocess.run(
                ["git", "pull", "origin", "main"], 
                cwd=project_dir, 
                capture_output=True, 
                text=True
            )

            if result.returncode == 0:
                # CASO A: Aggiornamento riuscito (o già aggiornato)
                if "Already up to date" in result.stdout:
                    QMessageBox.information(self, "Update", "The application is already up to date!")
                    self.check_update_button.setText("Check & Update from GitHub")
                    self.check_update_button.setEnabled(True)
                else:
                    QMessageBox.information(self, "Success", "Update installed successfully!\nRestarting...")
                    if self.main_window and hasattr(self.main_window, "restart_application"):
                        self.main_window.restart_application()
            
            else:
                # CASO B: Fallimento (Probabile conflitto)
                error_output = result.stderr
                print(f"Git Pull Failed: {error_output}")

                # Chiede all'utente se vuole FORZARE
                force_reply = QMessageBox.warning(
                    self, 
                    "Update Failed", 
                    f"Standard update failed (likely due to local file changes).\n\nError:\n{error_output}\n\nDo you want to FORCE the update?\nWARNING: This will delete your local changes.",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )

                if force_reply == QMessageBox.StandardButton.Yes:
                    self._force_update(project_dir)
                else:
                    self.check_update_button.setText("Check & Update from GitHub")
                    self.check_update_button.setEnabled(True)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred:\n{str(e)}")
            self.check_update_button.setText("Check & Update from GitHub")
            self.check_update_button.setEnabled(True)

    def _force_update(self, project_dir):
        """Funzione helper per eseguire il reset forzato."""
        self.check_update_button.setText("Forcing Update...")
        self.repaint()
        
        try:
            # 1. Fetch
            subprocess.run(["git", "fetch", "--all"], cwd=project_dir, capture_output=True)
            # 2. Reset Hard
            reset_result = subprocess.run(
                ["git", "reset", "--hard", "origin/main"], 
                cwd=project_dir, 
                capture_output=True, 
                text=True
            )

            if reset_result.returncode == 0:
                QMessageBox.information(self, "Forced Update", "Forced update successful!\nLocal changes overwritten.\nRestarting...")
                if self.main_window and hasattr(self.main_window, "restart_application"):
                    self.main_window.restart_application()
            else:
                QMessageBox.critical(self, "Fatal Error", f"Could not force update.\n{reset_result.stderr}")
                self.check_update_button.setText("Check & Update from GitHub")
                self.check_update_button.setEnabled(True)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error during forced update:\n{str(e)}")
            self.check_update_button.setText("Check & Update from GitHub")
            self.check_update_button.setEnabled(True)

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
        self.button_layout.setSpacing(
            scaled_button_layout_spacing
        )  # Scale button spacing

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

        # UI Render Mode Setting
        selected_render_mode = self.render_mode_combo.currentData()
        if selected_render_mode is None:
            selected_render_mode = "native"
        if selected_render_mode == "html" and not self.html_ui_available:
            print("HTML render mode selected but WebEngine is unavailable; keeping native mode.")
            selected_render_mode = "native"
        if selected_render_mode != self.settings_manager.get("ui_render_mode"):
            self.settings_manager.set("ui_render_mode", selected_render_mode)
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
                self.save_button.setText("Applied!")
                self.restart_button.setText("Applied!")
                self.save_button.setEnabled(False)
                self.restart_button.setEnabled(False)
                QTimer.singleShot(
                    2000,
                    lambda: (
                        self.save_button.setText("Apply Settings"),
                        self.restart_button.setText("Apply and Restart"),
                        self.save_button.setEnabled(True),
                        self.restart_button.setEnabled(True),
                    ),
                )
            else:
                print("Settings applied (No changes detected).")
                self.save_button.setText("No Changes")
                self.restart_button.setText("No Changes")
                self.save_button.setEnabled(False)
                self.restart_button.setEnabled(False)
                QTimer.singleShot(
                    1500,
                    lambda: (
                        self.save_button.setText("Apply Settings"),
                        self.restart_button.setText("Apply and Restart"),
                        self.save_button.setEnabled(True),
                        self.restart_button.setEnabled(True),
                    ),
                )

        if self.main_window and hasattr(self.main_window, "refresh_html_settings"):
            self.main_window.refresh_html_settings()
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
