#!/bin/bash
# bootstrap.sh - Prepara l'ambiente grafico KMSDRM + Touch su RPi Lite
set -e

# 1. Controllo Root
if [[ "$EUID" -ne 0 ]]; then
  echo "Per favore esegui con sudo: sudo ./bootstrap.sh"
  exit 1
fi

USER_NAME="${SUDO_USER:-pi}"
echo ">>> Utente rilevato: $USER_NAME"

# 2. Installazione Dipendenze (Grafica + Input)
echo ">>> Installazione dipendenze..."
apt update
apt install -y \
    python3-pip python3-pygame \
    libsdl2-2.0-0 libsdl2-image-2.0-0 libsdl2-ttf-2.0-0 \
    libgles2 libegl1 libgl1-mesa-dri libgbm1 libglapi-mesa libgl1 \
    fonts-liberation \
    evtest input-utils libevdev2

# 3. Permessi Utente (Video + Input)
echo ">>> Configurazione Permessi (video, render, input)..."
usermod -aG video,render,input "$USER_NAME"

# 4. Configurazione Boot (Forza KMS)
echo ">>> Verifica Configurazione Boot (Full KMS)..."
if [[ -f /boot/firmware/config.txt ]]; then CONFIG="/boot/firmware/config.txt"; else CONFIG="/boot/config.txt"; fi

if grep -q "dtoverlay=vc4-fkms-v3d" "$CONFIG"; then
    sed -i 's/dtoverlay=vc4-fkms-v3d/dtoverlay=vc4-kms-v3d/' "$CONFIG"
    echo "Aggiornato driver a Full KMS (vc4-kms-v3d)."
elif ! grep -q "dtoverlay=vc4-kms-v3d" "$CONFIG"; then
    echo "dtoverlay=vc4-kms-v3d" >> "$CONFIG"
    echo "Abilitato driver Full KMS."
fi

# 5. Spegnimento TTY1 (Essenziale per liberare risorse video/input)
echo ">>> Spegnimento TTY1..."
systemctl stop getty@tty1.service || true

echo ">>> Avvio Installer Grafico Touch..."
# Assicurati che installer_gui.py sia nella stessa cartella
python3 installer_gui.py

# Opzionale: ripristina TTY se l'installer esce senza riavviare
echo ">>> Installer terminato. Ripristino TTY1..."
systemctl start getty@tty1.service || true