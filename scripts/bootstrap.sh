#!/bin/bash
# bootstrap.sh - Prepara l'ambiente per l'installer grafico
set -e

if [[ "$EUID" -ne 0 ]]; then
  echo "Per favore esegui con sudo: sudo ./bootstrap.sh"
  exit 1
fi

echo ">>> Installazione dipendenze grafiche minime..."
apt update
# Installiamo Python3, Pip e le librerie SDL2 per PyGame su Framebuffer
apt install -y python3-pip python3-pygame libsdl2-2.0-0 libsdl2-image-2.0-0 libsdl2-ttf-2.0-0

# Opzionale: installa whiptail se servisse per debug, ma qui usiamo pygame
echo ">>> Avvio Installer Grafico Touch..."

# Passiamo il nome dell'utente reale (SUDO_USER) allo script python
# Assicurati che installer_gui.py sia nella stessa cartella
python3 installer_gui.py