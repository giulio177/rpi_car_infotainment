#!/usr/bin/env bash
set -u # Non usiamo -e qui per gestire gli errori manualmente dentro la GUI

# Controllo Root
if [[ "$EUID" -ne 0 ]]; then
  echo "Esegui come root: sudo ./install_gui.sh"
  exit 1
fi

# Configurazione variabili base
USER_NAME="${SUDO_USER:-pi}"
USER_HOME=$(getent passwd "$USER_NAME" | cut -d: -f6)
PROJECT_DIR="$USER_HOME/rpi_car_infotainment"
USER_UID=$(id -u "$USER_NAME")

# --- DEFINIZIONE DELLE FUNZIONI (I tuoi step originali) ---

func_update_system() {
    apt update && apt full-upgrade -y
    apt install -y git python3-venv python3-pip ffmpeg pulseaudio pulseaudio-module-bluetooth \
    alsa-utils bluez bluez-tools python3-dbus python3-gi gir1.2-glib-2.0 dbus-user-session \
    libminizip1 libxkbfile1 libsnappy1v5 libdbus-1-dev libglib2.0-dev python3-dev build-essential pkg-config
}

func_config_boot() {
    # Logica boot config (Step 1, 3, 3.5, 4 originali)
    # Step 1
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
    
    # Step 3
    echo ">>> Configurazione $CMDLINE_FILE..."

	EXTRA_CMDLINE="logo.nologo quiet loglevel=3 vt.global_cursor_default=0"

	if ! grep -q "logo.nologo" "$CMDLINE_FILE"; then
		sed -i "1s|\$| ${EXTRA_CMDLINE}|" "$CMDLINE_FILE"
		echo "Aggiunte opzioni extra/logo/log a cmdline.txt."
	else
		echo "Opzioni extra già presenti in cmdline.txt, salto."
	fi

	echo

    # Step 3.5
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
EOF)
    
    # Aggiungi il blocco solo se non già presente
	if ! grep -q "hdmi_cvt=1024 600 60 6 0 0 0" "$CONFIG_FILE"; then
		printf "\n%s\n" "$HDMI_BLOCK" >> "$CONFIG_FILE"
		echo "Blocco HDMI 1024x600 aggiunto a config.txt."
	else
      echo "Blocco HDMI 1024x600 già presente in config.txt, salto."
    fi
    
    echo
    
    # Step 4
    echo ">>> Configurazione $CONFIG_FILE (dtparam=audio=on)..."

    if grep -q '^dtparam=audio=' "$CONFIG_FILE"; then
      sed -i 's/^dtparam=audio=.*/dtparam=audio=on/' "$CONFIG_FILE"
    else
      echo 'dtparam=audio=on' >> "$CONFIG_FILE"
    fi
    echo "Audio del Pi abilitato in config.txt."
    echo
    
}

func_setup_bluetooth() {
    # Configurazione BlueZ, main.conf, installazione agente python
    # [Incolla qui la sezione 6, 7 e 8 del tuo script]
    # Step 6
    echo ">>> Configurazione /etc/bluetooth/main.conf..."

    # 1. Creazione file base se manca
    if [[ ! -f /etc/bluetooth/main.conf ]]; then
        echo "[General]" > /etc/bluetooth/main.conf
    elif ! grep -q '^\[General\]' /etc/bluetooth/main.conf; then
        sed -i '1i[General]' /etc/bluetooth/main.conf
    fi
    
    # 2. Funzione helper
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
    
    # 3. CONFIGURAZIONE CHIAVE
    # Class 0x200420 = Car Audio (Il telefono capisce che deve mandare l'audio qui)
    set_bt_conf "Class" "0x200420"
    
    # Timeout Visibilità: 180 secondi (3 minuti) poi torna invisibile
    set_bt_conf "DiscoverableTimeout" "180"
    
    # Timeout Pairing: 0 (Sempre accoppiabile SE visibile)
    set_bt_conf "PairableTimeout" "0"
    
    # Bluetooth acceso all'avvio, ma NON visibile (lo farà la tua app)
    set_bt_conf "AutoEnable" "true"
    set_bt_conf "ControllerMode" "bredr"
    set_bt_conf "Name" "RPi-Infotainment"
    
    echo "/etc/bluetooth/main.conf configurato: Car Audio, Timeout 180s."
    echo

    # Step 7
    echo ">>> Installazione agente Bluetooth NoInputNoOutput..."

    cat >/usr/local/bin/bt-agent-rpi.py <<'PY'
    #!/usr/bin/env python3
    import dbus, dbus.service, dbus.mainloop.glib
    from gi.repository import GLib
    
    # NoInputNoOutput = "Just Works" (Nessun PIN richiesto)
    AGENT_PATH = "/test/agent"
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
                # Marca come fidato immediatamente
                props.Set("org.bluez.Device1", "Trusted", True)
                print(f"Device {path} set to Trusted.")
            except Exception as e:
                print(f"Failed to set trusted: {e}")

        @dbus.service.method("org.bluez.Agent1", in_signature="o", out_signature="s")
        def RequestPinCode(self, device):
            self.set_trusted(device)
            return "0000"
    
        @dbus.service.method("org.bluez.Agent1", in_signature="o", out_signature="u")
        def RequestPasskey(self, device):
            self.set_trusted(device)
            return dbus.UInt32(0000)
    
        @dbus.service.method("org.bluez.Agent1", in_signature="ou", out_signature="")
        def RequestConfirmation(self, device, passkey):
            self.set_trusted(device)
            return
    
        @dbus.service.method("org.bluez.Agent1", in_signature="o", out_signature="")
        def RequestAuthorization(self, device):
            self.set_trusted(device)
            return
    
        @dbus.service.method("org.bluez.Agent1", in_signature="", out_signature="")
        def Cancel(self):
            pass
    
    if __name__ == "__main__":
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        bus = dbus.SystemBus()
        agent = Agent(bus, AGENT_PATH)
        obj = bus.get_object("org.bluez", "/org/bluez")
        manager = dbus.Interface(obj, "org.bluez.AgentManager1")
        
        # Rimuove vecchi agenti
        try: manager.UnregisterAgent(AGENT_PATH)
        except: pass
            
        manager.RegisterAgent(AGENT_PATH, CAPABILITY)
        manager.RequestDefaultAgent(AGENT_PATH)
        print("Bluetooth Agent (NoInputNoOutput) Running...")
        GLib.MainLoop().run()
PY
    
    chmod +x /usr/local/bin/bt-agent-rpi.py
    
    # Servizio Systemd per l'agente
    cat >/etc/systemd/system/bt-agent.service <<EOF
[Unit]
Description=Bluetooth Auto-Pairing Agent
Requires=bluetooth.service
After=bluetooth.service
    
[Service]
ExecStart=/usr/local/bin/bt-agent-rpi.py
Restart=always
RestartSec=2
StandardOutput=journal
StandardError=journal
    
[Install]
WantedBy=bluetooth.target
EOF
    
    systemctl daemon-reload
    systemctl enable --now bt-agent.service
    
    # Configurazione legacy per sicurezza
    btmgmt io-cap 3       || true
    btmgmt bondable on    || true
    btmgmt pairable on    || true
    # IMPORTANTE: NON mettiamo 'discoverable on' qui, ci penserà la tua app
    btmgmt connectable on || true
    btmgmt bredr on       || true
    
    echo "Agente Bluetooth installato. Visibilità gestita dall'App."
    echo
    

    # Step 8
    echo ">>> Configurazione controller Bluetooth (btmgmt)..."

    # In caso il controller non sia power on, btmgmt potrebbe lamentarsi: ignoriamo errori
    btmgmt io-cap 3       || true
    btmgmt bondable on    || true
    btmgmt connectable on || true
    btmgmt pairable on    || true
    btmgmt bredr on       || true
    
    echo "btmgmt configurato (io-cap=3, bondable/connectable/pairable/bredr on)."
    echo

}

func_python_env() {
    # Creazione venv
    sudo -u "$USER_NAME" bash -lc "
      if [[ ! -d '$PROJECT_DIR' ]]; then echo 'Dir non trovata'; exit 1; fi
      cd '$PROJECT_DIR'
      python3 -m venv venv
      source venv/bin/activate
      pip install -r requirements.txt
    "
}

func_audio_setup() {
    # Configurazione PulseAudio e Loopback
    # [Incolla qui la sezione 5 e 11 del tuo script]
    # Step 5
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

    # Step 11
    echo ">>> Configurazione Audio (Forzatura Jack Analogico)..."


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
            pactl load-module module-loopback source="$SRC_ID" sink="$SINK" latency_msec=100
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
}

func_install_service() {
    # Setup Systemd service
    # [Incolla qui la sezione 12 del tuo script]
    echo ">>> Creazione servizio systemd 'infotainment.service'..."


    # Proviamo a rilevare il nome esatto del sink (scheda audio) analogico/cuffie
    SINK_NAME=$(sudo -u "$USER_NAME" XDG_RUNTIME_DIR="/run/user/$USER_UID" pactl list sinks short 2>/dev/null | grep -E "analog-stereo|Headphones" | cut -f2 | head -n1)
    
    # Se il rilevamento fallisce, usiamo il nome standard del Raspberry Pi o il default
    if [[ -z "${SINK_NAME:-}" ]]; then
        SINK_NAME="alsa_output.platform-bcm2835_audio.analog-stereo"
    fi
    echo "Sink Audio identificato per il servizio: $SINK_NAME"
    # Percorsi
    SERVICE_EXEC="/home/pi/rpi_car_infotainment/scripts/start_infotainment.sh"
    SERVICE_WORK="/home/pi/rpi_car_infotainment"
    
    # Assicuriamoci che lo script sia eseguibile
    chmod +x "$SERVICE_EXEC"
    chown $USER_NAME:$USER_NAME "$SERVICE_EXEC"
    
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

# Nota: L'utente $USER_NAME deve essere già nei gruppi video, input, audio, render.
# Systemd userà i gruppi di default dell'utente.

# --- VARIABILI AMBIENTE ---
Environment=PYTHONUNBUFFERED=1

# Configurazione Grafica Qt (Framebuffer 1024x600 FORZATO)
# Impedisce il taglio della barra in basso e i pulsanti stirati
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
}

# --- INTERFACCIA WHIPTAIL ---

# 1. Menu di Selezione
# Visualizza una lista di opzioni selezionabili (ON/OFF)
CHOICES=$(whiptail --title "RPi Car Infotainment Installer" --checklist \
"Seleziona gli step da eseguire (Spazio per selezionare, Invio per confermare):" 20 78 6 \
"1" "Aggiornamento OS e Pacchetti" ON \
"2" "Configurazione Boot (HDMI/FKMS)" ON \
"3" "Configurazione Bluetooth (BlueZ/Agent)" ON \
"4" "Installazione Python e Dipendenze" ON \
"5" "Setup Audio (PulseAudio/Loopback)" ON \
"6" "Installazione Servizio Systemd" ON \
3>&1 1>&2 2>&3)

# Se l'utente preme Cancel
if [ $? -ne 0 ]; then
    echo "Installazione annullata dall'utente."
    exit 0
fi

# 2. Esecuzione con Barra di Caricamento
# La logica è: calcoliamo quanti step sono stati scelti, e aggiorniamo la barra.

# Conta quanti item sono stati selezionati
COUNT=$(echo "$CHOICES" | tr -cd '"' | wc -c)
COUNT=$((COUNT / 2)) # Ogni selezione ha 2 virgolette
CURRENT=0
STEP_SIZE=$((100 / COUNT)) # Percentuale per ogni step

# Avvia il processo piping tutto dentro whiptail gauge
{
    # STEP 1
    if [[ $CHOICES == *"1"* ]]; then
        echo "XXX"
        echo $((CURRENT + 10)) # Aumenta un po' subito per feedback visivo
        echo "Esecuzione: Aggiornamento Sistema e Pacchetti (Lungo)..."
        echo "XXX"
        func_update_system >> /var/log/rpi_install.log 2>&1
        CURRENT=$((CURRENT + STEP_SIZE))
        echo $CURRENT
    fi

    # STEP 2
    if [[ $CHOICES == *"2"* ]]; then
        echo "XXX"
        echo $CURRENT
        echo "Esecuzione: Configurazione Boot e Video..."
        echo "XXX"
        func_config_boot >> /var/log/rpi_install.log 2>&1
        CURRENT=$((CURRENT + STEP_SIZE))
        echo $CURRENT
    fi

    # STEP 3
    if [[ $CHOICES == *"3"* ]]; then
        echo "XXX"
        echo $CURRENT
        echo "Esecuzione: Configurazione Bluetooth..."
        echo "XXX"
        func_setup_bluetooth >> /var/log/rpi_install.log 2>&1
        CURRENT=$((CURRENT + STEP_SIZE))
        echo $CURRENT
    fi

    # STEP 4
    if [[ $CHOICES == *"4"* ]]; then
        echo "XXX"
        echo $CURRENT
        echo "Esecuzione: Ambiente Python (venv)..."
        echo "XXX"
        func_python_env >> /var/log/rpi_install.log 2>&1
        CURRENT=$((CURRENT + STEP_SIZE))
        echo $CURRENT
    fi

    # STEP 5
    if [[ $CHOICES == *"5"* ]]; then
        echo "XXX"
        echo $CURRENT
        echo "Esecuzione: Setup Audio Loopback..."
        echo "XXX"
        func_audio_setup >> /var/log/rpi_install.log 2>&1
        CURRENT=$((CURRENT + STEP_SIZE))
        echo $CURRENT
    fi

    # STEP 6
    if [[ $CHOICES == *"6"* ]]; then
        echo "XXX"
        echo $CURRENT
        echo "Esecuzione: Creazione Servizio Systemd..."
        echo "XXX"
        func_install_service >> /var/log/rpi_install.log 2>&1
        echo 100
    fi

    sleep 1

} | whiptail --title "Installazione in corso" --gauge "Attendere..." 8 70 0

# 3. Messaggio Finale
whiptail --title "Completato" --msgbox "Installazione terminata!\nLog salvato in /var/log/rpi_install.log\n\nPremi OK per riavviare o Cancel per uscire." 10 60

if [ $? -eq 0 ]; then
    reboot
fi
