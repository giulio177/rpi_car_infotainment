#!/usr/bin/env python3

import time
import logging
import argparse
import signal # Per gestire Ctrl+C
from rpi_rf import RFDevice

# --- Configurazione GPIO Ricevitore ---
RX_GPIO = 23 # GPIO collegato al pin DATA del ricevitore FS1000A (tramite level shifter se necessario!)
# --------------------------------------

# Configura il logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__) # Ottieni un logger specifico

# Variabile globale per controllare il loop principale
running = True

# Signal handler per uscita pulita
def handle_exit(sig, frame):
    global running
    logger.info("Segnale ricevuto, arresto listener...")
    running = False
    # Aggiungiamo un piccolo ritardo per permettere al loop di terminare
    time.sleep(0.1)

# Registra i signal handler
signal.signal(signal.SIGINT, handle_exit)  # Gestisce Ctrl+C
signal.signal(signal.SIGTERM, handle_exit) # Gestisce segnale di terminazione

# Parser per argomenti (opzionale)
parser = argparse.ArgumentParser(description='Ricevi codici RF usando rpi-rf')
parser.add_argument('-g', '--gpio', type=int, default=RX_GPIO, help=f'GPIO pin per il ricevitore (default: {RX_GPIO})')
args = parser.parse_args()

# Inizializza RFDevice per il ricevitore
# Usare pigpio come backend è generalmente preferito
try:
    rfdevice = RFDevice(args.gpio,
                        # tx_gpio=None, # Non trasmettiamo da qui
                        # Specifica parametri noti se disponibili:
                        # rx_pulselength=known_pulselength,
                        # rx_proto=known_protocol,
			rx_tolerance=80, # Tolleranza sulla lunghezza impulso (default 80)
                        # log_level=logging.DEBUG, # Decommenta per debug dettagliato
                        )

except Exception as e:
	logging.error(f"Errore durante l'inizializzazione di RFDevice (pigpio è attivo con flag -n?): {e}")
	exit(1)

# Abilita la ricezione
rfdevice.enable_rx()

logger.info(f"In ascolto per codici RF su GPIO {rfdevice.gpio}...")
logger.info("Premi Ctrl+C per uscire.")

# --- Loop Principale ---
last_code_timestamp = 0
last_code = None
debounce_interval = 0.3 # Secondi per ignorare codici duplicati

try:
    while running:
	# Controlla se è stato ricevuto un codice
	# rfdevice.rx_code_timestamp si aggiorna solo quando viene ricevuto un codice VALIDO
        # secondo i parametri (protocol, pulselength, tolerance)
        if rfdevice.rx_code_timestamp != last_code_timestamp:
            timestamp_received = time.time() # Registriamo l'ora locale di ricezione
            code = rfdevice.rx_code
            pulselength = rfdevice.rx_pulselength
            protocol = rfdevice.rx_proto
	
	
 	    # De-bounce: Ignora se lo stesso codice è stato ricevuto molto di recente
            if code != last_code or (timestamp_received - last_code_timestamp > debounce_interval):
                 logger.info(f"Ricevuto: Code={code}, Pulselength={pulselength} us, Protocol={protocol}")
                 last_code = code
                 # Usiamo il timestamp locale per il debounce
                 last_code_timestamp = timestamp_received
            else:
                 # logger.debug(f"Debounced duplicate code: {code}") # Decommenta per debug
                 last_code_timestamp = timestamp_received # Aggiorna comunque per il prossimo debounce

        # Piccolo sleep per ridurre l'uso della CPU
        time.sleep(0.01)

except Exception as e:
    # Gestisce altri errori imprevisti durante il loop
    logger.error(f"Errore durante l'esecuzione: {e}")

finally:
    # Assicura la pulizia delle risorse anche in caso di errore o uscita normale
    logger.info("Pulizia GPIO...")
    if 'rfdevice' in locals() and rfdevice is not None:
         rfdevice.cleanup()
    logger.info("Uscita dallo script ricevitore.")
