# gui/home_screen.py

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt

class HomeScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter) # Center content vertically and horizontally

        self.welcome_label = QLabel("Welcome!")
        self.welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.welcome_label.setStyleSheet("font-size: 28pt; font-weight: bold;")

        self.layout.addWidget(self.welcome_label)

        # You can add more widgets here later (time, date, status icons...)
