# gui/airplay_video_screen.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, pyqtSlot
from PyQt6.QtGui import QFont, QPainter, QColor


class AirPlayVideoScreen(QWidget):
    """Screen that shows AirPlay video mirroring integrated in the UI."""

    # Signals
    back_requested = pyqtSignal()
    stop_airplay = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("airplayVideoScreen")

        # Store base sizes for scaling
        self.base_margin = 15
        self.base_spacing = 20
        self.base_button_height = 50
        self.base_font_size = 14

        # Video area widget
        self.video_area = None
        self.device_connected = False

        self.setup_ui()
        self.apply_theme()

    def setup_ui(self):
        """Setup the AirPlay video screen UI."""
        # Main layout - leave space for bottom bar
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)  # No margins, bottom bar handled by MainWindow
        main_layout.setSpacing(0)

        # Content area (everything except bottom bar)
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(self.base_margin, self.base_margin,
                                        self.base_margin, self.base_margin)
        content_layout.setSpacing(self.base_spacing)

        # Header with title and controls
        header_layout = QHBoxLayout()

        # Back button
        self.back_button = QPushButton("← Back")
        self.back_button.setObjectName("backButton")
        self.back_button.clicked.connect(self.back_requested.emit)
        self.back_button.setFixedHeight(self.base_button_height)
        header_layout.addWidget(self.back_button)

        # Title
        title_label = QLabel("AirPlay Video Mirroring")
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title_label, 1)

        # Stop button
        self.stop_button = QPushButton("Stop AirPlay")
        self.stop_button.setObjectName("stopButton")
        self.stop_button.clicked.connect(self.stop_airplay.emit)
        self.stop_button.setFixedHeight(self.base_button_height)
        header_layout.addWidget(self.stop_button)

        content_layout.addLayout(header_layout)

        # Video area - this will contain the phone screen
        self.video_area = QFrame()
        self.video_area.setObjectName("videoArea")
        self.video_area.setMinimumHeight(400)  # Ensure minimum size

        # Video area layout
        video_layout = QVBoxLayout(self.video_area)
        video_layout.setContentsMargins(0, 0, 0, 0)

        # Status label for when no device is connected
        self.status_label = QLabel("📱 Connect your device to 'Car Display' to see video mirroring here")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        video_layout.addWidget(self.status_label)

        content_layout.addWidget(self.video_area, 1)  # Take most of the space

        # Footer with connection info
        footer_layout = QHBoxLayout()

        # Connection status
        self.connection_label = QLabel("Status: Waiting for connection...")
        self.connection_label.setObjectName("connectionLabel")
        footer_layout.addWidget(self.connection_label)

        # Spacer
        footer_layout.addStretch()

        # Device name info
        device_info = QLabel("Device Name: 'Car Display'")
        device_info.setObjectName("deviceInfo")
        footer_layout.addWidget(device_info)

        content_layout.addLayout(footer_layout)

        # Add content widget to main layout (bottom bar is handled by MainWindow)
        main_layout.addWidget(content_widget)

    def apply_theme(self):
        """Apply theme to the AirPlay video screen."""
        self.setStyleSheet("""
            QWidget#airplayVideoScreen {
                background-color: #1e1e1e;
                color: white;
            }

            QPushButton#backButton, QPushButton#stopButton {
                background-color: #333333;
                color: white;
                border: 2px solid #555555;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 16px;
                font-weight: bold;
                min-width: 120px;
            }

            QPushButton#backButton:hover, QPushButton#stopButton:hover {
                background-color: #444444;
                border-color: #666666;
            }

            QPushButton#stopButton {
                background-color: #d32f2f;
                border-color: #f44336;
            }

            QPushButton#stopButton:hover {
                background-color: #c62828;
                border-color: #e53935;
            }

            QLabel#titleLabel {
                color: #2196F3;
                font-size: 24px;
                font-weight: bold;
                padding: 10px;
            }

            QFrame#videoArea {
                background-color: #000000;
                border: 3px solid #2196F3;
                border-radius: 10px;
                margin: 10px;
            }

            QLabel#statusLabel {
                color: #cccccc;
                font-size: 18px;
                padding: 40px;
                background: transparent;
            }

            QLabel#connectionLabel {
                color: #ffeb3b;
                font-size: 14px;
                font-weight: bold;
            }

            QLabel#deviceInfo {
                color: #4caf50;
                font-size: 14px;
            }
        """)

    @pyqtSlot(bool)
    def on_device_connected(self, connected):
        """Handle device connection status change."""
        self.device_connected = connected

        if connected:
            self.connection_label.setText("Status: Device connected - Video mirroring active")
            self.connection_label.setStyleSheet("color: #4caf50; font-weight: bold;")
            self.status_label.setText("📱 Your device screen is being mirrored below\n\nVideo content will appear in this area")

            # Here we would embed the actual video widget
            self._setup_video_widget()

        else:
            self.connection_label.setText("Status: Waiting for connection...")
            self.connection_label.setStyleSheet("color: #ffeb3b; font-weight: bold;")
            self.status_label.setText("📱 Connect your device to 'Car Display' to see video mirroring here")

            # Remove video widget
            self._remove_video_widget()

    def _setup_video_widget(self):
        """Setup the video widget for displaying phone screen."""
        # Remove the status label
        self.status_label.hide()

        # Create a placeholder for the video
        # In a real implementation, this would be where we embed the X11 window
        # or create a widget that captures the RPiPlay video output
        if not hasattr(self, 'video_placeholder'):
            self.video_placeholder = QLabel("🎥 Video Stream Active\n\nPhone screen content will appear here")
            self.video_placeholder.setObjectName("videoPlaceholder")
            self.video_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.video_placeholder.setStyleSheet("""
                QLabel#videoPlaceholder {
                    background-color: #1a1a1a;
                    color: #2196F3;
                    font-size: 20px;
                    font-weight: bold;
                    border: 2px dashed #2196F3;
                    border-radius: 8px;
                    padding: 20px;
                }
            """)

            # Add to video area layout
            self.video_area.layout().addWidget(self.video_placeholder)

        self.video_placeholder.show()

    def _remove_video_widget(self):
        """Remove the video widget."""
        if hasattr(self, 'video_placeholder'):
            self.video_placeholder.hide()

        self.status_label.show()

    def resizeEvent(self, event):
        """Handle resize events to maintain proper scaling."""
        super().resizeEvent(event)

        # Scale UI elements based on window size
        scale_factor = min(self.width() / 1024, self.height() / 600)
        scale_factor = max(0.8, min(scale_factor, 2.0))  # Limit scaling

        # Update font sizes
        font_size = int(self.base_font_size * scale_factor)
        button_height = int(self.base_button_height * scale_factor)

        # Apply scaling to buttons
        for button in [self.back_button, self.stop_button]:
            button.setFixedHeight(button_height)
            font = button.font()
            font.setPointSize(font_size)
            button.setFont(font)

    def get_video_area_geometry(self):
        """Get the geometry of the video area for embedding external windows."""
        if self.video_area:
            # Get global position of video area
            global_pos = self.video_area.mapToGlobal(self.video_area.rect().topLeft())
            return {
                'x': global_pos.x(),
                'y': global_pos.y(),
                'width': self.video_area.width(),
                'height': self.video_area.height()
            }
        return None
