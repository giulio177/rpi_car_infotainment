import sys
from PyQt6.QtWidgets import QApplication, QLabel, QWidget

print("App starting on target!") # Test message

app = QApplication(sys.argv)
window = QWidget()
window.setWindowTitle("Test App")
label = QLabel("Hello from RPi!", parent=window)
window.resize(300, 100)
window.show() # Or window.showFullScreen()

print("Showing window...")
sys.exit(app.exec())