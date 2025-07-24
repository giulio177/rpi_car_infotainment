#!/bin/bash

# ===================================================================
# Script per avviare un'applicazione Qt/PySide su Raspberry Pi
# direttamente sul framebuffer (senza desktop/X server) con
# supporto per il touchscreen.
# ===================================================================

# Interrompe lo script in caso di errori
set -e

# --- CONFIGURAZIONE ---
# --- PERCORSI ASSOLUTI PER LA MASSIMA AFFIDABILITÀ CON SYSTEMD ---
APP_DIR="/home/pi/rpi_car_infotainment"
VENV_DIR="/home/pi/rpi_car_infotainment/venv"
# TOUCHSCREEN_DEVICE="/dev/input/touchscreen"  # È consigliato usare il link udev
TOUCHSCREEN_DEVICE="/dev/input/event0"   # Usa questo se non hai la regola udev

# In alternativa, puoi usare il percorso diretto (ma potrebbe cambiare al riavvio):
# TOUCHSCREEN_DEVICE="/dev/input/event1"

LOG_FILE="/tmp/app_output.log"


# --- FUNZIONI ---

# Funzione per attivare l'ambiente virtuale Python
activate_venv() {
    if [ -d "$VENV_DIR" ] && [ -f "$VENV_DIR/bin/activate" ]; then
        echo "Attivazione ambiente virtuale: $VENV_DIR"
        source "$VENV_DIR/bin/activate"
    else
        echo "ERRORE: Ambiente virtuale non trovato in $VENV_DIR"
        exit 1
    fi
}

# Funzione per avviare l'applicazione principale
start_application() {
    echo "Avvio dell'applicazione principale..."
    cd "$APP_DIR"

    # --- CONFIGURAZIONE FONDAMENTALE DI QT ---
    # Imposta la piattaforma Qt per usare:
    # - linuxfb: per disegnare direttamente sul display (framebuffer)
    # - evdev: per gestire l'input dal dispositivo touchscreen specificato
    export QT_QPA_PLATFORM="linuxfb:fb=/dev/fb0;evdev-touch-screen=${TOUCHSCREEN_DEVICE}"

    # Forza l'applicazione ad avviarsi in modalità fullscreen
    export QT_QPA_FB_FORCE_FULLSCREEN=1

    # svuota log precedente (opzionale)
    > "$LOG_FILE"

    # Esegui l'applicazione Python
    echo "Esecuzione di: $VENV_DIR/bin/python3 main.py"
    # --- MODIFICA CHIAVE: USA IL PERCORSO COMPLETO AL PYTHON DEL VENV ---
    "$VENV_DIR/bin/python3" main.py 2>&1 | tee "$LOG_FILE"
}


# --- ESECUZIONE DELLO SCRIPT ---

# Pulisci lo schermo e nascondi il cursore del terminale
#clear
#echo -e "\033[?25l"

echo "=== Avvio RPi Car Infotainment Launcher ==="

# Attiva l'ambiente virtuale
activate_venv

# Avvia l'applicazione
start_application

# Ripristina il cursore all'uscita (opzionale, utile per il debug)
echo -e "\033[?25h"
echo "Applicazione terminata."