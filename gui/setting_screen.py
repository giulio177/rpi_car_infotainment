# gui/setting_screen.py

import socket # <--- AGGIUNGI QUESTO
import os     # <--- AGGIUNGI QUESTO
import sys
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
from PyQt6.QtCore import QTimer, QDateTime, pyqtSlot, Qt, pyqtSignal, QProcess, QProcess

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

        # Aggiunta al layout
        # self.power_layout.addWidget(self.power_toggle)
        # self.power_layout.addWidget(self.power_off_button)
        
        # Boot configuration button
        self.apply_boot_config_button = QPushButton("Apply Boot Configuration")
        self.apply_boot_config_button.clicked.connect(self.apply_boot_config)
        self.power_layout.addWidget(self.apply_boot_config_button)
        
        self.scroll_layout.addWidget(self.power_group)

        
        
        # --- UPDATE SECTION (Software Update) ---
        self.update_group = QGroupBox("Software Update")
        self.update_group.setObjectName("settingsUpdateGroup")
        self.update_layout = QVBoxLayout()
        self.update_group.setLayout(self.update_layout)

        self.update_info_label = QLabel("Current Version: Main Branch")
        self.update_info_label.setStyleSheet("color: gray; font-size: 12px;")
        self.update_layout.addWidget(self.update_info_label)

        # Update Buttons Layout
        self.update_buttons_layout = QHBoxLayout()
        
        self.check_update_button = QPushButton("Update (GitHub)")
        self.check_update_button.setMinimumHeight(45)
        self.check_update_button.clicked.connect(self.perform_app_update)
        
        self.revert_update_button = QPushButton("Revert Version")
        self.revert_update_button.setMinimumHeight(45)
        self.revert_update_button.setStyleSheet("background-color: #666; color: white;")
        self.revert_update_button.clicked.connect(self.revert_app_update)
        
        self.update_buttons_layout.addWidget(self.check_update_button)
        self.update_buttons_layout.addWidget(self.revert_update_button)
        self.update_layout.addLayout(self.update_buttons_layout)

        self.scroll_layout.addWidget(self.update_group)

        # Add a large spacer at the bottom so the last setting isn't covered by the floating button
        self.scroll_layout.addSpacing(100)
        
        # Add stretch at the end of the scroll content
        self.scroll_layout.addStretch(1)
        # Set the content widget for the scroll area
        self.scroll_area.setWidget(self.scroll_content_widget)
        # Add scroll area to the main layout
        self.main_layout.addWidget(self.scroll_area, 1)

        # AirPlay info button moved to AirPlay screen settings section

        # --- Floating "Apply Settings" Button ---
        # Created as a child of 'self' (the overlay), NOT added to any layout.
        self.save_button = QPushButton("Apply Settings", self)
        self.save_button.setObjectName("settingsSaveButton")
        self.save_button.setFixedSize(160, 45) # Slightly smaller than before
        self.save_button.clicked.connect(self.apply_settings)
        
        # Initial position (will be updated by resizeEvent)
        self.save_button.show()
        self.save_button.raise_() # Ensure it stays on top

        # ## MODIFICATO: Collegamento del segnale e avvio del timer stabile ##
        self.info_updated.connect(self.update_info_labels)
        self.info_update_timer = QTimer(self)
        self.info_update_timer.timeout.connect(self.start_info_update_thread)
        self.info_update_timer.start(10000) # Aggiorna ogni 10 secondi per ridurre il carico
        self.start_info_update_thread() # Chiamata iniziale

    def resizeEvent(self, event):
        """Handle resize events to position the floating button."""
        super().resizeEvent(event)
        if hasattr(self, 'save_button'):
            # Position: Bottom Right with margin
            margin = 20
            x = self.width() - self.save_button.width() - margin - 20
            y = self.height() - self.save_button.height() - margin
            self.save_button.move(x, y)
            self.save_button.raise_() # Ensure top z-order

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
    


    def apply_boot_config(self):
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'deployment', 'configure_boot.sh'))
        
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        
        self.process.readyReadStandardOutput.connect(self.handle_output)
        self.process.finished.connect(self.handle_finish)
        
        # The user will be prompted for the password in the terminal where the app was launched
        self.process.start("sudo", ["bash", script_path])

    def handle_output(self):
        output = self.process.readAllStandardOutput().data().decode().strip()
        print(f"Script output: {output}")
        # NOTE: Showing a message box here might be too noisy if the script produces a lot of output.
        # A log window would be a better place for this. For now, we print to console.
        
    def handle_finish(self, exit_code, exit_status):
        output = self.process.readAllStandardOutput().data().decode().strip()
        if exit_code == 0:
            QMessageBox.information(self, "Success", f"Boot configuration applied successfully.\n\nOutput:\n{output}\n\nPlease reboot for the changes to take effect.")
        else:
            QMessageBox.warning(self, "Error", f"Failed to apply boot configuration. See terminal for details.\n\nOutput:\n{output}")


    def _install_dependencies(self, project_dir):
        """Installs dependencies from requirements.txt."""
        req_file = os.path.join(project_dir, "requirements.txt")
        if os.path.exists(req_file):
            print("Installing dependencies...")
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-r", req_file], 
                    check=True, 
                    capture_output=True
                )
                print("Dependencies installed successfully.")
            except Exception as e:
                print(f"Error installing dependencies: {e}")

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
                    self._install_dependencies(project_dir) # Install dependencies
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
                self._install_dependencies(project_dir) # Install dependencies
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

    def revert_app_update(self):
        """Reverts the application to the previous commit/version."""
        # Calcolo cartella progetto
        project_dir = os.path.dirname(os.path.abspath(__file__))
        if project_dir.endswith("gui"):
            project_dir = os.path.dirname(project_dir)

        reply = QMessageBox.question(
            self,
            "Revert Version",
            "Are you sure you want to revert to the previous version?\nThis will undo the last update.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.No:
            return

        self.revert_update_button.setText("Reverting...")
        self.revert_update_button.setEnabled(False)
        self.repaint()

        try:
            # Attempt to reset to the previous state (ORIG_HEAD is usually set before a merge/pull)
            # Alternatively, HEAD@{1} refers to the state before the last action.
            # Using HEAD@{1} is safer for "undoing" the last git command in the reflog.
            
            result = subprocess.run(
                ["git", "reset", "--hard", "HEAD@{1}"],
                cwd=project_dir,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                self._install_dependencies(project_dir) # Install dependencies
                QMessageBox.information(
                    self, 
                    "Revert Successful", 
                    "Successfully reverted to previous version.\nThe application will now restart."
                )
                if self.main_window and hasattr(self.main_window, "restart_application"):
                    self.main_window.restart_application()
            else:
                error_msg = result.stderr
                if "Reflog is not enabled" in error_msg or "HEAD@{1}" in error_msg:
                     # Fallback to HEAD^ (parent commit) if reflog fails
                     print("Reflog failed, trying HEAD^")
                     result = subprocess.run(
                        ["git", "reset", "--hard", "HEAD^"],
                        cwd=project_dir,
                        capture_output=True,
                        text=True
                    )
                     if result.returncode == 0:
                        self._install_dependencies(project_dir) # Install dependencies
                        QMessageBox.information(
                            self, 
                            "Revert Successful", 
                            "Successfully reverted to previous commit.\nThe application will now restart."
                        )
                        if self.main_window and hasattr(self.main_window, "restart_application"):
                            self.main_window.restart_application()
                        return

                QMessageBox.critical(self, "Revert Failed", f"Could not revert version:\n{error_msg}")
                self.revert_update_button.setText("Revert Version")
                self.revert_update_button.setEnabled(True)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred:\n{str(e)}")
            self.revert_update_button.setText("Revert Version")
            self.revert_update_button.setEnabled(True)

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

        # Apply to MAIN layouts
        self.main_layout.setContentsMargins(
            scaled_main_margin,
            scaled_main_margin,
            scaled_main_margin,
            scaled_main_margin,
        )
        self.main_layout.setSpacing(scaled_spacing)

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
        if settings_changed:
            if restart_required:
                reply = QMessageBox.question(
                    self, 
                    "Restart Required", 
                    "Settings saved. Some changes require a restart to take effect.\nDo you want to restart now?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    if self.main_window and hasattr(self.main_window, "restart_application"):
                        self.main_window.restart_application()
                    return True
                else:
                    self.save_button.setText("Saved (Restart Needed)")
            else:
                self.save_button.setText("Applied!")
        else:
            self.save_button.setText("No Changes")

        self.save_button.setEnabled(False)
        
        # Reset button state after delay (shortened)
        QTimer.singleShot(
            500,
            lambda: (
                self.save_button.setText("Apply Settings"),
                self.save_button.setEnabled(True),
            ),
        )

        if self.main_window and hasattr(self.main_window, "refresh_html_settings"):
            self.main_window.refresh_html_settings()
        return restart_required

    # AirPlay info popup method moved to AirPlay screen
