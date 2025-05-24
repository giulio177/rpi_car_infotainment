# gui/airplay_control_popup.py

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont


class AirPlayControlPopup(QWidget):
    """Popup widget that appears when clicking during AirPlay mirroring."""
    
    # Signals
    close_popup = pyqtSignal()  # Just close the popup
    stop_airplay = pyqtSignal()  # Stop AirPlay mirroring completely
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("airplayControlPopup")
        
        # Auto-hide timer
        self.auto_hide_timer = QTimer()
        self.auto_hide_timer.timeout.connect(self.close_popup.emit)
        self.auto_hide_timer.setSingleShot(True)
        
        self.setup_ui()
        self.apply_styles()
        
        # Initially hidden
        self.hide()
    
    def setup_ui(self):
        """Setup the popup UI."""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title_label = QLabel("AirPlay Control")
        title_label.setObjectName("popupTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Info text
        info_label = QLabel("Choose an action:")
        info_label.setObjectName("popupInfo")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(20)
        
        # Continue button (close popup)
        self.continue_button = QPushButton("Continue Mirroring")
        self.continue_button.setObjectName("continueButton")
        self.continue_button.clicked.connect(self.close_popup.emit)
        buttons_layout.addWidget(self.continue_button)
        
        # Stop AirPlay button
        self.stop_button = QPushButton("Stop AirPlay")
        self.stop_button.setObjectName("stopButton")
        self.stop_button.clicked.connect(self.stop_airplay.emit)
        buttons_layout.addWidget(self.stop_button)
        
        layout.addLayout(buttons_layout)
        
        # Auto-hide info
        auto_hide_label = QLabel("This popup will auto-hide in 10 seconds")
        auto_hide_label.setObjectName("autoHideInfo")
        auto_hide_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(auto_hide_label)
    
    def apply_styles(self):
        """Apply styles to the popup."""
        self.setStyleSheet("""
            QWidget#airplayControlPopup {
                background-color: rgba(0, 0, 0, 220);
                border: 3px solid #00ff00;
                border-radius: 15px;
            }
            
            QLabel#popupTitle {
                color: white;
                font-size: 24px;
                font-weight: bold;
                padding: 10px;
            }
            
            QLabel#popupInfo {
                color: #cccccc;
                font-size: 16px;
                padding: 5px;
            }
            
            QLabel#autoHideInfo {
                color: #888888;
                font-size: 12px;
                font-style: italic;
                padding: 5px;
            }
            
            QPushButton#continueButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 15px 25px;
                font-size: 16px;
                font-weight: bold;
                min-width: 150px;
            }
            
            QPushButton#continueButton:hover {
                background-color: #45a049;
            }
            
            QPushButton#continueButton:pressed {
                background-color: #3d8b40;
            }
            
            QPushButton#stopButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 8px;
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
    
    def show_popup(self):
        """Show the popup and start auto-hide timer."""
        # Center the popup on the parent
        if self.parent():
            parent_rect = self.parent().rect()
            popup_size = self.sizeHint()
            x = (parent_rect.width() - popup_size.width()) // 2
            y = (parent_rect.height() - popup_size.height()) // 2
            self.setGeometry(x, y, popup_size.width(), popup_size.height())
        
        self.show()
        self.raise_()
        
        # Start auto-hide timer (10 seconds)
        self.auto_hide_timer.start(10000)
        
        print("AirPlay control popup shown")
    
    def hide_popup(self):
        """Hide the popup and stop timer."""
        self.auto_hide_timer.stop()
        self.hide()
        print("AirPlay control popup hidden")
    
    def mousePressEvent(self, event):
        """Handle mouse clicks - prevent clicks from going through to background."""
        event.accept()  # Consume the event
        super().mousePressEvent(event)
    
    def keyPressEvent(self, event):
        """Handle key presses."""
        if event.key() == Qt.Key.Key_Escape:
            self.close_popup.emit()
        else:
            super().keyPressEvent(event)
