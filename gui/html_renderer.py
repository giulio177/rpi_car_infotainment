"""Reusable helpers to embed HTML-based screens inside the PyQt6 application."""

from __future__ import annotations

import json
import os
from typing import Any, Dict

from PyQt6.QtCore import QObject, QUrl, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import QVBoxLayout, QWidget

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebChannel import QWebChannel
except ImportError as exc:  # pragma: no cover - handled at runtime
    raise ImportError(
        "PyQt6-WebEngine is required to use the HTML rendering helpers."
    ) from exc


class HtmlBridge(QObject):
    """Bridge object exposed to the JavaScript runtime."""

    event_received = pyqtSignal(str, dict)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)

    @pyqtSlot(str, "QVariant")
    @pyqtSlot(str, object)
    def emit_event(self, name: str, payload: Any) -> None:
        """Receive events from JavaScript and forward them to Python."""
        if isinstance(payload, str):
            try:
                payload_obj = json.loads(payload)
            except json.JSONDecodeError:
                payload_obj = {"raw": payload}
        elif payload is None:
            payload_obj = {}
        elif isinstance(payload, dict):
            payload_obj = payload
        else:
            payload_obj = {"value": payload}
        self.event_received.emit(name, payload_obj)


class HtmlView(QWidget):
    """Widget that hosts a QWebEngineView with a ready-to-use bridge."""

    event_received = pyqtSignal(str, dict)

    def __init__(self, html_path: str | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._view = QWebEngineView(self)
        self._bridge = HtmlBridge(self)
        self._bridge.event_received.connect(self._on_event)

        channel = QWebChannel(self._view.page())
        channel.registerObject("bridge", self._bridge)
        self._view.page().setWebChannel(channel)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._view)

        if html_path:
            self.load_html(html_path)

    def _on_event(self, name: str, payload: dict) -> None:
        """Gestisce gli eventi JS lato Python e li ritrasmette verso l'esterno."""
        # Gestione interna della libreria
        if name == "library_request":
            tracks = self._scan_music_library()
            self.send_event("library_update", {"tracks": tracks})

        # Propaga comunque l'evento a chi si è collegato da fuori (se serve)
        self.event_received.emit(name, payload)

    def _scan_music_library(self) -> list[dict[str, Any]]:
        """Legge la cartella music/library e ritorna una lista di tracce."""
        # html_renderer.py sta in: gui/
        base_dir = os.path.dirname(__file__)          # .../gui
        project_root = os.path.dirname(base_dir)      # .../ (root progetto)
        music_dir = os.path.join(project_root, "music", "library")

        exts = {".mp3", ".wav", ".flac", ".ogg"}
        tracks: list[dict[str, Any]] = []

        if not os.path.isdir(music_dir):
            return tracks

        for filename in sorted(os.listdir(music_dir)):
            name, ext = os.path.splitext(filename)
            if ext.lower() not in exts:
                continue

            tracks.append(
                {
                    "id": name,          # es: "songs"
                    "title": name,       # titolo mostrato
                    "artist": "",        # per ora vuoto
                    "duration": "",      # potresti riempirlo con mutagen ecc.
                    "filename": filename,
                }
            )

        return tracks


    @property
    def view(self) -> QWebEngineView:
        return self._view

    def load_html(self, html_path: str) -> None:
        """Load an HTML file from disk."""
        absolute_path = os.path.abspath(html_path)
        url = QUrl.fromLocalFile(absolute_path)
        self._view.setUrl(url)

    def send_event(self, name: str, payload: Dict[str, Any] | None = None) -> None:
        """Invoke the JavaScript dispatcher with a JSON payload."""
        payload = payload or {}
        script = (
            "window.__pyBridgeDispatch && window.__pyBridgeDispatch("
            f"{json.dumps(name)}, {json.dumps(payload)});"
        )
        self._view.page().runJavaScript(script)

    def set_html(self, html: str) -> None:
        """Directly set inline HTML content."""
        self._view.setHtml(html)

