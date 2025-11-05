#!/bin/bash
echo "Script avviato con DISPLAY=$DISPLAY" >> /tmp/airplay_debug.log

export DISPLAY=:0            # <-- aggiusta/rimuovi se già corretto
export XAUTHORITY=/home/pi/.Xauthority  # <-- spesso necessario su Lite

# Dimensioni e posizione del "riquadro"
WIDTH=640
HEIGHT=360
X=100
Y=100

# Uccidi eventuali istanze
pkill -f uxplay

# Avvia uxplay
uxplay -n "Car-Display" -r >/tmp/uxplay.log 2>&1 &
PID=$!

sleep 2
# Sposta e ridimensiona
xdotool search --sync --name "Car-Display" windowmove $X $Y windowsize $WIDTH $HEIGHT