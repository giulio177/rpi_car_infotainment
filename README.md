# RPi Car Infotainment

A car infotainment system designed to run on a Raspberry Pi. This system provides music playback, OBD-II vehicle diagnostics, and RF communication capabilities.

## Project Structure

```
rpi_car_infotainment/
├── assets/             # Icons and other static assets
├── backend/            # Backend functionality
├── deployment/         # Service files, installation scripts, and deployment configs
├── gui/                # GUI components and screens
├── music/              # Music library and related files
├── scripts/            # Shell scripts and utilities
├── tests/              # Test files
├── tools/              # RF communication and other tools
├── config.json         # Configuration file
├── main.py             # Main application entry point
└── requirements.txt    # Python dependencies
```

## Dependencies

### Core Dependencies
- Python 3.11+
- PyQt6 - GUI framework
- obd (0.7.2) - OBD-II communication
- requests (2.32.3) - HTTP requests for music downloads
- pyserial (3.5) - Serial communication

### Optional Dependencies
- pygame - For music player functionality
- rpi-rf - For RF communication tools
- RPi.GPIO - For Raspberry Pi GPIO access
- yt-dlp - For downloading music (not included in requirements.txt)

## Installation on Raspberry Pi OS Lite

### 1. Update and install packages
```bash
sudo apt update
sudo apt full-upgrade -y
```

### 2. Install System Dependencies

```bash
sudo apt install -y \
    git \
    python3-venv \
    python3-pyqt6 \
    qt6-base-dev \
    qt6-tools-dev \
    build-essential \
    alsa-utils \
    libspa-0.2-bluetooth \
    xserver-xorg-core \
    xinit
```

### 3. Clone Repository
```bash
# Go in the home directory
cd /home/pi

# Clone the specific branch 'stable-liteOS'
git clone --branch stable-liteOS https://github.com/giulio177/rpi_car_infotainment.git
```

### 4. Set Up VENV

```bash
cd /home/pi/rpi_car_infotainment
python3 -m venv --system-site-packages venv
source venv/bin/activate
```

### 5. Install dependences

```bash
pip install -r requirements.txt

// Deactivate venv
deactivate
```
```bash
echo "dtoverlay=hifiberry-dac" | sudo tee -a /boot/firmware/config.txt

sudo sed -i 's/^dtparam=audio=on/#dtparam=audio=on/' /boot/firmware/config.txt

sudo sed -i '1 s/$/ logo.nologo quiet loglevel=3/' /boot/firmware/cmdline.txt
```

Build volume controller software for PipeWire
```bash
sudo mkdir -p /etc/wireplumber/main.lua.d
sudo nano /etc/wireplumber/main.lua.d/51-hifiberry-softvol.lua
```
Paste this



### 6. Hardware configuration

```bash
echo "dtoverlay=hifiberry-dac" | sudo tee -a /boot/firmware/config.txt

sudo sed -i 's/^dtparam=audio=on/#dtparam=audio=on/' /boot/firmware/config.txt

sudo sed -i '1 s/$/ logo.nologo quiet loglevel=3/' /boot/firmware/cmdline.txt
```

Build volume controller software for PipeWire
```bash
sudo mkdir -p /etc/wireplumber/main.lua.d
sudo nano /etc/wireplumber/main.lua.d/51-hifiberry-softvol.lua
```

Paste this:
```lua
rule = {
  matches = {
    {
      { "node.name", "matches", "alsa_output.platform-soc*sound.stereo-fallback" },
    },
  },
  apply_properties = {
    ["api.alsa.soft-mixer"] = true,
  },
}
table.insert(alsa_monitor.rules, rule)
```

### 7. Automatic Bluetooth Connection Configuration 

```bash
sudo nano /usr/local/bin/bt-agent-simple.py
```

Paste this:
```phyton
#!/usr/bin/env python3

import dbus
import dbus.service
import dbus.mainloop.glib
from gi.repository import GLib

AGENT_INTERFACE = 'org.bluez.Agent1'
AGENT_PATH = '/test/agent'

bus = None
mainloop = None

class Agent(dbus.service.Object):
    exit_on_release = True

    def set_exit_on_release(self, exit_on_release):
        self.exit_on_release = exit_on_release

    @dbus.service.method(AGENT_INTERFACE, in_signature="", out_signature="")
    def Release(self):
        print("Agent Release")
        if self.exit_on_release:
            if mainloop:
                mainloop.quit()

    @dbus.service.method(AGENT_INTERFACE, in_signature="o", out_signature="")
    def RequestAuthorization(self, device):
        print(f"RequestAuthorization for device {device}")
        # Accetta automaticamente qualsiasi richiesta di autorizzazione
        return

    @dbus.service.method(AGENT_INTERFACE, in_signature="ou", out_signature="")
    def RequestConfirmation(self, device, passkey):
        print(f"RequestConfirmation for device {device} with passkey {passkey}")
        # Accetta automaticamente qualsiasi richiesta di conferma (accoppiamento "Just Works")
        return

    @dbus.service.method(AGENT_INTERFACE, in_signature="os", out_signature="")
    def RequestPinCode(self, device):
        print(f"RequestPinCode for device {device}")
        # Rifiuta esplicitamente le richieste di PIN
        raise dbus.exceptions.DBusException('org.bluez.Error.Rejected', 'Pairing rejected: PIN code not supported')

    @dbus.service.method(AGENT_INTERFACE, in_signature="o", out_signature="s")
    def RequestPasskey(self, device):
        print(f"RequestPasskey for device {device}")
        # Rifiuta esplicitamente le richieste di passkey
        raise dbus.exceptions.DBusException('org.bluez.Error.Rejected', 'Pairing rejected: Passkey not supported')

    @dbus.service.method(AGENT_INTERFACE, in_signature="", out_signature="")
    def Cancel(self):
        print("Pairing Cancelled")

def register_agent():
    global bus
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()
    
    # La capacità "NoInputNoOutput" dice al sistema che non abbiamo né tastiera né display
    capability = "NoInputNoOutput"

    agent = Agent(bus, AGENT_PATH)
    
    try:
        obj = bus.get_object('org.bluez', '/org/bluez')
        manager = dbus.Interface(obj, 'org.bluez.AgentManager1')
        
        manager.RegisterAgent(AGENT_PATH, capability)
        manager.RequestDefaultAgent(AGENT_PATH)
        
        print(f"Python Agent with '{capability}' capability registered successfully.")
    except Exception as e:
        print(f"Failed to register agent: {e}")
        if mainloop:
            mainloop.quit()

if __name__ == '__main__':
    try:
        register_agent()
        
        global mainloop
        mainloop = GLib.MainLoop()
        mainloop.run()
    except KeyboardInterrupt:
        print("\nCaught KeyboardInterrupt. Unregistering agent...")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if bus:
            try:
                obj = bus.get_object('org.bluez', '/org/bluez')
                manager = dbus.Interface(obj, 'org.bluez.AgentManager1')
                manager.UnregisterAgent(AGENT_PATH)
                print("Agent unregistered.")
            except Exception as e:
                print(f"Failed to unregister agent: {e}")
        
        if mainloop and mainloop.is_running():
            mainloop.quit()
        
        print("Script finished.")
```

```bash
sudo chmod +x /usr/local/bin/bt-agent-simple.py
```

Make the systemd service
```bash
sudo nano /etc/systemd/system/bt-agent.service
```
Paste this:
```ini
[Unit]
Description=Python Bluetooth Agent for NoInputNoOutput
Requires=bluetooth.service
After=bluetooth.service

[Service]
ExecStart=/usr/local/bin/bt-agent-simple.py
Restart=always
RestartSec=5

[Install]
WantedBy=bluetooth.target
```

Enable it
```bash
sudo systemctl enable bt-agent.service
```

### 8. Configuration Auto Boot Application

```bash
echo "/home/pi/rpi_car_infotainment/scripts/start_infotainment.sh" > /home/pi/.xinitrc
echo -e 'if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then\n  startx\nfi' > /home/pi/.bash_profile

sudo mkdir -p /etc/systemd/system/getty@.service.d
sudo nano /etc/systemd/system/getty@.service.d/autologin.conf
```
Paste this:
```ini
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin pi --noclear %I $TERM
```

Set correct permits
```bash
sudo chown pi:pi /home/pi/.xinitrc /home/pi/.bash_profile
```

### 9. Reboot and final configuration

```bash
sudo reboot
alsamixer
```
Select the "snd_rpi_hifiberry_dac" DAC
Set volume to 100% (it must show 00)
Click ESC

Save permanently the state of the volume
```bash
sudo alsactl store
```

Run 
```bash
amixer scontrols
```
to see the controller name (es. 'PCM',0).

Make sure that backend/audio_manager.py use MIXER_CONTROL on that name.









## Running the Application

### Using the Start Script (Minimal X Server)
```bash
./scripts/start_infotainment.sh
```
This script will:
1. Start a minimal X server if not already running
2. Activate the virtual environment
3. Launch the application

### Running as a Service (Autostart on Boot)
```bash
# Install the service (run once)
sudo ./deployment/install_service.sh

# Start the service
sudo systemctl start rpi-infotainment

# Stop the service
sudo systemctl stop rpi-infotainment

# Check service status
sudo systemctl status rpi-infotainment
```

### Headless Mode (for testing)
```bash
python scripts/run_headless.py
```

### Testing Dependencies
```bash
python tests/test_dependencies.py
```

### Testing Music Player
```bash
python tests/test_music_player.py
```

### RF Communication Tools
To send RF codes:
```bash
python tools/send_code.py -c 12345 -g 24
```

To receive RF codes:
```bash
python tools/receive_code.py -g 23
```

## Features

### Music Player
- Playback of local music files from the `music/library` folder
- Download functionality with progress indicator
- Album art display
- Lyrics display with synchronization
- Volume control

### OBD-II Integration
- Connect to vehicle's OBD-II port for diagnostics
- Display vehicle data in real-time
- Configure connection parameters in settings

### RF Communication
- Send and receive RF codes using 433MHz transmitters/receivers
- Useful for controlling external devices or garage doors

### AirPlay Mirroring (with RPiPlay)
- Mirror your iPhone/iPad screen to the infotainment system
- Requires RPiPlay to be installed separately
- See the RPiPlay Integration section below for setup instructions

## Troubleshooting

### Music Player Issues
- **No Sound**: Ensure pygame is installed correctly and audio output is configured
- **Download Failures**: Check internet connection and ensure yt-dlp is installed
- **Missing Album Art**: The application will display a default image if album art cannot be found

### Display Issues
- If you're getting errors related to the display or XCB, make sure you're running the application in a graphical environment
- For headless testing, use `scripts/run_headless.py`
- Adjust resolution in `config.json` if the display is too large or small

### Minimal X Server Issues
- If running on Raspberry Pi OS Lite, make sure X server is installed: `sudo apt-get install xorg`
- Check if X server is running: `ps aux | grep Xorg`
- Start X server manually: `X :0 -nocursor &`
- Set the DISPLAY environment variable: `export DISPLAY=:0`
- For touchscreen issues, try: `DISPLAY=:0 xinput --calibrate "device_name"`

### OBD Connection Issues
- Make sure the OBD adapter is properly connected
- Verify the correct port in `config.json` (e.g., "/dev/ttyUSB0")
- Set the correct baudrate (typically 38400 for ELM327 adapters)
- Enable OBD functionality in settings

### RF Communication Issues
- Ensure the RF transmitter/receiver is connected to the correct GPIO pins
- For transmitters, default is GPIO 24
- For receivers, default is GPIO 23
- Make sure pigpio daemon is running: `sudo pigpiod -n`

## RPiPlay Integration (AirPlay Mirroring)

To enable AirPlay mirroring from iOS devices to your infotainment system:

### 1. Install RPiPlay

```bash
# Install dependencies
sudo apt-get update
sudo apt-get install -y cmake libavahi-compat-libdnssd-dev libplist-dev \
  libssl-dev libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev \
  gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad \
  gstreamer1.0-libav

# Clone and build RPiPlay
git clone https://github.com/FD-/RPiPlay.git
cd RPiPlay
mkdir build
cd build
cmake ..
make -j$(nproc)
sudo make install
```

### 2. Create a Script to Start RPiPlay

Create a file named `start_airplay.sh`:

```bash
#!/bin/bash
# Start RPiPlay with the correct display
export DISPLAY=:0
rpiplay -n "Car Display" -b auto
```

Make it executable:
```bash
chmod +x start_airplay.sh
```

### 3. Create a Systemd Service for RPiPlay (Optional)

Create a file named `rpi-airplay.service`:

```
[Unit]
Description=RPiPlay AirPlay Service
After=network.target rpi-infotainment.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/rpi_car_infotainment
ExecStart=/home/pi/rpi_car_infotainment/scripts/start_airplay.sh
Restart=on-failure
RestartSec=5
Environment=DISPLAY=:0

[Install]
WantedBy=multi-user.target
```

Install the service:
```bash
sudo cp rpi-airplay.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable rpi-airplay
sudo systemctl start rpi-airplay
```

## Development

### Running Tests
```bash
# Test dependencies
python tests/test_dependencies.py

# Test music player
python tests/test_music_player.py
```

### Adding New Features
1. Backend functionality should be added to the `backend/` directory
2. GUI components should be added to the `gui/` directory
3. Update `config.json` with any new configuration options
4. Update tests as needed

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
# Versione stabile con DAC e Bluetooth funzionanti
