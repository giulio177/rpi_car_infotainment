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
  python3-pyqt6 qt6-base-dev \
  python3-pygame ffmpeg \
  pulseaudio pulseaudio-module-bluetooth alsa-utils \
  bluez bluez-tools \
  python3-dbus python3-gi gir1.2-glib-2.0 \
  dbus-user-session \
  libdbus-1-dev libglib2.0-dev python3-dev \
  build-essential pkg-config

echo ">>> Pacchetti installati."
echo

###############################################################################
# 3) Configurazione cmdline.txt (quiet, logo, loglevel, cursore)
###############################################################################
echo ">>> Configurazione $CMDLINE_FILE..."

EXTRA_CMDLINE="logo.nologo quiet loglevel=3 vt.global_cursor_default=0"

if ! grep -q "1024x600@60D" "$CMDLINE_FILE"; then
  # cmdline.txt è una sola riga: aggiungiamo le opzioni in coda
  sed -i "1s|\$| ${EXTRA_CMDLINE}|" "$CMDLINE_FILE"
  echo "Aggiunte opzioni extra/logo/log a cmdline.txt."
else
  echo "Opzioni extra già presenti in cmdline.txt, salto."
fi
echo

###############################################################################
# 3.5) Configurazione config.txt (risoluzione HDMI 1024x600)
###############################################################################
echo ">>> Configurazione $CONFIG_FILE (display 1024x600)..."

# Blocco HDMI per forzare 1024x600 @ 60Hz con CVT custom
read -r -d '' HDMI_BLOCK << 'EOF'
# RPi Car Infotainment - display 1024x600
hdmi_force_hotplug=1
hdmi_ignore_edid=0xa5000080
hdmi_group=2
hdmi_mode=87
hdmi_cvt=1024 600 60 6 0 0 0
EOF

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
# 6) Configurazione BlueZ (BR/EDR, AutoEnable) in /etc/bluetooth/main.conf
###############################################################################
echo ">>> Configurazione /etc/bluetooth/main.conf..."

if [[ ! -f /etc/bluetooth/main.conf ]]; then
  # Creiamo un file base con sezione [General]
  cat >/etc/bluetooth/main.conf <<'EOF'
[General]
EOF
fi

# Assicuriamoci che la sezione [General] esista
if ! grep -q '^\[General\]' /etc/bluetooth/main.conf; then
  sed -i '1i[General]' /etc/bluetooth/main.conf
fi

# Aggiungi/aggiorna ControllerMode e AutoEnable
if grep -q '^ControllerMode' /etc/bluetooth/main.conf; then
  sed -i 's/^ControllerMode.*/ControllerMode = bredr/' /etc/bluetooth/main.conf
else
  sed -i '/^\[General\]/a ControllerMode = bredr' /etc/bluetooth/main.conf
fi

if grep -q '^AutoEnable' /etc/bluetooth/main.conf; then
  sed -i 's/^AutoEnable.*/AutoEnable = true/' /etc/bluetooth/main.conf
else
  sed -i '/^\[General\]/a AutoEnable = true' /etc/bluetooth/main.conf
fi

echo "/etc/bluetooth/main.conf configurato (BR/EDR, AutoEnable=true)."
echo

###############################################################################
# 7) Agente Bluetooth di auto-pairing (PIN 0000)
###############################################################################
echo ">>> Installazione agente Bluetooth di auto-pairing..."

cat >/usr/local/bin/bt-agent-rpi.py <<'PY'
#!/usr/bin/env python3
import dbus, dbus.service, dbus.mainloop.glib
from gi.repository import GLib

AGENT_PATH = "/test/agent"
AGENT_INTERFACE = "org.bluez.Agent1"
CAPABILITY = "NoInputNoOutput"

class Agent(dbus.service.Object):
    def __init__(self, bus, path):
        super().__init__(bus, path)
        self.bus = bus

    def set_trusted(self, path):
        try:
            props = dbus.Interface(
                self.bus.get_object("org.bluez", path),
                "org.freedesktop.DBus.Properties"
            )
            props.Set("org.bluez.Device1", "Trusted", True)
        except Exception:
            pass

    @dbus.service.method(AGENT_INTERFACE, in_signature="o", out_signature="s")
    def RequestPinCode(self, device):
        self.set_trusted(device)
        return "0000"

    @dbus.service.method(AGENT_INTERFACE, in_signature="ou", out_signature="")
    def RequestConfirmation(self, device, passkey):
        self.set_trusted(device)

    @dbus.service.method(AGENT_INTERFACE, in_signature="o", out_signature="")
    def RequestAuthorization(self, device):
        self.set_trusted(device)

    @dbus.service.method(AGENT_INTERFACE, in_signature="", out_signature="")
    def Release(self):
        pass

    @dbus.service.method(AGENT_INTERFACE, in_signature="", out_signature="")
    def Cancel(self):
        pass

if __name__ == "__main__":
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()
    agent = Agent(bus, AGENT_PATH)
    obj = bus.get_object("org.bluez", "/org/bluez")
    manager = dbus.Interface(obj, "org.bluez.AgentManager1")
    manager.RegisterAgent(AGENT_PATH, CAPABILITY)
    manager.RequestDefaultAgent(AGENT_PATH)
    GLib.MainLoop().run()
PY

chmod +x /usr/local/bin/bt-agent-rpi.py

cat >/etc/systemd/system/bt-agent.service <<EOF
[Unit]
Description=Bluetooth Auto-Pairing Agent (RPi Car Infotainment)
Requires=bluetooth.service
After=bluetooth.service

[Service]
ExecStart=/usr/local/bin/bt-agent-rpi.py
Restart=always
RestartSec=2

[Install]
WantedBy=bluetooth.target
EOF

systemctl daemon-reload
systemctl enable --now bt-agent.service

echo "Agente Bluetooth bt-agent-rpi attivato."
echo

###############################################################################
# 8) Configurazione spinte tramite btmgmt (non interattivo)
###############################################################################
echo ">>> Configurazione controller Bluetooth (btmgmt)..."

# In caso il controller non sia power on, btmgmt potrebbe lamentarsi: ignoriamo errori
btmgmt io-cap 3       || true
btmgmt bondable on    || true
btmgmt connectable on || true
btmgmt pairable on    || true
btmgmt bredr on       || true

echo "btmgmt configurato (io-cap=3, bondable/connectable/pairable/bredr on)."
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
  python3 -m venv --system-site-packages venv
  source venv/bin/activate
  pip install --upgrade pip
  pip install -r requirements.txt
"

echo "Virtualenv e dipendenze Python installate."
echo

###############################################################################
# 11) Setup systemd user per PulseAudio e loopback Bluetooth → analog
###############################################################################
echo ">>> Configurazione user systemd, PulseAudio e loopback Bluetooth..."

# Linger: permette al manager user di girare anche senza login interattivo
loginctl enable-linger "$USER_NAME" || true

# Avvia systemd user per l'utente
systemctl start "user@${USER_UID}.service" || true

# Proviamo ad abilitare/avviare pulseaudio come servizio user (se esiste)
sudo -u "$USER_NAME" XDG_RUNTIME_DIR="/run/user/$USER_UID" systemctl --user enable pulseaudio 2>/dev/null || true
sudo -u "$USER_NAME" XDG_RUNTIME_DIR="/run/user/$USER_UID" systemctl --user start pulseaudio 2>/dev/null || true

# Se non esiste il servizio, PulseAudio di solito si auto-spawna; forziamo l'avvio una volta
sudo -u "$USER_NAME" XDG_RUNTIME_DIR="/run/user/$USER_UID" pulseaudio --start 2>/dev/null || true

sleep 3

# Individua il sink analogico (o il primo disponibile) per usarlo come uscita
SINK_NAME="$(sudo -u "$USER_NAME" XDG_RUNTIME_DIR="/run/user/$USER_UID" pactl list sinks short 2>/dev/null | awk '/analog-stereo/ {print $2; exit}')"
if [[ -z "${SINK_NAME:-}" ]]; then
  SINK_NAME="$(sudo -u "$USER_NAME" XDG_RUNTIME_DIR="/run/user/$USER_UID" pactl list sinks short 2>/dev/null | awk 'NR==1 {print $2; exit}')"
fi
if [[ -z "${SINK_NAME:-}" ]]; then
  echo "ATTENZIONE: nessun sink PulseAudio trovato. Imposto fallback generico per Pi analog:"
  SINK_NAME="alsa_output.platform-bcm2835-audio.analog-stereo"
fi

echo "Sink PulseAudio usato: $SINK_NAME"
echo

# Script loopback bluetooth → sink scelto (user)
sudo -u "$USER_NAME" mkdir -p "$USER_HOME/.local/bin" "$USER_HOME/.config/systemd/user"

cat >"$USER_HOME/.local/bin/bt-loopback.sh" <<EOF
#!/bin/bash
set -euo pipefail
SINK="$SINK_NAME"

try_once() {
  src=\$(pactl list sources short | awk '/bluez_source/ {print \$2; exit}')
  if [[ -n "\${src:-}" ]]; then
    pactl load-module module-loopback source="\$src" sink="\$SINK" latency_msec=60 >/dev/null 2>&1 || true
  fi
}

try_once
pactl subscribe | while read -r line; do
  echo "\$line" | grep -qE "source|card" && try_once
done
EOF

chown "$USER_NAME:$USER_NAME" "$USER_HOME/.local/bin/bt-loopback.sh"
chmod +x "$USER_HOME/.local/bin/bt-loopback.sh"

cat >"$USER_HOME/.config/systemd/user/bt-loopback.service" <<EOF
[Unit]
Description=Bluetooth A2DP loopback to analog sink
After=pulseaudio.service bluetooth.target
Wants=pulseaudio.service

[Service]
ExecStart=$USER_HOME/.local/bin/bt-loopback.sh
Restart=always
RestartSec=2

[Install]
WantedBy=default.target
EOF

chown "$USER_NAME:$USER_NAME" "$USER_HOME/.config/systemd/user/bt-loopback.service"

sudo -u "$USER_NAME" XDG_RUNTIME_DIR="/run/user/$USER_UID" systemctl --user daemon-reload
sudo -u "$USER_NAME" XDG_RUNTIME_DIR="/run/user/$USER_UID" systemctl --user enable bt-loopback.service
sudo -u "$USER_NAME" XDG_RUNTIME_DIR="/run/user/$USER_UID" systemctl --user start bt-loopback.service

echo "Servizio user bt-loopback attivato."
echo

###############################################################################
# 12) Servizio systemd per avviare l'infotainment (framebuffer, no X)
###############################################################################
echo ">>> Creazione servizio systemd 'infotainment.service'..."

PULSE_SERVER_PATH="unix:/run/user/${USER_UID}/pulse/native"

cat >/etc/systemd/system/infotainment.service <<EOF
[Unit]
Description=RPi Car Infotainment (framebuffer, no X)
After=network.target bluetooth.service
Wants=bluetooth.service

[Service]
Type=simple
User=$USER_NAME
Group=$USER_NAME
WorkingDirectory=$USER_HOME
# Accesso a /dev/fb0 e /dev/input/event*
SupplementaryGroups=video,input
# Niente display X
Environment=DISPLAY=
# Audio app: SDL/pygame -> Pulse, e sink scelto sopra
Environment=SDL_AUDIODRIVER=pulseaudio
Environment=PULSE_SERVER=$PULSE_SERVER_PATH
Environment=PULSE_SINK=$SINK_NAME
ExecStart=$PROJECT_DIR/scripts/start_infotainment.sh
Restart=on-failure
RestartSec=2
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
