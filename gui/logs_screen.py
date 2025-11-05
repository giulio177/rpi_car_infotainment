# gui/logs_screen.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QPushButton, QGroupBox, QPlainTextEdit
)
from PyQt6.QtCore import Qt, pyqtSlot
from backend.log_streamer import LogStreamer

from .styling import scale_value

class LogsScreen(QWidget):
    screen_title = "Logs"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.log_streamer = LogStreamer()

        self.setup_ui()
        self.log_streamer.new_line.connect(self.append_line)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Gruppo Logs
        group = QGroupBox("Output dell'applicazione")
        vbox = QVBoxLayout(group)

        self.text_edit = QPlainTextEdit()
        self.text_edit.setObjectName("logsText")
        self.text_edit.setReadOnly(True)
        self.text_edit.setMaximumBlockCount(10000)
        vbox.addWidget(self.text_edit)

        # Pulsante pulizia
        self.clear_btn = QPushButton("Pulisci")
        self.clear_btn.clicked.connect(self.text_edit.clear)
        vbox.addWidget(self.clear_btn)

        layout.addWidget(group)

    @pyqtSlot(str)
    def append_line(self, line):
        self.text_edit.appendPlainText(line)
        sb = self.text_edit.verticalScrollBar()
        sb.setValue(sb.maximum())