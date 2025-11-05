# backend/airplay_manager.py
import subprocess
import os
import signal

class AirPlayManager:
    def __init__(self):
        self.process = None
        # Definiamo un percorso per uno script che avvierà rpiplay
        self.script_path = "/home/pi/rpi_car_infotainment/scripts/start_airplay.sh"

    def start_airplay(self):
        """Avvia uxplay in una finestra ridimensionata."""
        if self.is_running():
            print("AirPlay è già in esecuzione.")
            return

        print("Avvio del mirroring AirPlay (uxplay in finestra)...")
        try:
            env = os.environ.copy()
            env['DISPLAY'] = ':0'
            env['XAUTHORITY'] = '/home/pi/.Xauthority'

            self.process = subprocess.Popen(
                ["/home/pi/rpi_car_infotainment/scripts/start_airplay_embed.sh"],
                env=env,
                shell=False,
                preexec_fn=os.setsid
            )
            print(f"Comando di avvio inviato. PID: {self.process.pid}")
        except Exception as e:
            print(f"ERRORE: Impossibile avviare uxplay: {e}")


    def stop_airplay(self):
        """Ferma il processo RPiPlay in modo robusto."""
        if not self.is_running():
            print("AirPlay non è in esecuzione o già fermato.")
            return

        print("Arresto del servizio di mirroring AirPlay...")
        try:
            # Invece di pkill, terminiamo l'intero gruppo di processi avviato dalla shell.
            # os.setsid nel Popen è fondamentale perché questo funzioni.
            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            print("Segnale SIGTERM inviato al gruppo di processi di RPiPlay.")
            self.process.wait(timeout=2) # Attendi che termini
        except subprocess.TimeoutExpired:
            print("Il processo non è terminato, forzo la chiusura (SIGKILL)...")
            os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
        except Exception as e:
            print(f"ERRORE: Impossibile terminare RPiPlay: {e}")
        finally:
            self.process = None

    def is_running(self):
        """
        Controlla se il processo RPiPlay è in esecuzione usando l'oggetto Popen.
        Questo è molto più affidabile di pgrep.
        """
        # --- LOGICA COMPLETAMENTE NUOVA ---
        if self.process is None:
            return False
        
        # poll() restituisce None se il processo è attivo, altrimenti il codice di uscita.
        return self.process.poll() is None
        

    def cleanup(self):
        """Metodo di pulizia da chiamare alla chiusura dell'app."""
        self.stop_airplay()