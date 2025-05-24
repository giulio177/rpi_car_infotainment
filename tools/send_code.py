#!/usr/bin/env python3

import time
import logging
import argparse
import pathlib
import sys

# Add the project root directory to the Python path
script_dir = pathlib.Path(__file__).parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

from rpi_rf import RFDevice

# --- Configurazione GPIO Trasmettitore ---
TX_GPIO = 24 # GPIO collegato al pin DATA del trasmettitore FS1000A
# -----------------------------------------

# Configura il logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Parser per argomenti da riga di comando (opzionale ma utile)
parser = argparse.ArgumentParser(description='Invia codice RF usando rpi-rf')
parser.add_argument('-g', '--gpio', type=int, default=TX_GPIO, help=f'GPIO pin per il trasmettitore (default: {TX_GPIO})')
parser.add_argument('-c', '--code', type=int, default=12345, help='Codice (intero) da inviare (default: 12345)')
parser.add_argument('-p', '--pulselength', type=int, default=350, help='Lunghezza impulso in microsecondi (default: 350)')
parser.add_argument('-l', '--protocol', type=int, default=1, help='Protocollo (default: 1)')
parser.add_argument('-r', '--repeat', type=int, default=10, help='Numero di ripetizioni trasmissione (default: 10)')
args = parser.parse_args()


# Inizializza RFDevice per il trasmettitore
# Usare pigpio come backend è generalmente preferito per la precisione
try:
    rfdevice = RFDevice(args.gpio,
                        tx_proto=args.protocol,
                        tx_pulselength=args.pulselength,
                        tx_repeat=args.repeat,
			#log_level=logging.DEBUG # Decommenta per debug dettagliato
                        )


except Exception as e:
	logging.error(f"Errore durante l'inizializzazione di RFDevice (pigpio è attivo con flag -n?): {e}")
	exit(1)

# Abilita la trasmissione
rfdevice.enable_tx()

logging.info(f"Invio codice: {args.code} [Protocollo: {args.protocol}, Lunghezza Impulso: {args.pulselength} us, GPIO: {args.gpio}, Ripetizioni: {args.repeat}]")

# Invia il codice
start_time = time.time()
rfdevice.tx_code(args.code)
end_time = time.time()

logging.info(f"Codice inviato in {end_time - start_time:.2f} secondi.")

# Pulisci le risorse GPIO
rfdevice.cleanup()
logging.info("GPIO puliti. Uscita.")
