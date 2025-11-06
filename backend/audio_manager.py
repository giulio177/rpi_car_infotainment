# backend/audio_manager.py

import subprocess
import re
from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot

from .media_info import (
    get_album_art_data_url,
    get_lyrics,
    load_local_placeholder_data_url,
)


# Questa classe farà il lavoro bloccante in un thread separato.
class MetadataWorker(QObject):
    # Segnale per comunicare i risultati: (data_url_copertina, testo_canzone)
    finished = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()
        self._placeholder_art = load_local_placeholder_data_url(
            "gui/html/assets/media/album_placeholder.svg"
        )

    @pyqtSlot(str, str)
    def do_work(self, title, artist):
        """
        Questo è lo slot che riceve il lavoro da fare.
        Contiene le chiamate di rete bloccanti.
        """
        print(f"[Worker Thread] Ricevuto lavoro: {artist} - {title}")

        art_data_url = get_album_art_data_url(title, artist)
        if not art_data_url:
            art_data_url = self._placeholder_art or ""
        lyrics = get_lyrics(title, artist)

        # Emette i risultati quando ha finito
        self.finished.emit(art_data_url, lyrics)


class AudioManager(QObject):
    """
    Manages system audio by controlling the default PipeWire mixer ('Master')
    using the 'amixer' command-line utility.
    """
    
    # Segnale per dire al worker di iniziare a lavorare
    start_work = pyqtSignal(str, str)

    # Nuovo segnale che l'AudioManager emetterà quando i dati sono pronti
    metadata_ready = pyqtSignal(str, str)

    # Come hai scoperto, il controllo creato da PipeWire si chiama "Master".
    MIXER_CONTROL = "Master"

    def __init__(self):
        super().__init__()
        
        # --- Creazione del thread e del worker una sola volta ---
        self.worker_thread = QThread()
        self.worker = MetadataWorker()
        
        # Sposta il worker sul thread
        self.worker.moveToThread(self.worker_thread)
        
        # --- Connessioni permanenti ---
        # 1. Quando diciamo al worker di partire, lui esegue do_work
        self.start_work.connect(self.worker.do_work)
        
        # 2. Quando il worker finisce, i suoi risultati vengono emessi dal segnale di AudioManager
        self.worker.finished.connect(self.metadata_ready)
        
        # 3. Gestisci la pulizia quando l'applicazione si chiude
        self.worker_thread.finished.connect(self.worker.deleteLater)
        
        # Avvia il thread. Rimarrà in attesa di lavoro.
        self.worker_thread.start()
        print("[AudioManager] Worker thread avviato e in attesa di lavoro.")


    def request_media_info(self, title, artist):
        """
        Invia un nuovo lavoro al worker esistente.
        Questa funzione è ora molto semplice e sicura.
        """
        # Emette un segnale per dire al worker di iniziare a lavorare con i nuovi dati.
        # Questa operazione è asincrona e non blocca nulla.
        self.start_work.emit(title, artist)

    def cleanup(self):
        """Metodo da chiamare alla chiusura dell'app per pulire il thread."""
        print("[AudioManager] Pulizia del worker thread...")
        if self.worker_thread.isRunning():
            self.worker_thread.quit()
            self.worker_thread.wait(2000) # Attendi max 2 secondi

    def on_worker_finished(self, cover_url, lyrics):
        """
        Questo slot viene eseguito quando il worker ha finito.
        Emette il segnale pubblico che la UI sta ascoltando.
        """
        print("[AudioManager] Worker ha finito. Emetto il segnale metadata_ready.")
        self.metadata_ready.emit(cover_url, lyrics)

    def _run_amixer_command(self, args):
        """Helper function to run amixer commands on the default card."""
        # Non specifichiamo una card (-c) per operare sul dispositivo di default,
        # che è esattamente quello che PipeWire ci presenta.
        command = ["amixer"] + args
        try:
            return subprocess.check_output(
                command, stderr=subprocess.DEVNULL, text=True, timeout=3
            )
        except FileNotFoundError:
            print("ERROR: 'amixer' command not found. Is alsa-utils installed?")
            return None
        except Exception as e:
            print(f"ERROR: Unexpected error running amixer for control '{self.MIXER_CONTROL}': {e}")
            return None

    def set_volume(self, level_percent):
        """Sets the system volume for the 'Master' control."""
        if not 0 <= level_percent <= 100:
            print(f"ERROR: Invalid volume level {level_percent}.")
            return False

        print(f"AudioManager: Setting volume to {level_percent}% using 'amixer'")
        args = ["sset", self.MIXER_CONTROL, f"{level_percent}%"]
        result = self._run_amixer_command(args)
        return result is not None

    def set_mute(self, muted: bool):
        """Mutes or unmutes the 'Master' control."""
        state = "mute" if muted else "unmute"
        print(f"AudioManager: Setting mute state to {state} using 'amixer'")
        args = ["sset", self.MIXER_CONTROL, state]
        result = self._run_amixer_command(args)
        return result is not None

    def get_volume(self):
        """Gets the current volume percentage for the 'Master' control."""
        args = ["sget", self.MIXER_CONTROL]
        output = self._run_amixer_command(args)
        if output:
            match = re.search(r"\[(\d+)%\]", output)
            if match:
                return int(match.group(1))
        return None

    def get_mute_status(self):
        """Checks if the 'Master' control is muted."""
        args = ["sget", self.MIXER_CONTROL]
        output = self._run_amixer_command(args)
        if output:
            match = re.search(r"\[(on|off)\]", output)
            if match:
                # 'off' in amixer significa mutato
                is_muted = match.group(1) == "off"
                return is_muted
        return None
