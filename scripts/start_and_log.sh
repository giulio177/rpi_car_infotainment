#!/bin/bash

# --- SCRIPT DI DEBUGGING PER CATTURARE TUTTO L'OUTPUT ---

LOG_FILE="/home/pi/rpi_car_infotainment/docs/infotainment_boot.log"

# Pulisci il log precedente ad ogni avvio
echo "" > $LOG_FILE
echo "--- NUOVO AVVIO: $(date) ---" >> $LOG_FILE
echo "Script 'start_and_log.sh' in esecuzione." >> $LOG_FILE

# Imposta le variabili d'ambiente necessarie
export DISPLAY=:0
export XAUTHORITY=/home/pi/.Xauthority
export QT_QPA_PLATFORM="linuxfb:evdev-touch-screen=/dev/input/touchscreen"
export QT_QPA_FB_FORCE_FULLSCREEN=1
export XDG_RUNTIME_DIR=/run/user/1000

echo "Variabili d'ambiente impostate:" >> $LOG_FILE
env >> $LOG_FILE
echo "---" >> $LOG_FILE

# La directory di lavoro
cd /home/pi/rpi_car_infotainment

# Percorso del python del venv
PYTHON_EXEC="/home/pi/rpi_car_infotainment/venv/bin/python3"
MAIN_SCRIPT="/home/pi/rpi_car_infotainment/main.py"

echo "Avvio dell'applicazione Python: $PYTHON_EXEC $MAIN_SCRIPT" >> $LOG_FILE
echo "==========================================================" >> $LOG_FILE

# --- COMANDO CHIAVE ---
# 'exec' sostituisce il processo dello script con quello di python.
# '2>&1' reindirizza l'errore (stderr) sull'output normale (stdout).
# '>> $LOG_FILE' appende tutto l'output al nostro file di log.
exec $PYTHON_EXEC $MAIN_SCRIPT >> $LOG_FILE 2>&1
