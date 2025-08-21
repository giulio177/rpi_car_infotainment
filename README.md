# RPi Car Infotainment (Lite OS · Pi 4)

A lightweight, touch-friendly car infotainment system for Raspberry Pi.

This branch targets **Raspberry Pi 4** running **Raspberry Pi OS Lite (Bookworm)**, using:
 - **Direct framebuffer** rendering (no X/Wayland) via Qt `linuxfb` + `evdev`
 - Bluetooth auto-pairing (no code) with **A2DP** audio input from phone
 - **PulseAudio (user instance)** with audio out on the **3.5 mm jack**
 - **Fixed display mode 1024×600** on both HDMI ports

> If you’re on Raspberry Pi 5 or a Desktop (with X/Wayland), refer to the Pi 5 branch/instructions.
> This document is optimized for **Pi 4 + Lite**.

## Project Structure

```bash
rpi_car_infotainment/
├── assets/             # Icons and other static assets
├── backend/            # Backend functionality
├── deployment/         # Service files, installation scripts, and deployment configs
├── gui/                # GUI components and screens
├── music/              # Music library and related files
├─ scripts/
│  ├─ start_infotainment.sh          # Launches the app (Qt linuxfb + evdev, activates venv)
│  └─ (other helpers)
├── tests/              # Test files
├── tools/              # RF communication and other tools
├── config.json         # Configuration file
├── main.py             # Main application entry point
└── requirements.txt    # Python dependencies
```

System files created during setup (not in repo):
```
/etc/systemd/system/infotainment.service      # Autostarts the app on boot (no X)
/etc/systemd/system/bt-agent.service          # Auto-pairing Bluetooth agent (NoInputNoOutput)
/usr/local/bin/bt-agent-rpi.py                # Agent script
/etc/asound.conf                              # Force ALSA → PulseAudio
/boot/firmware/cmdline.txt                    # Forces 1024×600 on HDMI-A-1,A-2 (Pi 4 · Bookworm)
```

## Hardware & OS
 - **Raspberry Pi 4** (2GB/4GB/8GB)
 - **Raspberry Pi OS Lite (Bookworm)** 64-bit recommended
 - 7–10″ HDMI “car” display (physical **1024×600** panel, many controllers advertise 1080p)
 - USB/serial touchscreen controller (evdev)
 - Audio output via **3.5 mm jack**

## Dependencies

### System packages
```bash
sudo apt update
sudo apt full-upgrade -y
sudo apt install -y \
  git python3-venv python3-pip \
  python3-pyqt6 qt6-base-dev \
  python3-pygame ffmpeg \
  pulseaudio pulseaudio-module-bluetooth alsa-utils \
  bluez bluez-tools \
  python3-dbus python3-gi gir1.2-glib-2.0 \
  dbus-user-session
```
> - `python3-dbus`, `python3-gi`, `gir1.2-glib-2.0` are required by the **Bluetooth agent**.
> - We use **PulseAudio (user instance)**, not the system-wide daemon.
> - We don’t install Xorg/xinit here because the app runs directly **on the framebuffer**.

## Python packages
The project ships a `requirements.txt`. You’ll install it into a virtualenv during setup.

# Installation (Pi 4 · Lite · Bookworm)

## 1. Clone & virtualenv
```bash
cd /home/pi
git clone --branch stable-liteOS-pi4B https://github.com/giulio177/rpi_car_infotainment.git
cd /home/pi/rpi_car_infotainment

python3 -m venv --system-site-packages venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
```


## 2. Force HDMI 1024×600 on both ports (KMS / Bookworm)

Edit **/boot/firmware/cmdline.txt** (single line!) and append:
```bash
video=HDMI-A-1:1024x600@60D video=HDMI-A-2:1024x600@60D logo.nologo quiet loglevel=3 vt.global_cursor_default=0
```
 - **HDMI-A-1** is the port near the **audio jack** on Pi 4.
 - **HDMI-A-2** is the one near **USB-C**.

> Do **not** add line breaks. Keep everything on one line.


## 3. Enable analog audio
```bash
echo 'dtparam=audio=on' | sudo tee -a /boot/config.txt
```
Reboot to apply overlays and ensure groups/sound come up:
```bash
sudo reboot
```

## 4. PulseAudio (user instance) + ALSA → Pulse
Disable any system-wide PulseAudio if present:
```bash
sudo systemctl disable --now pulseaudio || true
```
Enable per-user services even without a GUI login:
```bash
sudo loginctl enable-linger pi
sudo systemctl start user@1000.service
```
Start/enable PulseAudio for the `pi` user:
```bash
sudo -u pi XDG_RUNTIME_DIR=/run/user/1000 systemctl --user enable --now pulseaudio
```
Make ALSA default to PulseAudio (so pygame/SDL and other ALSA apps go through Pulse):
```bash
sudo tee /etc/asound.conf >/dev/null <<'EOF'
pcm.!default pulse
ctl.!default pulse
EOF
```
Ensure PulseAudio loads Bluetooth modules (user instance reads **/etc/pulse/default.pa**):
```bash
grep -q bluetooth-discover /etc/pulse/default.pa || sudo tee -a /etc/pulse/default.pa >/dev/null <<'EOF'

### Bluetooth A2DP (user instance)
load-module module-bluetooth-policy
load-module module-bluetooth-discover
EOF

sudo -u pi systemctl --user restart pulseaudio
```

## 5. Pick your analog sink (jack) and remember its name
List sinks and test:
```bash
pactl list sinks short
paplay /usr/share/sounds/alsa/Front_Center.wav
```
On our test the best sink was:
```bash
alsa_output.platform-fe00b840.mailbox.stereo-fallback.3
```
Yours can differ; use whatever plays on the jack.


## 6. Bluetooth “no-code” agent (NoInputNoOutput)
Create the agent:
```bash
sudo tee /usr/local/bin/bt-agent-rpi.py >/dev/null <<'PY'
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
            props = dbus.Interface(self.bus.get_object("org.bluez", path), "org.freedesktop.DBus.Properties")
            props.Set("org.bluez.Device1", "Trusted", True)
        except Exception:
            pass

    @dbus.service.method(AGENT_INTERFACE, in_signature="o", out_signature="s")
    def RequestPinCode(self, device): self.set_trusted(device); return "0000"

    @dbus.service.method(AGENT_INTERFACE, in_signature="ou", out_signature="")
    def RequestConfirmation(self, device, passkey): self.set_trusted(device)

    @dbus.service.method(AGENT_INTERFACE, in_signature="o", out_signature="")
    def RequestAuthorization(self, device): self.set_trusted(device)

    @dbus.service.method(AGENT_INTERFACE, in_signature="", out_signature="")
    def Release(self): pass

    @dbus.service.method(AGENT_INTERFACE, in_signature="", out_signature="")
    def Cancel(self): pass

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
sudo chmod +x /usr/local/bin/bt-agent-rpi.py
```

Systemd unit for the agent:
```bash
sudo tee /etc/systemd/system/bt-agent.service >/dev/null <<'EOF'
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

sudo systemctl enable --now bt-agent.service
```

Set controller IO capability to NoInputNoOutput (prevents “pair code” screens):
```bash
sudo btmgmt
# inside prompt:
[mgmt] io-cap 3
[mgmt] bondable on
[mgmt] connectable on
[mgmt] pairable on
[mgmt] bredr on
[mgmt] exit

# ensure BR/EDR mode
sudo sed -i '/^\[General\]/,$!b;/^\[General\]/a ControllerMode = bredr\nAutoEnable = true' /etc/bluetooth/main.conf
sudo systemctl restart bluetooth
```

Now pair from the phone (first time only).
You should not see numeric-comparison codes; the device will be trusted automatically.


## 7. Autostart the app (framebuffer, no X)
Create the service:
```bash
sudo tee /etc/systemd/system/infotainment.service >/dev/null <<'EOF'
[Unit]
Description=RPi Car Infotainment (framebuffer, no X)
After=network.target bluetooth.service
Wants=bluetooth.service

[Service]
Type=simple
User=pi
Group=pi
WorkingDirectory=/home/pi
# Access /dev/fb0 and /dev/input/event*
SupplementaryGroups=video,input
# Don't inherit a DISPLAY
Environment=DISPLAY=
# App audio: force SDL/pygame -> Pulse, and pick the analog sink found above
Environment=SDL_AUDIODRIVER=pulseaudio
Environment=PULSE_SERVER=unix:/run/user/1000/pulse/native
Environment=PULSE_SINK=alsa_output.platform-fe00b840.mailbox.stereo-fallback.3
ExecStart=/home/pi/rpi_car_infotainment/scripts/start_infotainment.sh
Restart=on-failure
RestartSec=2
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable infotainment.service
sudo systemctl start infotainment.service
sudo systemctl status infotainment.service -n 20
```

> Your `scripts/start_infotainment.sh` should already set `QT_QPA_PLATFORM=linuxfb:fb=/dev/fb0;evdev-touch-screen=/dev/input/eventX` and run `main.py` in foreground (no `startx/xinit` inside).









# Bluetooth → Jack: optional auto-loopback

If you want phone audio (A2DP source) to be automatically routed to the analog jack on connect:

```bash
mkdir -p /home/pi/.local/bin /home/pi/.config/systemd/user
cat >/home/pi/.local/bin/bt-loopback.sh <<'SH'
#!/bin/bash
set -euo pipefail
SINK="alsa_output.platform-fe00b840.mailbox.stereo-fallback.3"
try_once() {
  src=$(pactl list sources short | awk '/bluez_source/ {print $2; exit}')
  [ -n "${src:-}" ] && pactl load-module module-loopback source="$src" sink="$SINK" latency_msec=60 >/dev/null 2>&1 || true
}
try_once
pactl subscribe | while read -r line; do
  echo "$line" | grep -qE "source|card" && try_once
done
SH
chmod +x /home/pi/.local/bin/bt-loopback.sh

cat >/home/pi/.config/systemd/user/bt-loopback.service <<'EOF'
[Unit]
Description=Bluetooth A2DP loopback to analog jack
After=pulseaudio.service bluetooth.target
Wants=pulseaudio.service

[Service]
ExecStart=/home/pi/.local/bin/bt-loopback.sh
Restart=always
RestartSec=2

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now bt-loopback.service
```


# Run / Logs / Maintenance
 - Start/stop the app:
```bash
sudo systemctl start infotainment.service
sudo systemctl stop  infotainment.service
sudo journalctl -u infotainment.service -n 50
```
 - Bluetooth agent:
```bash
sudo systemctl status bt-agent.service
sudo journalctl -u bt-agent.service -n 50
```
 - PulseAudio (user):
```bash
systemctl --user status pulseaudio -n 20
pactl list sinks short
pactl list sources short
pactl list sink-inputs short
```

#


## Troubleshooting
 - Black screen / wrong resolution
   Ensure /boot/firmware/cmdline.txt has video=HDMI-A-1:1024x600@60D video=HDMI-A-2:1024x600@60D on the single line. Try the other HDMI port if needed.
 - Service bounces / exits immediately
   Make sure start_infotainment.sh does not start X or exit early; it must exec python3 main.py and stay in foreground.
 - Phone pairs but no speaker appears
   You must use PulseAudio user instance and have these in /etc/pulse/default.pa:
   ```bash
   python scripts/run_headless.py
   ```
   Then restart PA: systemctl --user restart pulseaudio.
 - Phone asks for a code
   Confirm the agent is running and controller IO capability is NoInputNoOutput:
   ```bash
   sudo systemctl status bt-agent.service
   sudo btmgmt info   # should show IO cap: NoInputNoOutput
   ```
 - App plays but no sound
   Ensure ALSA → Pulse (/etc/asound.conf) and that infotainment.service has:
   ```bash
   Environment=SDL_AUDIODRIVER=pulseaudio
   Environment=PULSE_SERVER=unix:/run/user/1000/pulse/native
   Environment=PULSE_SINK=<your-analog-sink>
   ```
   While pressing Play, check an extra sink-input appears:
   ```bash
   pactl list sink-inputs short
   ```


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
