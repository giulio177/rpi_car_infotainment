"""Reusable helpers to embed HTML-based screens inside the PyQt6 application."""

from __future__ import annotations

import json
import os
from typing import Any, Dict
from mutagen import File as MutagenFile
import math

from PyQt6.QtCore import QObject, QUrl, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import QVBoxLayout, QWidget

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebChannel import QWebChannel
except ImportError as exc:  # pragma: no cover - handled at runtime
    raise ImportError(
        "PyQt6-WebEngine is required to use the HTML rendering helpers."
    ) from exc

import logging
from mutagen import File as MutagenFile
from mutagen.easyid3 import EasyID3

logging.basicConfig(
    level=logging.DEBUG,
    format="[HTML Renderer] %(levelname)s: %(message)s"
)


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
            logging.debug("Handling library_request...")
            tracks = self._scan_music_library()
            logging.debug(f"Sending library_update with {len(tracks)} tracks")
            self.send_event("library_update", {"tracks": tracks})
            return

        # Propaga comunque l'evento a chi si è collegato da fuori (se serve)
        self.event_received.emit(name, payload)

    def _scan_music_library(self) -> list[dict[str, Any]]:
        """Legge la cartella music/library e ritorna una lista di tracce."""
        logging.debug("Scanning music library...")

        # html_renderer.py sta in: gui/
        base_dir = os.path.dirname(__file__)          # .../gui
        project_root = os.path.dirname(base_dir)      # .../ (root progetto)
        music_dir = os.path.join(project_root, "music", "library")

        logging.debug(f"Music folder resolved to: {music_dir}")

        exts = {".mp3", ".wav", ".flac", ".ogg"}
        tracks: list[dict[str, Any]] = []

        if not os.path.isdir(music_dir):
            logging.error(f"Music directory not found: {music_dir}")
            return tracks

        for filename in sorted(os.listdir(music_dir)):
            logging.debug(f"Found file: {filename}")

            name, ext = os.path.splitext(filename)
            if ext.lower() not in exts:
                logging.debug(f"Skipping unsupported extension: {ext}")
                continue

            full_path = os.path.join(music_dir, filename)
            logging.debug(f"Processing audio file: {full_path}")



            
            # ---------- DURATA ----------
            duration = ""
            try:
                audio = MutagenFile(full_path)
                logging.debug(f"Mutagen loaded: {audio}")

                if audio is not None and hasattr(audio, "info") and hasattr(audio.info, "length"):
                    seconds = int(audio.info.length)
                    minutes = seconds // 60
                    sec = seconds % 60
                    duration = f"{minutes}:{sec:02d}"
                    logging.debug(f"Duration computed: {duration}")
                else:
                    logging.warning(f"No duration info for file: {filename}")
            except Exception as e:
                logging.error(f"Error reading {filename} with mutagen: {e}")

            
            
            # ---------- METADATA (title, artist, album) ----------
            title = name
            artist = ""
            album = ""

            try:
                if ext.lower() == ".mp3":
                    # per gli MP3 usiamo EasyID3 (sono quelli su cui hai scritto i tag)
                    try:
                        tags = EasyID3(full_path)
                        logging.debug(f"EasyID3 tags for {filename}: {dict(tags)}")

                        if "title" in tags and tags["title"]:
                            title = tags["title"][0]
                        if "artist" in tags and tags["artist"]:
                            artist = tags["artist"][0]
                        if "album" in tags and tags["album"]:
                            album = tags["album"][0]
                    except Exception as e:
                        logging.warning(f"No EasyID3 tags for {filename}: {e}")
                else:
                    # per altri formati proviamo a leggere i tag generici
                    if audio is not None and audio.tags:
                        tags = audio.tags
                        logging.debug(f"Generic tags for {filename}: {tags}")

                        # questi campi dipendono dal formato; fallback semplice
                        title = str(tags.get("title", [title])[0]) if "title" in tags else title
                        artist = str(tags.get("artist", [""])[0]) if "artist" in tags else artist
                        album = str(tags.get("album", [""])[0]) if "album" in tags else album

            except Exception as e:
                logging.error(f"Error reading metadata from {filename}: {e}")

            track = {
                "id": name,          # es: "songs"
                "title": title,       # titolo mostrato
                "artist": artist,        # per ora vuoto
                "album": album,
                "duration": duration,      # potresti riempirlo con mutagen ecc.
                "filename": filename,
            }

            logging.debug(f"Track entry: {track}")
            tracks.append(track)

        logging.debug(f"Library scan complete: {len(tracks)} tracks found")
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

