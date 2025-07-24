#!/bin/bash
# Questo script avvia il mirroring AirPlay sul display principale

# Assicura che RPiPlay sappia su quale display disegnarsi
export DISPLAY=:0

# Attendi in un ciclo finché il server X non è pronto.
# Questo è importante se lo script viene chiamato subito all'avvio del sistema.
while ! xdpyinfo -display $DISPLAY >/dev/null 2>&1; do
  sleep 1
done

echo "Server X trovato. Avvio di RPiPlay in fullscreen..."
# Avvia RPiPlay in fullscreen.
# -n: Nome che appare sull'iPhone
# -f: Avvia in fullscreen
exec rpiplay -n "Car-Display" -f