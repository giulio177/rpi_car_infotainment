# gui/airplay_screen.py

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QGroupBox,
    QLineEdit,
    QComboBox,
    QSpacerItem,
    QSizePolicy,
    QFrame,
    QScrollArea,
    QApplication,
    QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QFont, QPixmap
from .styling import scale_value


class AirPlayScreen(QWidget):
    """Screen for AirPlay mirroring control and status."""

    # Screen Title
    screen_title = "AirPlay Mirroring"

    def __init__(self, airplay_manager, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.airplay_manager = airplay_manager

        # Store base sizes for scaling
        self.base_margin = 15
        self.base_spacing = 20
        self.base_button_height = 50
        self.base_font_size = 14

        # Current status
        self.current_status = "stopped"

        # Overlay widget for AirPlay mirroring
        self.airplay_overlay = None

        self.setup_ui()
        self.connect_signals()
        self.update_ui_state()
        self.apply_theme_from_mainwindow()

    def apply_theme_from_mainwindow(self):
        # Get theme from main window/settings
        theme = None
        if self.main_window and hasattr(self.main_window, "current_theme"):
            theme = self.main_window.current_theme
        elif hasattr(self, "settings_manager"):
            theme = self.settings_manager.get("theme")

        if theme == "dark":
            self.setObjectName("airplayScreenDark")
        else:
            self.setObjectName("airplayScreenLight")

        # Force style update on main widget
        self.style().unpolish(self)
        self.style().polish(self)

    def setup_ui(self):
        """Set up the user interface."""
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(
            self.base_margin, self.base_margin, self.base_margin, self.base_margin
        )
        self.main_layout.setSpacing(self.base_spacing)

        # --- Remove duplicate title (keep only top bar title) ---
        # self.title_label = QLabel("AirPlay Mirroring")  # REMOVE

        # Status section
        self.create_status_section()
        self.create_control_section()
        self.create_settings_section()
        # Removed instructions section - will be in settings popup instead
        self.main_layout.addStretch()

        # Removed scrollable area - content is now compact enough

    def create_status_section(self):
        """Create the status display section."""
        status_group = QGroupBox("Status")
        status_layout = QHBoxLayout(status_group)  # Changed to horizontal layout

        # Status indicator on the left
        status_left_layout = QVBoxLayout()
        status_left_layout.addWidget(QLabel("Status:"))
        self.status_label = QLabel("Stopped")
        self.status_label.setObjectName("statusLabel")
        font = QFont()
        font.setPointSize(self.base_font_size + 1)  # Slightly smaller
        font.setBold(True)
        self.status_label.setFont(font)
        status_left_layout.addWidget(self.status_label)
        status_layout.addLayout(status_left_layout)

        # Add some spacing
        status_layout.addStretch(1)

        # Device name display on the right
        device_right_layout = QVBoxLayout()
        device_right_layout.addWidget(QLabel("Device Name:"))
        self.device_name_display = QLabel(self.airplay_manager.airplay_name)
        self.device_name_display.setStyleSheet("font-weight: bold;")
        device_right_layout.addWidget(self.device_name_display)
        status_layout.addLayout(device_right_layout)

        self.main_layout.addWidget(status_group)

    def create_control_section(self):
        """Create the control buttons section."""
        control_group = QGroupBox("Control")
        control_layout = QVBoxLayout(control_group)

        # Button layout
        button_layout = QHBoxLayout()

        # Start button
        self.start_button = QPushButton("Start AirPlay")
        self.start_button.setObjectName("startAirPlayButton")
        self.start_button.clicked.connect(self.start_airplay)
        button_layout.addWidget(self.start_button)

        # Stop button
        self.stop_button = QPushButton("Stop AirPlay")
        self.stop_button.setObjectName("stopAirPlayButton")
        self.stop_button.clicked.connect(self.stop_airplay)
        button_layout.addWidget(self.stop_button)

        # Restart button
        self.restart_button = QPushButton("Restart")
        self.restart_button.setObjectName("restartAirPlayButton")
        self.restart_button.clicked.connect(self.restart_airplay)
        button_layout.addWidget(self.restart_button)

        control_layout.addLayout(button_layout)
        self.main_layout.addWidget(control_group)

    def create_settings_section(self):
        """Create the settings section."""
        settings_group = QGroupBox("Settings")
        settings_layout = QVBoxLayout(settings_group)

        # Device name setting
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Device Name:"))
        self.device_name_input = QLineEdit(self.airplay_manager.airplay_name)
        self.device_name_input.setPlaceholderText("Enter device name")
        name_layout.addWidget(self.device_name_input)

        self.apply_name_button = QPushButton("Apply")
        self.apply_name_button.clicked.connect(self.apply_device_name)
        name_layout.addWidget(self.apply_name_button)
        settings_layout.addLayout(name_layout)

        # Background mode setting with connection info button
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Background Mode:"))
        self.background_mode_combo = QComboBox()
        self.background_mode_combo.addItems(["auto", "fill", "fit", "stretch"])
        self.background_mode_combo.setCurrentText(self.airplay_manager.background_mode)
        self.background_mode_combo.currentTextChanged.connect(self.apply_background_mode)
        mode_layout.addWidget(self.background_mode_combo)
        mode_layout.addStretch()

        # Connection info button on the right
        self.connection_info_button = QPushButton("Connection Info")
        self.connection_info_button.setObjectName("airplayInfoButton")
        self.connection_info_button.clicked.connect(self.show_connection_info)
        mode_layout.addWidget(self.connection_info_button)

        settings_layout.addLayout(mode_layout)

        self.main_layout.addWidget(settings_group)

    # Instructions section removed - now available via popup in settings

    def connect_signals(self):
        """Connect AirPlay manager signals."""
        if self.airplay_manager:
            self.airplay_manager.status_changed.connect(self.on_status_changed)
            self.airplay_manager.connection_changed.connect(self.on_connection_changed)
            # Connect overlay signals if using overlay manager
            if hasattr(self.airplay_manager, 'show_overlay'):
                self.airplay_manager.show_overlay.connect(self.on_show_overlay)

    @pyqtSlot()
    def start_airplay(self):
        """Start AirPlay service."""
        if self.airplay_manager:
            success = self.airplay_manager.start_airplay()
            if not success:
                self.status_label.setText("Error Starting")
                self.status_label.setStyleSheet("color: red;")

    @pyqtSlot()
    def stop_airplay(self):
        """Stop AirPlay service."""
        if self.airplay_manager:
            self.airplay_manager.stop_airplay()

    @pyqtSlot()
    def restart_airplay(self):
        """Restart AirPlay service."""
        if self.airplay_manager:
            self.airplay_manager.restart_airplay()

    @pyqtSlot()
    def apply_device_name(self):
        """Apply the new device name."""
        new_name = self.device_name_input.text().strip()
        if new_name and self.airplay_manager:
            self.airplay_manager.set_device_name(new_name)
            self.device_name_display.setText(new_name)

    @pyqtSlot(str)
    def apply_background_mode(self, mode):
        """Apply the new background mode."""
        if self.airplay_manager:
            self.airplay_manager.set_background_mode(mode)

    @pyqtSlot(str)
    def on_status_changed(self, status):
        """Handle status change from AirPlay manager."""
        self.current_status = status
        self.update_ui_state()

    @pyqtSlot(bool)
    def on_connection_changed(self, connected):
        """Handle connection change from AirPlay manager."""
        if connected:
            self.status_label.setText("Device Connected - Mirroring Active")
            self.status_label.setStyleSheet("color: blue; font-weight: bold;")
        else:
            if self.current_status == "running":
                self.status_label.setText("Ready - Discoverable as 'Car Display'")
                self.status_label.setStyleSheet("color: green; font-weight: bold;")

    @pyqtSlot(bool)
    def on_show_overlay(self, show):
        """Handle overlay show/hide from AirPlay manager."""
        if show:
            # Create overlay if it doesn't exist
            if not self.airplay_overlay and self.main_window:
                self.airplay_overlay = self._create_airplay_overlay()

            if self.airplay_overlay:
                self.airplay_overlay.show()
                self.airplay_overlay.raise_()  # Bring to front
                print("AirPlay overlay shown")
        else:
            if self.airplay_overlay:
                self.airplay_overlay.hide()
                print("AirPlay overlay hidden")

    def _create_airplay_overlay(self):
        """Create the AirPlay overlay widget."""
        if not self.main_window:
            return None

        from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
        from PyQt6.QtCore import Qt

        overlay = QWidget(self.main_window)
        overlay.setObjectName("airplayOverlay")

        # Make it cover the entire main window
        overlay.setGeometry(self.main_window.rect())

        # Semi-transparent background with border
        overlay.setStyleSheet("""
            QWidget#airplayOverlay {
                background-color: rgba(0, 0, 0, 180);
                border: 3px solid #00ff00;
                border-radius: 10px;
            }
            QLabel {
                color: white;
                font-size: 28px;
                font-weight: bold;
                background: transparent;
            }
        """)

        layout = QVBoxLayout(overlay)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        label = QLabel("🔄 AirPlay Mirroring Active\n\nYour device screen is being mirrored")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setWordWrap(True)

        layout.addWidget(label)

        # Initially hidden
        overlay.hide()

        return overlay

    def update_scaling(self, scale_factor, scaled_main_margin):
        """Update scaling and apply theme changes."""
        # Apply scaling to margins and spacing
        scaled_margin = int(self.base_margin * scale_factor)
        scaled_spacing = int(self.base_spacing * scale_factor)
        scaled_button_height = int(self.base_button_height * scale_factor)

        # Update main layout
        self.main_layout.setContentsMargins(
            scaled_margin, scaled_margin, scaled_margin, scaled_margin
        )
        self.main_layout.setSpacing(scaled_spacing)

        # No scroll content to update anymore

        # Apply theme (this will be called when theme changes)
        self.apply_theme_from_mainwindow()

    def update_ui_state(self):
        """Update UI based on current status."""
        if not self.airplay_manager or not self.airplay_manager.is_available():
            self.status_label.setText("RPiPlay Not Available")
            self.status_label.setStyleSheet("color: red;")
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(False)
            self.restart_button.setEnabled(False)
            return

        if self.current_status == "starting":
            self.status_label.setText("Starting...")
            self.status_label.setStyleSheet("color: orange;")
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.restart_button.setEnabled(False)
        elif self.current_status == "running":
            self.status_label.setText("Ready - Discoverable as 'Car Display'")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.restart_button.setEnabled(True)
        elif self.current_status == "stopped":
            self.status_label.setText("Stopped")
            self.status_label.setStyleSheet("color: gray;")
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.restart_button.setEnabled(False)
        elif self.current_status == "error":
            self.status_label.setText("Error - Check Console for Details")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.restart_button.setEnabled(False)

    def show_connection_info(self):
        """Show AirPlay connection information popup."""
        instructions_text = """How to Connect to AirPlay:

1. Make sure your iPhone/iPad and this device are on the same Wi-Fi network

2. Click "Start AirPlay" to make this device discoverable

3. On your iPhone/iPad:
   • Open Control Center (swipe down from top-right on newer devices, or swipe up from bottom on older devices)
   • Tap "Screen Mirroring" or the AirPlay icon
   • Select "Car Display" (or your custom device name from the list)

4. Your device screen will appear on this display

5. To disconnect, either:
   • Use Screen Mirroring in Control Center and tap "Stop Mirroring"
   • Or click "Stop AirPlay" in the Control section above

Note: Both devices must be connected to the same Wi-Fi network for AirPlay to work properly."""

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("AirPlay Connection Instructions")
        msg_box.setText(instructions_text)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()
