#!/usr/bin/env bash
set -euo pipefail

###############################################################################
# RPi Car Infotainment installer - Raspberry Pi OS Lite
# - 1 solo reboot finale
# - parametrizzato (utente, path boot, sink audio, ecc.)
# - idempotente quanto basta (non duplica righe se rilanciato)
###############################################################################

# Deve girare come root (es. sudo ./install_rpi_car_infotainment.sh)
if [[ "$EUID" -ne 0 ]]; then
  echo "Questo script va eseguito con sudo o da root."
  exit 1
fi

# Utente "reale" (di solito pi) = quello che ha lanciato sudo
USER_NAME="${SUDO_USER:-pi}"
if ! id "$USER_NAME" >/dev/null 2>&1; then
  echo "Utente $USER_NAME non trovato. Imposta SUDO_USER o modifica lo script."
  exit 1
fi

USER_UID="$(id -u "$USER_NAME")"
USER_HOME="$(getent passwd "$USER_NAME" | cut -d: -f6)"
PROJECT_DIR="$USER_HOME/rpi_car_infotainment"

if [[ ! -d "$PROJECT_DIR" ]]; then
  echo "Directory progetto non trovata: $PROJECT_DIR"
  echo "Clona prima il repository in $USER_HOME."
  exit 1
fi

echo "Utente:       $USER_NAME (UID: $USER_UID)"
echo "Home:         $USER_HOME"
echo "Project dir:  $PROJECT_DIR"
echo

###############################################################################
# 1) Individua la partizione di boot (/boot/firmware vs /boot)
###############################################################################
if [[ -f /boot/firmware/cmdline.txt ]]; then
  BOOT_DIR="/boot/firmware"
elif [[ -f /boot/cmdline.txt ]]; then
  BOOT_DIR="/boot"
else
  echo "Impossibile trovare cmdline.txt (né /boot/firmware né /boot)."
  exit 1
fi

CMDLINE_FILE="$BOOT_DIR/cmdline.txt"
CONFIG_FILE="$BOOT_DIR/config.txt"

echo "Usando BOOT_DIR: $BOOT_DIR"
echo

###############################################################################
# 2) Aggiornamento sistema + pacchetti necessari
###############################################################################
echo ">>> Aggiornamento sistema e installazione pacchetti..."

apt update
apt full-upgrade -y

apt install -y \
  git python3-venv python3-pip \
  ffmpeg \
  pulseaudio pulseaudio-module-bluetooth alsa-utils \
  bluez bluez-tools pi-bluetooth bluez-firmware \
  libfdk-aac2 libavcodec-extra \
  python3-dbus python3-gi gir1.2-glib-2.0 \
  dbus-user-session \
  libminizip1 libxkbfile1 libsnappy1v5 \
  libdbus-1-dev libglib2.0-dev python3-dev \
  build-essential pkg-config 


echo ">>> Pacchetti installati."
echo

###############################################################################
# 3) Configurazione cmdline.txt (quiet, logo, loglevel, cursore)
###############################################################################
echo ">>> Configurazione $CMDLINE_FILE..."

EXTRA_CMDLINE="logo.nologo quiet loglevel=3 vt.global_cursor_default=0"

if ! grep -q "logo.nologo" "$CMDLINE_FILE"; then
  sed -i "1s|\$| ${EXTRA_CMDLINE}|" "$CMDLINE_FILE"
  echo "Aggiunte opzioni extra/logo/log a cmdline.txt."
else
  echo "Opzioni extra già presenti in cmdline.txt, salto."
fi

echo

###############################################################################
# 3.5) Configurazione config.txt (risoluzione HDMI 1024x600)
###############################################################################
echo ">>> Configurazione $CONFIG_FILE (display 1024x600 + fkms)..."

# 1) Sostituisci KMS con FKMS se esiste
if grep -q "dtoverlay=vc4-kms-v3d" "$CONFIG_FILE"; then
  sed -i 's/dtoverlay=vc4-kms-v3d/dtoverlay=vc4-fkms-v3d/' "$CONFIG_FILE"
  echo "Sostituito vc4-kms-v3d con vc4-fkms-v3d."
fi

# 2) Aggiungi FKMS se non è già presente
if ! grep -q "dtoverlay=vc4-fkms-v3d" "$CONFIG_FILE"; then
  echo "dtoverlay=vc4-fkms-v3d" >> "$CONFIG_FILE"
  echo "Aggiunto dtoverlay=vc4-fkms-v3d."
else
  echo "dtoverlay=vc4-fkms-v3d già presente, salto."
fi

# Blocco HDMI per forzare 1024x600 @ 60Hz con CVT custom
HDMI_BLOCK=$(cat << 'EOF'
# RPi Car Infotainment - display 1024x600
hdmi_force_hotplug=1
hdmi_group=2
hdmi_mode=87
hdmi_cvt=1024 600 60 6 0 0 0
EOF
)

# Aggiungi il blocco solo se non già presente
if ! grep -q "hdmi_cvt=1024 600 60 6 0 0 0" "$CONFIG_FILE"; then
  printf "\n%s\n" "$HDMI_BLOCK" >> "$CONFIG_FILE"
  echo "Blocco HDMI 1024x600 aggiunto a config.txt."
else
  echo "Blocco HDMI 1024x600 già presente in config.txt, salto."
fi

echo

###############################################################################
# 4) Abilita audio del Pi in config.txt
###############################################################################
echo ">>> Configurazione $CONFIG_FILE (dtparam=audio=on)..."

if grep -q '^dtparam=audio=' "$CONFIG_FILE"; then
  sed -i 's/^dtparam=audio=.*/dtparam=audio=on/' "$CONFIG_FILE"
else
  echo 'dtparam=audio=on' >> "$CONFIG_FILE"
fi
echo "Audio del Pi abilitato in config.txt."
echo

###############################################################################
# 5) Setup PulseAudio + ALSA + moduli Bluetooth
###############################################################################
echo ">>> Configurazione PulseAudio/ALSA/Bluetooth..."

# Disabilita eventuale pulseaudio di sistema (se non esiste, non è un problema)
systemctl disable --now pulseaudio 2>/dev/null || true

# ALSA → PulseAudio di default
cat >/etc/asound.conf <<'EOF'
pcm.!default pulse
ctl.!default pulse
EOF
echo "/etc/asound.conf configurato per usare PulseAudio."

# Moduli BT in /etc/pulse/default.pa (se non c'è già bluetooth-discover)
if [[ -f /etc/pulse/default.pa ]]; then
  if ! grep -q 'bluetooth-discover' /etc/pulse/default.pa; then
    cat >>/etc/pulse/default.pa <<'EOF'

### Bluetooth A2DP (user instance)
load-module module-bluetooth-policy
load-module module-bluetooth-discover
EOF
    echo "Aggiunti moduli Bluetooth a /etc/pulse/default.pa."
  else
    echo "Moduli Bluetooth già presenti in /etc/pulse/default.pa, salto."
  fi
else
  # File non esistente: creiamo mini default.pa con solo moduli BT
  cat >/etc/pulse/default.pa <<'EOF'
### Minimal PulseAudio config with Bluetooth

load-module module-bluetooth-policy
load-module module-bluetooth-discover
EOF
  echo "Creato /etc/pulse/default.pa minimale con moduli Bluetooth."
fi
echo

###############################################################################
# 6) Configurazione BlueZ e FIX HARDWARE (Sblocco UART/RFKill)
###############################################################################
echo ">>> Configurazione Bluetooth (Hardware & Software)..."

# --- 6.1 FIX HARDWARE: UART e RFKill (Risolve 'Failed to set power on') ---

# 1. Rimuove blocco 'disable-bt' se presente in config.txt
if grep -q "dtoverlay=disable-bt" "$CONFIG_FILE"; then
    sed -i '/dtoverlay=disable-bt/d' "$CONFIG_FILE"
    echo "Rimosso dtoverlay=disable-bt da config.txt."
fi

# 2. Assicura che la UART sia abilitata (Necessario per il chip BT del Pi)
if ! grep -q "enable_uart=1" "$CONFIG_FILE"; then
    echo "enable_uart=1" >> "$CONFIG_FILE"
    echo "Abilitato enable_uart=1 in config.txt."
fi

# 3. Sblocco RFKill (Soft Block)
if command -v rfkill &> /dev/null; then
    rfkill unblock bluetooth || true
    echo "RFKill sbloccato."
fi

# 4. Assicura che il servizio driver UART (hciuart) sia attivo
systemctl enable hciuart
systemctl restart hciuart || true

# --- 6.2 Configurazione main.conf ---
echo ">>> Configurazione /etc/bluetooth/main.conf..."

# Creazione file base se manca
if [[ ! -f /etc/bluetooth/main.conf ]]; then
    echo "[General]" > /etc/bluetooth/main.conf
elif ! grep -q '^\[General\]' /etc/bluetooth/main.conf; then
    sed -i '1i[General]' /etc/bluetooth/main.conf
fi

# Funzione helper
set_bt_conf() {
    local key="$1"
    local val="$2"
    local file="/etc/bluetooth/main.conf"
    if grep -q "^$key" "$file"; then
        sed -i "s/^$key.*/$key = $val/" "$file"
    else
        sed -i "/^\[General\]/a $key = $val" "$file"
    fi
}

# CONFIGURAZIONE STRATEGICA
set_bt_conf "Class" "0x200420"             # Car Audio
set_bt_conf "DiscoverableTimeout" "30"     # 30s Visibilità (Sicurezza)
set_bt_conf "PairableTimeout" "0"          # Sempre accoppiabile se visibile
set_bt_conf "JustWorksRepairing" "always"  # Forza No PIN
set_bt_conf "AutoEnable" "true"            # Acceso al boot
set_bt_conf "ControllerMode" "bredr"       # Modalità classica (A2DP)
set_bt_conf "Name" "RPi-Infotainment"

echo "/etc/bluetooth/main.conf configurato: Just Works, UART Fix applicato."
echo

###############################################################################
# 7) Agente Bluetooth Auto-Pairing (bluez-tools / NoInputNoOutput)
###############################################################################
echo ">>> Installazione agente Bluetooth 'Just Works' (bluez-tools)..."

# 1. Installazione bluez-tools (Agente C++)
if ! dpkg -l | grep -q bluez-tools; then
    apt install -y bluez-tools
fi

# 2. Creazione Servizio 'Porte Aperte'
cat >/etc/systemd/system/bt-auto-pair.service <<EOF
[Unit]
Description=Bluetooth Auto-Accept Agent (No PIN, No Confirmation)
After=bluetooth.service
Requires=bluetooth.service

[Service]
Type=simple
# -c NoInputNoOutput: Dice al telefono che non c'è tastiera/schermo
# L'agente accetta AUTOMATICAMENTE le richieste
ExecStart=/usr/bin/bt-agent -c NoInputNoOutput
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now bt-auto-pair.service

echo "Nuovo agente 'bt-auto-pair' installato e attivo."
echo

###############################################################################
# 8) Configurazione spinte tramite btmgmt
###############################################################################
echo ">>> Configurazione controller Bluetooth (btmgmt)..."

# Forza capabilities I/O basse per evitare richieste PIN
btmgmt io-cap 3       || true
btmgmt bondable on    || true
btmgmt pairable on    || true
btmgmt bredr on       || true
# NON mettiamo 'discoverable on', lo farà l'app
btmgmt connectable on || true

# Riavvio finale dello stack bluetooth per applicare tutto
systemctl restart bluetooth

echo "btmgmt configurato."
echo

###############################################################################
# 9) Gruppi utente per accesso a video/input/audio
###############################################################################
echo ">>> Aggiunta utente $USER_NAME a gruppi video,input (se necessario)..."

usermod -aG video,input "$USER_NAME" || true
echo "Gruppi aggiornati (effettivi al prossimo login/servizio)."
echo

###############################################################################
# 10) Creazione venv Python e install requisiti (come utente normale)
###############################################################################
echo ">>> Creazione virtualenv e installazione requirements.txt..."

sudo -u "$USER_NAME" bash -lc "
  set -e
  cd '$PROJECT_DIR'
  python3 -m venv venv
  source venv/bin/activate
  pip install --upgrade pip
  pip install -r requirements.txt
"

echo "Virtualenv e dipendenze Python installate."
echo

###############################################################################
# 11) Setup Audio: PulseAudio, ALSA Default e Loopback Bluetooth
###############################################################################
echo ">>> Configurazione Audio (Forzatura Jack Analogico)..."

# --- NUOVO BLOCCO: Ottimizzazione Qualità Audio ---
echo "Configurazione /etc/pulse/daemon.conf per audio alta qualità..."
cat >/etc/pulse/daemon.conf <<'EOF'
# Priorità Processo
high-priority = yes
nice-level = -11
realtime-scheduling = yes
realtime-priority = 5

# Qualità Audio (Stabile per RPi 4)
resample-method = speex-float-1
avoid-resampling = false

# Formato e Frequenza (Match iPhone/Android standard)
default-sample-format = s16le
default-sample-rate = 44100
alternate-sample-rate = 48000
default-sample-channels = 2

# Buffer (Bilanciato per Bluetooth)
default-fragments = 4
default-fragment-size-msec = 25
EOF
echo "daemon.conf ottimizzato."

# 2. Reset configurazione PulseAudio (per cancellare vecchie memorie HDMI)
rm -rf "$USER_HOME/.config/pulse"
echo "Configurazione PulseAudio pulita."

# 3. Imposta volume Hardware (PCM su Card 1) al 100%
# Usiamo 'amixer -c 1' per essere sicuri di colpire la scheda giusta
amixer -c 1 set PCM 100% unmute || true
echo "Volume PCM alzato al 100%."

# 4. Linger e Systemd User (come prima)
loginctl enable-linger "$USER_NAME" || true
systemctl start "user@${USER_UID}.service" || true

# 5. Avvia PulseAudio (necessario per configurare il loopback)
sudo -u "$USER_NAME" XDG_RUNTIME_DIR="/run/user/$USER_UID" systemctl --user enable pulseaudio 2>/dev/null || true
sudo -u "$USER_NAME" XDG_RUNTIME_DIR="/run/user/$USER_UID" systemctl --user start pulseaudio 2>/dev/null || true
# Aspetta che PulseAudio sia su
sleep 5

# 6. Script Loopback DINAMICO (Migliorato)
# Questo script cerca il sink ogni volta che parte, così non sbaglia mai nome
mkdir -p "$USER_HOME/.local/bin" "$USER_HOME/.config/systemd/user"

cat >"$USER_HOME/.local/bin/bt-loopback.sh" <<'SCRIPT_EOF'
#!/bin/bash
set -euo pipefail

# Funzione per trovare il sink analogico ATTUALE
find_sink() {
    # Cerca il sink che contiene "analog-stereo" o "Headphones"
    TARGET_SINK=$(pactl list sinks short | grep -E "analog-stereo|Headphones" | cut -f2 | head -n1)
    
    # Se non lo trova, usa il default (che grazie a .asoundrc dovrebbe essere giusto)
    if [[ -z "$TARGET_SINK" ]]; then
        TARGET_SINK="@DEFAULT_SINK@"
    fi
    echo "$TARGET_SINK"
}

# Funzione per collegare il bluetooth al sink
try_connect() {
    SINK=$(find_sink)
    # Disabilita profilo HDMI (Card 0) per sicurezza, se esiste
    pactl set-card-profile 0 off 2>/dev/null || true
    
    # Cerca sorgenti bluetooth
    pactl list sources short | grep "bluez_source" | while read -r line; do
        SRC_ID=$(echo "$line" | cut -f2)
        # Evita duplicati
        if ! pactl list modules short | grep -q "source=$SRC_ID sink=$SINK"; then
            echo "Loopback: $SRC_ID -> $SINK"
            pactl load-module module-loopback source="$SRC_ID" sink="$SINK" latency_msec=200
        fi
    done
}

# Tentativo all'avvio
try_connect

# Ascolta eventi (connessione telefono)
pactl subscribe | while read -r line; do
    if echo "$line" | grep -qE "new|put"; then
        if echo "$line" | grep -qE "source|card"; then
            sleep 2
            try_connect
        fi
    fi
done
SCRIPT_EOF

chown "$USER_NAME:$USER_NAME" "$USER_HOME/.local/bin/bt-loopback.sh"
chmod +x "$USER_HOME/.local/bin/bt-loopback.sh"

# 7. Servizio Systemd per il Loopback
cat >"$USER_HOME/.config/systemd/user/bt-loopback.service" <<EOF
[Unit]
Description=Bluetooth Loopback Automation
After=pulseaudio.service bluetooth.target
Wants=pulseaudio.service

[Service]
ExecStart=$USER_HOME/.local/bin/bt-loopback.sh
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
EOF

chown "$USER_NAME:$USER_NAME" "$USER_HOME/.config/systemd/user/bt-loopback.service"

sudo -u "$USER_NAME" XDG_RUNTIME_DIR="/run/user/$USER_UID" systemctl --user daemon-reload
sudo -u "$USER_NAME" XDG_RUNTIME_DIR="/run/user/$USER_UID" systemctl --user enable bt-loopback.service
sudo -u "$USER_NAME" XDG_RUNTIME_DIR="/run/user/$USER_UID" systemctl --user restart bt-loopback.service

echo "Configurazione Audio e Loopback completata."
echo

###############################################################################
# 11.5) Rende eseguibile lo script di avvio infotainment
###############################################################################
if [[ -f "$PROJECT_DIR/scripts/start_infotainment.sh" ]]; then
  chmod +x "$PROJECT_DIR/scripts/start_infotainment.sh"
  echo "Reso eseguibile: $PROJECT_DIR/scripts/start_infotainment.sh"
else
  echo "ATTENZIONE: $PROJECT_DIR/scripts/start_infotainment.sh non trovato!"
fi


###############################################################################
# 12) Servizio systemd per avviare l'infotainment (FIXED)
###############################################################################
echo ">>> Creazione servizio systemd 'infotainment.service'..."

# Tenta di rilevare il nome del sink. Aggiungiamo "|| true" per evitare che
# grep faccia crashare lo script se non trova nulla (cosa normale prima del reboot).
DETECTED_SINK=$(sudo -u "$USER_NAME" XDG_RUNTIME_DIR="/run/user/$USER_UID" pactl list sinks short 2>/dev/null | grep -E "analog-stereo|Headphones" | cut -f2 | head -n1 || true)

if [[ -n "$DETECTED_SINK" ]]; then
    SINK_NAME="$DETECTED_SINK"
    echo "Sink Audio rilevato dinamicamente: $SINK_NAME"
else
    # Se il rilevamento fallisce (es. al primo install), usiamo il default del Jack Audio del Pi
    SINK_NAME="alsa_output.platform-bcm2835_audio.analog-stereo"
    echo "Nessun sink rilevato (normale pre-reboot). Usato default: $SINK_NAME"
fi

# Percorsi
SERVICE_EXEC="$PROJECT_DIR/scripts/start_infotainment.sh"
SERVICE_WORK="$PROJECT_DIR"

# Assicuriamoci che lo script sia eseguibile e appartenga all'utente
chmod +x "$SERVICE_EXEC"
chown "$USER_NAME:$USER_NAME" "$SERVICE_EXEC"

# Percorso Socket PulseAudio
PULSE_SERVER_PATH="unix:/run/user/${USER_UID}/pulse/native"

# Scriviamo il file di servizio (Versione stabile senza SupplementaryGroups espliciti)
cat >/etc/systemd/system/infotainment.service <<EOF
[Unit]
Description=RPi Car Infotainment (Qt6 Framebuffer)
After=network.target bluetooth.service pulseaudio.service
Wants=bluetooth.service

[Service]
Type=simple
User=$USER_NAME
Group=$USER_NAME
WorkingDirectory=$SERVICE_WORK

# --- VARIABILI AMBIENTE ---
Environment=PYTHONUNBUFFERED=1

# Configurazione Grafica Qt (Framebuffer 1024x600 FORZATO)
Environment=QT_QPA_PLATFORM=linuxfb:fb=/dev/fb0:size=1024x600
Environment=QT_QPA_GENERIC_PLUGINS=evdevtouch:/dev/input/event0

# Configurazione Audio
Environment=SDL_AUDIODRIVER=pulseaudio
Environment=PULSE_SERVER=$PULSE_SERVER_PATH
Environment=PULSE_SINK=$SINK_NAME

# Comando di avvio
ExecStart=$SERVICE_EXEC

# Riavvio automatico
Restart=always
RestartSec=3

# Log
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable infotainment.service

echo "Servizio infotainment abilitato. Partirà automaticamente al prossimo reboot."
echo

###############################################################################
# 13) Fine
###############################################################################
echo ">>> INSTALLAZIONE COMPLETATA."
echo "Ora esegui: sudo reboot"
echo "Al riavvio, il Pi dovrebbe:"
echo "- usare lo schermo in 1024x600"
echo "- presentarsi come dispositivo BT classico (A2DP)"
echo "- inoltrare l'audio BT al jack analogico"
echo "- avviare automaticamente l'app rpi_car_infotainment"
