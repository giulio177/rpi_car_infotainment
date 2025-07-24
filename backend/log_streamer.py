# backend/log_streamer.py
import os
import subprocess
import threading
from queue import Queue, Empty
from PyQt6.QtCore import QObject, pyqtSignal, QTimer


class LogStreamer(QObject):
    new_line = pyqtSignal(str)

    def __init__(self, log_path="/tmp/app_output.log"):
        super().__init__()
        self.log_path = log_path
        self._running = True
        self._queue = Queue()

        # Thread che tail -f il file
        self._thread = threading.Thread(target=self._tail, daemon=True)
        self._thread.start()

        # Timer Qt per svuotare la coda nel main thread
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._emit_lines)
        self._timer.start(200)

    def _tail(self):
        if not os.path.exists(self.log_path):
            open(self.log_path, "w").close()
        proc = subprocess.Popen(
            ["tail", "-F", self.log_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        for line in proc.stdout:
            if not self._running:
                break
            self._queue.put(line.rstrip())

    def _emit_lines(self):
        while True:
            try:
                line = self._queue.get_nowait()
                self.new_line.emit(line)
            except Empty:
                break

    def stop(self):
        self._running = False
        self._timer.stop()