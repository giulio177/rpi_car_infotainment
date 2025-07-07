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

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/giulio177/rpi_car_infotainment.git
cd rpi_car_infotainment
```

### 2. Install System Dependencies

#### For Raspberry Pi OS with Desktop
```bash
sudo apt-get update
sudo apt-get install python3-pyqt6 python3-pip
```

#### For Raspberry Pi OS Lite (Minimal Installation)
```bash
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip xorg alsa-utils
sudo apt-get install -y python3-pyqt6  # Install PyQt6 from apt
```

### 3. Set Up Python Virtual Environment
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# For music player functionality
pip install pygame

# For RF tools
pip install rpi-rf RPi.GPIO

# For music downloads (optional)
pip install yt-dlp
```

### 4. Set Up Configuration
The application uses a `config.json` file for configuration. If it doesn't exist, it will be created with default values. You can customize it according to your needs:

```json
{
    "theme": "dark",                 # UI theme (dark/light)
    "obd_port": null,                # OBD port (e.g., "/dev/ttyUSB0")
    "obd_baudrate": null,            # OBD baudrate (e.g., 38400)
    "obd_enabled": false,            # Enable OBD functionality
    "radio_type": "none",            # Radio type
    "radio_i2c_address": null,       # I2C address for radio
    "radio_enabled": false,          # Enable radio functionality
    "last_fm_station": 98.5,         # Last used FM station
    "window_resolution": [1024, 600],# Window resolution
    "show_cursor": false,            # Show cursor in UI
    "position_bottom_right": true,   # Position window at bottom-right
    "ui_scale_mode": "auto",         # UI scaling mode
    "developer_mode": false,         # Enable developer features
    "volume": 48                     # Default volume level
}
```

## Running the Application

### Normal Mode (with GUI)
```bash
python main.py
```

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
