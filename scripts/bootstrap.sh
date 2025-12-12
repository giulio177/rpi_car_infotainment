#!/bin/bash
# Installa solo il minimo indispensabile per la grafica
sudo apt update
sudo apt install -y python3-pygame libsdl2-2.0-0 libsdl2-image-2.0-0 libsdl2-ttf-2.0-0

echo "Avvio Installer Grafico Touch..."
sudo python3 installer_gui.py
