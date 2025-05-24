# gui/airplay_click_overlay.py

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QColor


class AirPlayClickOverlay(QWidget):
    """Transparent overlay that captures clicks during AirPlay mirroring."""
    
    # Signals
    screen_clicked = pyqtSignal()  # Emitted when screen is clicked
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("airplayClickOverlay")
        
        # Make it transparent and capture clicks
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        
        # Initially hidden
        self.hide()
    
    def show_overlay(self):
        """Show the click overlay covering the entire parent."""
        if self.parent():
            # Cover the entire parent widget
            self.setGeometry(self.parent().rect())
        
        self.show()
        self.raise_()  # Bring to front to capture clicks
        print("AirPlay click overlay shown - screen is now clickable")
    
    def hide_overlay(self):
        """Hide the click overlay."""
        self.hide()
        print("AirPlay click overlay hidden")
    
    def mousePressEvent(self, event):
        """Handle mouse clicks on the overlay."""
        print("Screen clicked during AirPlay mirroring")
        self.screen_clicked.emit()
        event.accept()
    
    def paintEvent(self, event):
        """Paint the overlay - completely transparent."""
        painter = QPainter(self)
        # Make it completely transparent
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))
        painter.end()
    
    def resizeEvent(self, event):
        """Handle resize events."""
        super().resizeEvent(event)
        # Update geometry to match parent if needed
        if self.parent() and self.isVisible():
            self.setGeometry(self.parent().rect())
