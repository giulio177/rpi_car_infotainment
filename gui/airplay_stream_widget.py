# gui/airplay_stream_widget.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPainter, QColor, QPixmap


class AirPlayStreamWidget(QWidget):
    """Widget that shows AirPlay streaming status and controls."""
    
    # Signals
    stop_airplay = pyqtSignal()  # Stop AirPlay streaming
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("airplayStreamWidget")
        
        self.setup_ui()
        self.apply_styles()
        
        # Initially hidden
        self.hide()
    
    def setup_ui(self):
        """Setup the stream widget UI."""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(30)
        layout.setContentsMargins(50, 50, 50, 50)
        
        # Title
        title_label = QLabel("🎵 AirPlay Audio Streaming")
        title_label.setObjectName("streamTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Status
        status_label = QLabel("Your device is connected and streaming audio")
        status_label.setObjectName("streamStatus")
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(status_label)
        
        # Info about video
        info_label = QLabel("Video mirroring is not available in this mode\nto ensure system stability and UI accessibility")
        info_label.setObjectName("streamInfo")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Controls layout
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(20)
        
        # Close button (hide widget)
        self.close_button = QPushButton("Continue with Car UI")
        self.close_button.setObjectName("closeButton")
        self.close_button.clicked.connect(self.hide_widget)
        controls_layout.addWidget(self.close_button)
        
        # Stop AirPlay button
        self.stop_button = QPushButton("Stop AirPlay")
        self.stop_button.setObjectName("stopButton")
        self.stop_button.clicked.connect(self.stop_airplay.emit)
        controls_layout.addWidget(self.stop_button)
        
        layout.addLayout(controls_layout)
        
        # Instructions
        instructions_label = QLabel("You can continue using the car interface while audio streams in the background")
        instructions_label.setObjectName("instructionsLabel")
        instructions_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instructions_label.setWordWrap(True)
        layout.addWidget(instructions_label)
    
    def apply_styles(self):
        """Apply styles to the stream widget."""
        self.setStyleSheet("""
            QWidget#airplayStreamWidget {
                background-color: rgba(0, 0, 0, 200);
                border: 3px solid #2196F3;
                border-radius: 20px;
            }
            
            QLabel#streamTitle {
                color: #2196F3;
                font-size: 32px;
                font-weight: bold;
                padding: 20px;
            }
            
            QLabel#streamStatus {
                color: white;
                font-size: 20px;
                font-weight: bold;
                padding: 10px;
            }
            
            QLabel#streamInfo {
                color: #cccccc;
                font-size: 16px;
                padding: 10px;
                font-style: italic;
            }
            
            QLabel#instructionsLabel {
                color: #888888;
                font-size: 14px;
                padding: 10px;
            }
            
            QPushButton#closeButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 15px 25px;
                font-size: 16px;
                font-weight: bold;
                min-width: 180px;
            }
            
            QPushButton#closeButton:hover {
                background-color: #45a049;
            }
            
            QPushButton#closeButton:pressed {
                background-color: #3d8b40;
            }
            
            QPushButton#stopButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 15px 25px;
                font-size: 16px;
                font-weight: bold;
                min-width: 150px;
            }
            
            QPushButton#stopButton:hover {
                background-color: #da190b;
            }
            
            QPushButton#stopButton:pressed {
                background-color: #c1170a;
            }
        """)
    
    def show_widget(self):
        """Show the stream widget covering the parent."""
        if self.parent():
            # Cover the entire parent widget
            self.setGeometry(self.parent().rect())
        
        self.show()
        self.raise_()
        print("AirPlay stream widget shown")
    
    def hide_widget(self):
        """Hide the stream widget."""
        self.hide()
        print("AirPlay stream widget hidden")
    
    def mousePressEvent(self, event):
        """Handle mouse clicks - prevent clicks from going through to background."""
        event.accept()  # Consume the event
        super().mousePressEvent(event)
    
    def keyPressEvent(self, event):
        """Handle key presses."""
        if event.key() == Qt.Key.Key_Escape:
            self.hide_widget()
        else:
            super().keyPressEvent(event)
    
    def resizeEvent(self, event):
        """Handle resize events."""
        super().resizeEvent(event)
        # Update geometry to match parent if needed
        if self.parent() and self.isVisible():
            self.setGeometry(self.parent().rect())
