# RPi Car Infotainment

A car infotainment system designed to run on a Raspberry Pi. This system provides music playback, OBD-II vehicle diagnostics, and RF communication capabilities.

## Project Structure

```
rpi_car_infotainment/
├── assets/             # Icons and other static assets
├── backend/            # Backend functionality
├── gui/                # GUI components and screens
├── music/              # Music library and related files
├── rf_tools/           # RF communication tools
├── scripts/            # Utility scripts
├── tests/              # Test files
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
```bash
sudo apt-get update
sudo apt-get install python3-pyqt6 python3-pip
```

### 3. Install Python Dependencies
```bash
# Install all required dependencies
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
python rf_tools/send_code.py -c 12345 -g 24
```

To receive RF codes:
```bash
python rf_tools/receive_code.py -g 23
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

## Troubleshooting

### Music Player Issues
- **No Sound**: Ensure pygame is installed correctly and audio output is configured
- **Download Failures**: Check internet connection and ensure yt-dlp is installed
- **Missing Album Art**: The application will display a default image if album art cannot be found

### Display Issues
- If you're getting errors related to the display or XCB, make sure you're running the application in a graphical environment
- For headless testing, use `scripts/run_headless.py`
- Adjust resolution in `config.json` if the display is too large or small

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
