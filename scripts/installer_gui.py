#!/usr/bin/env python3
import os
import sys
import time
import subprocess
import threading
import pygame
from pathlib import Path

# --- CONFIGURAZIONE SISTEMA ---
# Forza l'uso del Framebuffer o DRM (necessario su RPi Lite senza Desktop)
os.environ["SDL_VIDEODRIVER"] = "kmsdrm" 
# Se kmsdrm da errore su vecchi RPi, prova: os.environ["SDL_VIDEODRIVER"] = "fbcon"

# Recupero variabili utente (Simile a SUDO_USER in bash)
SUDO_USER = os.environ.get('SUDO_USER', 'pi')
try:
    import pwd
    pw_record = pwd.getpwnam(SUDO_USER)
    USER_HOME = pw_record.pw_dir
    USER_UID = pw_record.pw_uid
    USER_GID = pw_record.pw_gid
except KeyError:
    print(f"Utente {SUDO_USER} non trovato!")
    sys.exit(1)

PROJECT_DIR = os.path.join(USER_HOME, "rpi_car_infotainment")
LOG_FILE = os.path.join(PROJECT_DIR, "logs/rpi_car_installer.log")

# --- COLORI & UI ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK_GRAY = (30, 30, 30)
BLUE = (0, 120, 215)
GREEN = (0, 200, 100)
RED = (220, 50, 50)
LIGHT_GRAY = (200, 200, 200)

# --- FUNZIONI HELPER (Traduzione logica Bash) ---

def run_cmd(command, as_user=None):
    """Esegue un comando shell. Se as_user è impostato, usa sudo -u."""
    cmd_str = command
    if isinstance(command, list):
        cmd_str = " ".join(command)
    
    prefix = ""
    if as_user:
        prefix = f"sudo -u {as_user} bash -c "
        final_cmd = [f"sudo -u {as_user} bash -c '{cmd_str}'"]
        shell_mode = True
    else:
        final_cmd = command
        shell_mode = isinstance(command, str)

    with open(LOG_FILE, "a") as log:
        log.write(f"\n>>> EXEC: {cmd_str}\n")
        try:
            subprocess.run(final_cmd, shell=shell_mode, check=True, stdout=log, stderr=log)
        except subprocess.CalledProcessError as e:
            log.write(f"!!! ERROR: {e}\n")
            raise e

def write_file(path, content, mode="w"):
    """Scrive contenuto su file (simile a cat > file << EOF)."""
    with open(path, mode) as f:
        f.write(content)

def append_if_missing(path, search_str, append_str):
    """Simula grep || echo >> logic."""
    if not os.path.exists(path): return
    with open(path, "r") as f:
        content = f.read()
    if search_str not in content:
        with open(path, "a") as f:
            f.write(f"\n{append_str}\n")

# --- STEP DI INSTALLAZIONE (Logica del tuo script originale) ---

def step_update_system():
    run_cmd("apt update")
    run_cmd("apt full-upgrade -y")
    pkgs = [
        "git", "python3-venv", "python3-pip", "ffmpeg", 
        "pulseaudio", "pulseaudio-module-bluetooth", "alsa-utils",
        "bluez", "bluez-tools", "python3-dbus", "python3-gi", 
        "gir1.2-glib-2.0", "dbus-user-session", "libminizip1", 
        "libxkbfile1", "libsnappy1v5", "libdbus-1-dev", 
        "libglib2.0-dev", "python3-dev", "build-essential", "pkg-config"
    ]
    run_cmd(f"apt install -y {' '.join(pkgs)}")

def step_config_boot():
    # Detect Boot Dir
    boot_dir = "/boot"
    if os.path.exists("/boot/firmware/cmdline.txt"):
        boot_dir = "/boot/firmware"
    
    cmdline_file = f"{boot_dir}/cmdline.txt"
    config_file = f"{boot_dir}/config.txt"

    # Cmdline
    extra = "logo.nologo quiet loglevel=3 vt.global_cursor_default=0"
    with open(cmdline_file, 'r') as f:
        data = f.read().strip()
    if "logo.nologo" not in data:
        with open(cmdline_file, 'w') as f:
            f.write(f"{data} {extra}")

    # Config.txt - FKMS replacement
    with open(config_file, 'r') as f:
        lines = f.readlines()
    
    new_lines = []
    has_fkms = False
    for line in lines:
        if "dtoverlay=vc4-kms-v3d" in line:
            new_lines.append(line.replace("kms", "fkms"))
            has_fkms = True
        elif "dtoverlay=vc4-fkms-v3d" in line:
            new_lines.append(line)
            has_fkms = True
        elif "dtparam=audio=" in line:
             new_lines.append("dtparam=audio=on\n") # Force audio on
        else:
            new_lines.append(line)
    
    if not has_fkms:
        new_lines.append("dtoverlay=vc4-fkms-v3d\n")
    
    # Audio if missing entirely
    if not any("dtparam=audio=" in l for l in new_lines):
        new_lines.append("dtparam=audio=on\n")

    # HDMI Block
    hdmi_block = """
# RPi Car Infotainment - display 1024x600
hdmi_force_hotplug=1
hdmi_group=2
hdmi_mode=87
hdmi_cvt=1024 600 60 6 0 0 0
"""
    # Check if HDMI block exists loosely
    if not any("hdmi_cvt=1024" in l for l in new_lines):
        new_lines.append(hdmi_block)

    with open(config_file, 'w') as f:
        f.writelines(new_lines)

def step_setup_bluetooth():
    # /etc/bluetooth/main.conf
    main_conf = "/etc/bluetooth/main.conf"
    if not os.path.exists(main_conf):
        write_file(main_conf, "[General]\n")
    
    # Python ConfigParser logic is cleaner, but let's stick to appending/replacing for simplicity
    # Simulating the sed logic roughly by rewriting file logic is safer in Python
    # But for brevity, we will append if keys missing, assuming clean install
    
    settings = {
        "Class": "0x200420",
        "DiscoverableTimeout": "180",
        "PairableTimeout": "0",
        "AutoEnable": "true",
        "ControllerMode": "bredr",
        "Name": "RPi-Infotainment"
    }
    
    # Read content
    with open(main_conf, 'r') as f:
        lines = f.readlines()
    
    # Simple logic: Remove lines starting with key, append new ones under [General]
    final_lines = []
    seen_keys = []
    
    for line in lines:
        key = line.split('=')[0].strip()
        if key in settings:
            continue # Skip, we will add later
        final_lines.append(line)
        
    # Find [General] index
    idx = 0
    for i, line in enumerate(final_lines):
        if "[General]" in line:
            idx = i + 1
            break
            
    # Insert settings
    for k, v in settings.items():
        final_lines.insert(idx, f"{k} = {v}\n")
        idx += 1
        
    with open(main_conf, 'w') as f:
        f.writelines(final_lines)

    # Agent Python Script
    agent_path = "/usr/local/bin/bt-agent-rpi.py"
    agent_code = r'''#!/usr/bin/env python3
import dbus, dbus.service, dbus.mainloop.glib
from gi.repository import GLib

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
            props.Set("org.bluez.Device1", "Trusted", True)
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
    try: manager.UnregisterAgent(AGENT_PATH)
    except: pass
    manager.RegisterAgent(AGENT_PATH, CAPABILITY)
    manager.RequestDefaultAgent(AGENT_PATH)
    GLib.MainLoop().run()
'''
    write_file(agent_path, agent_code)
    run_cmd(f"chmod +x {agent_path}")

    # Service Agent
    service_content = """[Unit]
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
"""
    write_file("/etc/systemd/system/bt-agent.service", service_content)
    run_cmd("systemctl daemon-reload")
    run_cmd("systemctl enable --now bt-agent.service")
    
    # BTMGMT
    # Ignore errors here with try/except inside run_cmd wrapper if needed, or allow fail
    try: run_cmd("btmgmt io-cap 3")
    except: pass
    try: run_cmd("btmgmt bondable on")
    except: pass
    try: run_cmd("btmgmt pairable on")
    except: pass
    try: run_cmd("btmgmt bredr on")
    except: pass

def step_python_env():
    if not os.path.exists(PROJECT_DIR):
        raise Exception(f"Directory {PROJECT_DIR} non trovata!")
    
    cmd = f"cd '{PROJECT_DIR}' && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    run_cmd(cmd, as_user=SUDO_USER)

def step_audio_setup():
    run_cmd("systemctl disable --now pulseaudio", as_user=None) # Disable system wide
    
    write_file("/etc/asound.conf", "pcm.!default pulse\nctl.!default pulse\n")
    
    # Pulse Default
    default_pa = "/etc/pulse/default.pa"
    bt_modules = "\nload-module module-bluetooth-policy\nload-module module-bluetooth-discover\n"
    
    if os.path.exists(default_pa):
        append_if_missing(default_pa, "module-bluetooth-discover", bt_modules)
    else:
        write_file(default_pa, f"### Minimal\n{bt_modules}")
        
    # Cleanup User Pulse
    run_cmd(f"rm -rf {USER_HOME}/.config/pulse")
    run_cmd("amixer -c 1 set PCM 100% unmute")
    run_cmd(f"loginctl enable-linger {SUDO_USER}")
    
    # Start User Pulse
    xdg_env = f"XDG_RUNTIME_DIR=/run/user/{USER_UID}"
    run_cmd(f"{xdg_env} systemctl --user enable pulseaudio", as_user=SUDO_USER)
    run_cmd(f"{xdg_env} systemctl --user start pulseaudio", as_user=SUDO_USER)
    time.sleep(3)
    
    # Loopback Script
    local_bin = f"{USER_HOME}/.local/bin"
    os.makedirs(local_bin, exist_ok=True)
    loop_script = f"{local_bin}/bt-loopback.sh"
    
    script_content = r'''#!/bin/bash
set -euo pipefail
find_sink() {
    TARGET_SINK=$(pactl list sinks short | grep -E "analog-stereo|Headphones" | cut -f2 | head -n1)
    if [[ -z "$TARGET_SINK" ]]; then TARGET_SINK="@DEFAULT_SINK@"; fi
    echo "$TARGET_SINK"
}
try_connect() {
    SINK=$(find_sink)
    pactl set-card-profile 0 off 2>/dev/null || true
    pactl list sources short | grep "bluez_source" | while read -r line; do
        SRC_ID=$(echo "$line" | cut -f2)
        if ! pactl list modules short | grep -q "source=$SRC_ID sink=$SINK"; then
            pactl load-module module-loopback source="$SRC_ID" sink="$SINK" latency_msec=100
        fi
    done
}
try_connect
pactl subscribe | while read -r line; do
    if echo "$line" | grep -qE "new|put"; then
        if echo "$line" | grep -qE "source|card"; then
            sleep 2; try_connect
        fi
    fi
done
'''
    write_file(loop_script, script_content)
    os.chown(loop_script, USER_UID, USER_GID)
    run_cmd(f"chmod +x {loop_script}")
    
    # Loopback Service
    svc_dir = f"{USER_HOME}/.config/systemd/user"
    os.makedirs(svc_dir, exist_ok=True)
    svc_file = f"{svc_dir}/bt-loopback.service"
    
    svc_content = f"""[Unit]
Description=Bluetooth Loopback
After=pulseaudio.service bluetooth.target
Wants=pulseaudio.service
[Service]
ExecStart={loop_script}
Restart=always
RestartSec=5
[Install]
WantedBy=default.target
"""
    write_file(svc_file, svc_content)
    os.chown(svc_file, USER_UID, USER_GID)
    
    run_cmd(f"{xdg_env} systemctl --user daemon-reload", as_user=SUDO_USER)
    run_cmd(f"{xdg_env} systemctl --user enable bt-loopback.service", as_user=SUDO_USER)
    run_cmd(f"{xdg_env} systemctl --user restart bt-loopback.service", as_user=SUDO_USER)

def step_install_service():
    # Detect Sink for Service
    # Note: We do a simple guess here or default, similar to bash
    sink_name = "alsa_output.platform-bcm2835_audio.analog-stereo"
    
    service_exec = f"{PROJECT_DIR}/scripts/start_infotainment.sh"
    run_cmd(f"chmod +x {service_exec}")
    os.chown(service_exec, USER_UID, USER_GID)
    
    pulse_server = f"unix:/run/user/{USER_UID}/pulse/native"
    
    svc_content = f"""[Unit]
Description=RPi Car Infotainment
After=network.target bluetooth.service pulseaudio.service
Wants=bluetooth.service
[Service]
Type=simple
User={SUDO_USER}
Group={SUDO_USER}
WorkingDirectory={PROJECT_DIR}
Environment=PYTHONUNBUFFERED=1
Environment=QT_QPA_PLATFORM=linuxfb:fb=/dev/fb0:size=1024x600
Environment=QT_QPA_GENERIC_PLUGINS=evdevtouch:/dev/input/event0
Environment=SDL_AUDIODRIVER=pulseaudio
Environment=PULSE_SERVER={pulse_server}
Environment=PULSE_SINK={sink_name}
ExecStart={service_exec}
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal
[Install]
WantedBy=multi-user.target
"""
    write_file("/etc/systemd/system/infotainment.service", svc_content)
    run_cmd("systemctl daemon-reload")
    run_cmd("systemctl enable infotainment.service")

# Lista Ordinata degli step
INSTALL_STEPS = [
    ("Update OS & Pkgs", step_update_system),
    ("Boot Config", step_config_boot),
    ("Bluetooth Setup", step_setup_bluetooth),
    ("Python Env", step_python_env),
    ("Audio Config", step_audio_setup),
    ("Install Service", step_install_service),
]

# --- UI LOGIC ---

class InstallThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.progress = 0
        self.current_step = ""
        self.done = False
        self.error = None

    def run(self):
        total = len(INSTALL_STEPS)
        try:
            for i, (name, func) in enumerate(INSTALL_STEPS):
                self.current_step = name
                self.progress = int((i / total) * 100)
                func() # Esegue la funzione
            self.progress = 100
            self.current_step = "Completato!"
            self.done = True
        except Exception as e:
            self.error = str(e)

def draw_text_centered(surface, text, font, color, rect):
    text_surf = font.render(text, True, color)
    text_rect = text_surf.get_rect(center=rect.center)
    surface.blit(text_surf, text_rect)

def main():
    pygame.init()
    
    # Setup Schermo
    info = pygame.display.Info()
    W, H = info.current_w, info.current_h
    screen = pygame.display.set_mode((W, H), pygame.FULLSCREEN)
    pygame.mouse.set_visible(True) # Utile anche col touch per feedback

    # Font
    font_large = pygame.font.SysFont(None, 60)
    font_med = pygame.font.SysFont(None, 40)
    font_small = pygame.font.SysFont(None, 25)

    # Stato
    running = True
    installing = False
    worker = None
    
    # UI Elements
    btn_start = pygame.Rect(W//2 - 150, H//2 - 50, 300, 100)
    btn_exit = pygame.Rect(W - 120, 20, 100, 50)
    
    clock = pygame.time.Clock()

    while running:
        screen.fill(DARK_GRAY)
        
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if not installing:
                    # Start
                    if btn_start.collidepoint(event.pos):
                        installing = True
                        worker = InstallThread()
                        worker.start()
                    # Exit
                    if btn_exit.collidepoint(event.pos):
                        running = False
                elif installing and worker and worker.done:
                    # Reboot (bottone verde)
                    if btn_start.collidepoint(event.pos):
                         subprocess.run(["reboot"])

        # --- DRAWING ---

        # Titolo
        title = font_large.render("RPi Installer Infotainment", True, WHITE)
        screen.blit(title, (50, 50))

        # Box Log/Stato
        if installing:
            status_text = f"Step: {worker.current_step}"
            if worker.error:
                 status_text = f"ERRORE: {worker.error}"
                 col = RED
            else:
                 col = BLUE
            
            # Barra Progresso
            pygame.draw.rect(screen, BLACK, (50, H//2 - 20, W-100, 40))
            fill_w = (W-100) * (worker.progress / 100.0)
            pygame.draw.rect(screen, col, (50, H//2 - 20, fill_w, 40))
            
            # Testo sotto barra
            lbl = font_med.render(f"{worker.progress}% - {status_text}", True, WHITE)
            screen.blit(lbl, (50, H//2 + 30))
            
            # Se finito, trasforma la UI per Reboot
            if worker.done:
                pygame.draw.rect(screen, GREEN, btn_start, border_radius=15)
                draw_text_centered(screen, "RIAVVIA ORA", font_med, WHITE, btn_start)
            elif worker.error:
                pygame.draw.rect(screen, RED, btn_start, border_radius=15)
                draw_text_centered(screen, "ERRORE (Vedi Log)", font_med, WHITE, btn_start)

        else:
            # Stato Iniziale
            pygame.draw.rect(screen, BLUE, btn_start, border_radius=15)
            draw_text_centered(screen, "INSTALLA", font_large, WHITE, btn_start)
            
            info_txt = font_small.render("Assicurati di essere connesso a Internet.", True, LIGHT_GRAY)
            screen.blit(info_txt, (W//2 - 150, H//2 + 70))

        # Bottone Exit
        pygame.draw.rect(screen, RED, btn_exit, border_radius=5)
        draw_text_centered(screen, "ESCI", font_small, WHITE, btn_exit)

        pygame.display.flip()
        clock.tick(10)

    pygame.quit()

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("Devi essere root!")
    else:
        main()